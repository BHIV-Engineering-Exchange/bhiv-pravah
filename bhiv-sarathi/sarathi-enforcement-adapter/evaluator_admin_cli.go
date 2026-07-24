package main

// evaluator_admin_cli.go — v15.0 Sovereign Identity Closure.
//
// Command-line helpers for operating the inbound-auth machinery WITHOUT
// shelling out to python or openssl. Every subcommand here is a thin wrapper
// around the same Go primitives the live middleware uses — there is no
// divergence between CLI and runtime behaviour.
//
// SUBCOMMANDS:
//
//   --genkey --out-dir=<dir>
//       Generates a fresh Ed25519 keypair. Writes:
//         <dir>/issuer-priv.key   (64-byte hex, MODE 0600)
//         <dir>/issuer-pub.hex    (32-byte hex, MODE 0644)
//         <dir>/issuer-id.txt     (auto-generated UUID v4, MODE 0644)
//
//   --genapikey [--length=32]
//       Prints a cryptographically-random hex API key to stdout. Use this to
//       create a key for SARATHI_CALLER_KEY_TEST_HARNESS (or any other caller
//       slot) and share with the tester over a private channel.
//
//   --register-evaluator --issuer-id=<id> --public-key=<hex>
//       [--status=active|suspended|revoked]
//       [--metadata='{"name":"..","org":".."}']
//       [--snapshot=./live/trust_snapshot.json]
//       Creates or updates a row in the trust snapshot JSON file that
//       BootstrapTrustConsumer already reads (SARATHI_TRUST_SNAPSHOT). Safe
//       to run while the service is up; the next restart picks up the new
//       state. No locking is needed because the snapshot file is a single
//       atomic rename target.
//
//   --suspend-evaluator --issuer-id=<id> [--snapshot=...]
//   --revoke-evaluator  --issuer-id=<id> [--snapshot=...]
//       Flip the status field in place.
//
//   --list-evaluators [--snapshot=...]
//       Pretty-print the snapshot.
//
//   --sign-and-post --priv-key=<path> --issuer-id=<id>
//       --endpoint=<url> --api-key=<key> --decision-file=<path>
//       [--force-timestamp=<offset-seconds>] [--reuse-nonce=<nonce>]
//       [--omit-signature]
//       Reviewer-side helper that builds the 5 X-Sarathi-* headers, POSTs,
//       and prints HTTP status + response body. Reproduces what the middleware
//       expects without leaking private keys into a shell history.
//
//   --report-query <file.jsonl> <field-path>
//       Streams field values from a JSONL file (e.g., .reason, .issuer_id)
//       so VC-script readers never need python or jq.
//
// All snapshot mutations append a row to proof_logs/registry_audit.jsonl.

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/google/uuid"
)

// ============================================================================
// DISPATCH
// ============================================================================

// RunEvaluatorAdminCLI inspects os.Args and dispatches any v15.0 admin
// subcommand. Returns (handled, exitCode). When handled=false, main.go
// continues with its legacy flag handling.
func RunEvaluatorAdminCLI(args []string) (bool, int) {
	if len(args) < 2 {
		return false, 0
	}
	switch args[1] {
	case "--genkey":
		return true, runGenKey(args[2:])
	case "--genapikey":
		return true, runGenAPIKey(args[2:])
	case "--register-evaluator":
		return true, runRegisterEvaluator(args[2:])
	case "--suspend-evaluator":
		return true, runSetEvaluatorStatus(args[2:], "SUSPENDED")
	case "--revoke-evaluator":
		return true, runSetEvaluatorStatus(args[2:], "REVOKED")
	case "--reactivate-evaluator":
		return true, runSetEvaluatorStatus(args[2:], "ACTIVE")
	case "--list-evaluators":
		return true, runListEvaluators(args[2:])
	case "--sign-and-post":
		return true, runSignAndPost(args[2:])
	case "--report-query":
		return true, runReportQuery(args[2:])
	case "--register-tantra-evaluator":
		// v15.7: register a TANTRA-shaped evaluator entry. Caller supplies
		// the PUBLIC key (private key never travels through Sarathi).
		return true, runRegisterTantraEvaluator(args[2:])
	case "--provider-keygen":
		// v15.7: generate a fresh keypair under the active CryptoProvider.
		return true, runProviderKeygen(args[2:])
	case "--register-peer-key":
		// v15.9: register a propagation peer's PINNED public key (bucket /
		// core / insightflow). Closes the prior TOFU weakness in VerifyReceipt.
		return true, runRegisterPeerKey(args[2:])
	}
	return false, 0
}

// ============================================================================
// FLAG PARSING (stdlib-only; no external deps)
// ============================================================================

type cliFlags map[string]string

// parseCLIFlags parses --key=value and --flag (bare) tokens. Positional args
// are captured in order under the special key "".
func parseCLIFlags(args []string) (cliFlags, []string) {
	out := cliFlags{}
	var positional []string
	for _, a := range args {
		if !strings.HasPrefix(a, "--") {
			positional = append(positional, a)
			continue
		}
		name := strings.TrimPrefix(a, "--")
		if eq := strings.Index(name, "="); eq >= 0 {
			out[name[:eq]] = name[eq+1:]
		} else {
			out[name] = "true"
		}
	}
	return out, positional
}

// ============================================================================
// SNAPSHOT PERSISTENCE
// ============================================================================

const defaultSnapshotPath = "./live/trust_snapshot.json"
const registryAuditLog = "proof_logs/registry_audit.jsonl"

func resolveSnapshotPath(f cliFlags) string {
	if p := f["snapshot"]; p != "" {
		return p
	}
	if p := os.Getenv("SARATHI_TRUST_SNAPSHOT"); p != "" {
		return p
	}
	return defaultSnapshotPath
}

func loadOrInitSnapshot(path string) (*TrustSnapshotFile, error) {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return &TrustSnapshotFile{Version: "v15.0", Evaluators: nil}, nil
	}
	return LoadTrustSnapshot(path)
}

func saveSnapshotAtomic(path string, snap *TrustSnapshotFile) error {
	if dir := filepath.Dir(path); dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return fmt.Errorf("mkdir: %w", err)
		}
	}
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal: %w", err)
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return fmt.Errorf("write tmp: %w", err)
	}
	return os.Rename(tmp, path)
}

func appendRegistryAudit(op string, fields map[string]string) {
	if dir := filepath.Dir(registryAuditLog); dir != "" && dir != "." {
		_ = os.MkdirAll(dir, 0o755)
	}
	f, err := os.OpenFile(registryAuditLog, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer f.Close()
	row := map[string]interface{}{
		"ts": time.Now().UTC().Format(time.RFC3339Nano),
		"op": op,
	}
	for k, v := range fields {
		row[k] = v
	}
	line, err := json.Marshal(row)
	if err != nil {
		return
	}
	line = append(line, '\n')
	_, _ = f.Write(line)
	_ = f.Sync()
}

// ============================================================================
// --genkey
// ============================================================================

func runGenKey(args []string) int {
	flags, _ := parseCLIFlags(args)
	outDir := flags["out-dir"]
	if outDir == "" {
		fmt.Fprintln(os.Stderr, "ERROR: --out-dir is required")
		return 2
	}
	if err := os.MkdirAll(outDir, 0o700); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: mkdir: %v\n", err)
		return 1
	}
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: keygen: %v\n", err)
		return 1
	}
	issuerID := uuid.New().String()
	privPath := filepath.Join(outDir, "issuer-priv.key")
	pubPath := filepath.Join(outDir, "issuer-pub.hex")
	idPath := filepath.Join(outDir, "issuer-id.txt")

	if err := os.WriteFile(privPath, []byte(hex.EncodeToString(priv)), 0o600); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: write priv: %v\n", err)
		return 1
	}
	if err := os.WriteFile(pubPath, []byte(hex.EncodeToString(pub)), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: write pub: %v\n", err)
		return 1
	}
	if err := os.WriteFile(idPath, []byte(issuerID+"\n"), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: write id: %v\n", err)
		return 1
	}
	fmt.Printf("Generated Ed25519 keypair:\n")
	fmt.Printf("  issuer_id:  %s\n", issuerID)
	fmt.Printf("  private:    %s  (KEEP SECRET, chmod 0600)\n", privPath)
	fmt.Printf("  public:     %s  (share with Sarathi operator)\n", pubPath)
	fmt.Printf("  id:         %s  (share with Sarathi operator)\n", idPath)
	fmt.Printf("\npublic_key_hex=%s\n", hex.EncodeToString(pub))
	return 0
}

// ============================================================================
// --genapikey
// ============================================================================

func runGenAPIKey(args []string) int {
	flags, _ := parseCLIFlags(args)
	length := 32
	if raw := flags["length"]; raw != "" {
		var v int
		if _, err := fmt.Sscanf(raw, "%d", &v); err == nil && v >= 16 && v <= 128 {
			length = v
		}
	}
	buf := make([]byte, length)
	if _, err := rand.Read(buf); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: rand: %v\n", err)
		return 1
	}
	fmt.Println(hex.EncodeToString(buf))
	return 0
}

// ============================================================================
// --register-evaluator
// ============================================================================

func runRegisterEvaluator(args []string) int {
	flags, _ := parseCLIFlags(args)
	issuerID := flags["issuer-id"]
	pubHex := flags["public-key"]
	if issuerID == "" || pubHex == "" {
		fmt.Fprintln(os.Stderr, "ERROR: --issuer-id and --public-key are required")
		return 2
	}
	pubBytes, err := hex.DecodeString(pubHex)
	if err != nil || len(pubBytes) != ed25519.PublicKeySize {
		fmt.Fprintf(os.Stderr, "ERROR: public key must be %d hex bytes\n", ed25519.PublicKeySize)
		return 2
	}

	status := strings.ToUpper(flags["status"])
	if status == "" {
		status = "ACTIVE"
	}
	if status != "ACTIVE" && status != "SUSPENDED" && status != "REVOKED" {
		fmt.Fprintln(os.Stderr, "ERROR: --status must be active|suspended|revoked")
		return 2
	}

	name := ""
	if md := flags["metadata"]; md != "" {
		var m map[string]string
		if err := json.Unmarshal([]byte(md), &m); err == nil {
			if n, ok := m["name"]; ok {
				name = n
			}
		}
	}

	path := resolveSnapshotPath(flags)
	snap, err := loadOrInitSnapshot(path)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: load snapshot: %v\n", err)
		return 1
	}

	found := false
	for i, e := range snap.Evaluators {
		if e.EvaluatorID == issuerID {
			snap.Evaluators[i] = EvaluatorTrustSnapshot{
				EvaluatorID: issuerID, Name: name, Status: status, PublicKeyHex: pubHex,
			}
			found = true
			break
		}
	}
	if !found {
		snap.Evaluators = append(snap.Evaluators, EvaluatorTrustSnapshot{
			EvaluatorID: issuerID, Name: name, Status: status, PublicKeyHex: pubHex,
		})
	}
	if snap.Version == "" {
		snap.Version = "v15.0"
	}
	if err := saveSnapshotAtomic(path, snap); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: save snapshot: %v\n", err)
		return 1
	}

	appendRegistryAudit("REGISTER_EVALUATOR", map[string]string{
		"issuer_id":  issuerID,
		"status":     status,
		"pub_prefix": pubHex[:16],
		"snapshot":   path,
	})

	action := "ADDED"
	if found {
		action = "UPDATED"
	}
	fmt.Printf("%s evaluator '%s' (status=%s) in %s\n", action, issuerID, status, path)
	return 0
}

// ============================================================================
// --suspend / --revoke / --reactivate
// ============================================================================

func runSetEvaluatorStatus(args []string, newStatus string) int {
	flags, _ := parseCLIFlags(args)
	issuerID := flags["issuer-id"]
	if issuerID == "" {
		fmt.Fprintln(os.Stderr, "ERROR: --issuer-id is required")
		return 2
	}
	path := resolveSnapshotPath(flags)
	snap, err := loadOrInitSnapshot(path)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: load snapshot: %v\n", err)
		return 1
	}
	updated := false
	for i, e := range snap.Evaluators {
		if e.EvaluatorID == issuerID {
			snap.Evaluators[i].Status = newStatus
			updated = true
			break
		}
	}
	if !updated {
		fmt.Fprintf(os.Stderr, "ERROR: issuer_id '%s' not found in %s\n", issuerID, path)
		return 1
	}
	if err := saveSnapshotAtomic(path, snap); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: save: %v\n", err)
		return 1
	}
	appendRegistryAudit("SET_STATUS", map[string]string{
		"issuer_id": issuerID,
		"status":    newStatus,
		"snapshot":  path,
	})
	fmt.Printf("SET %s -> %s in %s\n", issuerID, newStatus, path)
	return 0
}

// ============================================================================
// --list-evaluators
// ============================================================================

func runListEvaluators(args []string) int {
	flags, _ := parseCLIFlags(args)
	path := resolveSnapshotPath(flags)
	snap, err := loadOrInitSnapshot(path)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: load: %v\n", err)
		return 1
	}
	fmt.Printf("Snapshot: %s  (version=%s, count=%d)\n", path, snap.Version, len(snap.Evaluators))
	for _, e := range snap.Evaluators {
		prefix := e.PublicKeyHex
		if len(prefix) > 16 {
			prefix = prefix[:16] + "..."
		}
		fmt.Printf("  - %-40s %-10s  %s\n", e.EvaluatorID, e.Status, prefix)
	}
	return 0
}

// ============================================================================
// --sign-and-post
// ============================================================================

func runSignAndPost(args []string) int {
	flags, _ := parseCLIFlags(args)
	privPath := flags["priv-key"]
	issuerID := flags["issuer-id"]
	endpoint := flags["endpoint"]
	apiKey := flags["api-key"]
	decFile := flags["decision-file"]
	if privPath == "" || issuerID == "" || endpoint == "" || apiKey == "" || decFile == "" {
		fmt.Fprintln(os.Stderr,
			"ERROR: --priv-key, --issuer-id, --endpoint, --api-key, --decision-file are required")
		return 2
	}
	privHex, err := os.ReadFile(privPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: read priv: %v\n", err)
		return 1
	}
	priv, err := hex.DecodeString(strings.TrimSpace(string(privHex)))
	if err != nil || len(priv) != ed25519.PrivateKeySize {
		fmt.Fprintf(os.Stderr, "ERROR: priv key must be %d hex bytes\n", ed25519.PrivateKeySize)
		return 1
	}
	body, err := os.ReadFile(decFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: read decision: %v\n", err)
		return 1
	}

	// Nonce: random or forced for replay tests.
	nonce := flags["reuse-nonce"]
	if nonce == "" {
		var b [16]byte
		_, _ = rand.Read(b[:])
		nonce = hex.EncodeToString(b[:])
	}

	// Timestamp: now, or shifted by --force-timestamp seconds.
	now := time.Now().UTC()
	if raw := flags["force-timestamp"]; raw != "" {
		var offset int64
		if _, err := fmt.Sscanf(raw, "%d", &offset); err == nil {
			now = now.Add(time.Duration(offset) * time.Second)
		}
	}
	ts := now.Format(time.RFC3339)

	canonical, cerr := CanonicalMarshalBytes(body)
	if cerr != nil {
		fmt.Fprintf(os.Stderr, "ERROR: canonicalise: %v\n", cerr)
		return 1
	}
	payload := BuildInboundSigningPayload(canonical, nonce, ts, issuerID)
	sigB64 := base64.StdEncoding.EncodeToString(ed25519.Sign(ed25519.PrivateKey(priv), payload))

	req, err := http.NewRequest(http.MethodPost, endpoint, bytes.NewReader(body))
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: build request: %v\n", err)
		return 1
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", apiKey)
	req.Header.Set(HeaderSarathiIssuerID, issuerID)
	req.Header.Set(HeaderSarathiRequestNonce, nonce)
	req.Header.Set(HeaderSarathiTimestamp, ts)
	if flags["omit-signature"] != "true" {
		req.Header.Set(HeaderSarathiBodySignature, sigB64)
	}
	req.Header.Set(HeaderSarathiSigAlgorithm, "ed25519")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: POST: %v\n", err)
		return 1
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)

	fmt.Printf("HTTP %d\n", resp.StatusCode)
	fmt.Printf("nonce=%s  ts=%s  issuer=%s\n", nonce, ts, issuerID)
	fmt.Println(string(respBody))
	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		return 0
	}
	return 3
}

// ============================================================================
// --report-query
// ============================================================================

func runReportQuery(args []string) int {
	_, pos := parseCLIFlags(args)
	if len(pos) < 2 {
		fmt.Fprintln(os.Stderr, "ERROR: usage: --report-query <file.jsonl> <field>")
		return 2
	}
	path := pos[0]
	field := strings.TrimPrefix(pos[1], ".")
	f, err := os.Open(path)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: open: %v\n", err)
		return 1
	}
	defer f.Close()
	dec := json.NewDecoder(f)
	for {
		var row map[string]interface{}
		if err := dec.Decode(&row); err != nil {
			if err == io.EOF {
				break
			}
			fmt.Fprintf(os.Stderr, "WARN: decode: %v\n", err)
			continue
		}
		if v, ok := row[field]; ok {
			fmt.Println(stringifyValue(v))
		}
	}
	return 0
}

func stringifyValue(v interface{}) string {
	switch t := v.(type) {
	case string:
		return t
	case float64:
		return fmt.Sprintf("%v", t)
	case bool:
		return fmt.Sprintf("%v", t)
	default:
		b, _ := json.Marshal(v)
		return string(b)
	}
}
