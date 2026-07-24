package main

// cmd_tantra_register.go — Admin CLI for TANTRA evaluator registration.
//
// REPLACES the deleted cmd_sovereign_keygen.go --bootstrap-sovereign-core flow.
//
// Key difference: this command NEVER mints a private key on Sarathi's behalf.
// The caller (operator) supplies the evaluator's PUBLIC key only — the
// private key always stays with the evaluator that owns it (Sovereign Core
// for the upstream PDP, Sarathi for its own enforcement key, etc.).
//
// Usage:
//
//   sarathi-enforcement-adapter --register-tantra-evaluator \
//       --evaluator-id=bhiv.sovereign.decision.prod.v1 \
//       --schema-version=tantra.decision.v1 \
//       --algorithm=Ed25519 \
//       --key-id=bhiv.sovereign.decision.prod.v1#ed25519-2026-05 \
//       --public-key=<hex-or-base64url> \
//       --api-key-fingerprint=<sha256-hex>             # optional
//       --snapshot=./live/trust_snapshot.json          # optional override
//       --name="Sovereign BHIV Core"                   # optional
//
// What it does:
//   1. Validates --evaluator-id parses as a TANTRA id.
//   2. Validates --key-id is "<evaluator_id>#<rotation_tag>".
//   3. Validates --public-key parses under the indicated algorithm.
//   4. Loads existing snapshot (or creates a fresh one).
//   5. Inserts / updates the tantra_evaluators row.
//   6. Atomically writes the snapshot back to disk.
//   7. Appends a row to proof_logs/tantra_registry_audit.jsonl.
//
// Idempotent: running twice with the same inputs is a no-op except for the
// audit log row.
//
// TAG: tantra-v15.7

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const tantraRegistryAuditLog = "proof_logs/tantra_registry_audit.jsonl"

func runRegisterTantraEvaluator(args []string) int {
	flags, _ := parseCLIFlags(args)

	evID := strings.TrimSpace(flags["evaluator-id"])
	schema := strings.TrimSpace(flags["schema-version"])
	if schema == "" {
		schema = TantraSchemaV1
	}
	alg := strings.TrimSpace(flags["algorithm"])
	if alg == "" {
		alg = string(CryptoAlgEd25519)
	}
	keyID := strings.TrimSpace(flags["key-id"])
	pubKey := strings.TrimSpace(flags["public-key"])
	apiKeyFP := strings.TrimSpace(flags["api-key-fingerprint"])
	name := strings.TrimSpace(flags["name"])
	snapshotPath := resolveSnapshotPath(flags)
	notes := strings.TrimSpace(flags["notes"])

	if evID == "" || keyID == "" || pubKey == "" {
		fmt.Fprintln(os.Stderr, "register-tantra-evaluator: --evaluator-id, --key-id, --public-key are required")
		return 2
	}

	// Validate the evaluator id format.
	if _, err := ParseTantraEvaluatorID(evID); err != nil {
		fmt.Fprintf(os.Stderr, "register-tantra-evaluator: %v\n", err)
		return 2
	}
	// Validate the key_id wraps the evaluator id.
	parsedID, _, err := SplitKeyID(keyID)
	if err != nil {
		fmt.Fprintf(os.Stderr, "register-tantra-evaluator: %v\n", err)
		return 2
	}
	if parsedID.Raw != evID {
		fmt.Fprintf(os.Stderr,
			"register-tantra-evaluator: key_id prefix %q does not match --evaluator-id %q\n",
			parsedID.Raw, evID)
		return 2
	}
	// Validate algorithm.
	switch CryptoAlgorithmID(alg) {
	case CryptoAlgEd25519, CryptoAlgCompositeMLDSA65Ed25519:
	default:
		fmt.Fprintf(os.Stderr, "register-tantra-evaluator: unknown algorithm %q\n", alg)
		return 2
	}
	// Validate public key parses under the indicated algorithm.
	var validator CryptoProvider
	switch CryptoAlgorithmID(alg) {
	case CryptoAlgEd25519:
		validator = NewEd25519Provider()
	case CryptoAlgCompositeMLDSA65Ed25519:
		validator = NewHybridProvider()
	}
	if _, perr := validator.ParsePublicKey(pubKey); perr != nil {
		fmt.Fprintf(os.Stderr, "register-tantra-evaluator: public_key parse: %v\n", perr)
		return 2
	}

	// Load (or seed) the snapshot.
	var snap TantraTrustSnapshotFile
	if data, rerr := os.ReadFile(snapshotPath); rerr == nil {
		_ = json.Unmarshal(data, &snap)
	}
	if snap.Version == "" {
		snap.Version = "v15.7"
	}

	row := TantraEvaluatorEntry{
		EvaluatorID:       evID,
		Name:              name,
		Status:            "ACTIVE",
		SchemaVersion:     schema,
		Algorithm:         alg,
		KeyID:             keyID,
		PublicKey:         pubKey,
		APIKeyFingerprint: apiKeyFP,
		RegisteredAt:      time.Now().UTC().Format(time.RFC3339Nano),
		Notes:             notes,
	}

	// Upsert.
	replaced := false
	for i := range snap.TantraEvaluators {
		if snap.TantraEvaluators[i].EvaluatorID == evID {
			snap.TantraEvaluators[i] = row
			replaced = true
			break
		}
	}
	if !replaced {
		snap.TantraEvaluators = append(snap.TantraEvaluators, row)
	}

	if err := writeTantraSnapshotAtomically(snapshotPath, &snap); err != nil {
		fmt.Fprintf(os.Stderr, "register-tantra-evaluator: write snapshot: %v\n", err)
		return 1
	}

	appendTantraRegistryAudit(map[string]interface{}{
		"ts":             time.Now().UTC().Format(time.RFC3339Nano),
		"action":         "register_tantra_evaluator",
		"evaluator_id":   evID,
		"schema_version": schema,
		"algorithm":      alg,
		"key_id":         keyID,
		"replaced":       replaced,
		"snapshot_path":  snapshotPath,
	})

	verb := "registered"
	if replaced {
		verb = "updated"
	}
	fmt.Printf("Successfully %s TANTRA evaluator %q\n", verb, evID)
	fmt.Printf("  schema_version: %s\n", schema)
	fmt.Printf("  algorithm:      %s\n", alg)
	fmt.Printf("  key_id:         %s\n", keyID)
	fmt.Printf("  snapshot:       %s\n", snapshotPath)
	if apiKeyFP != "" {
		fmt.Printf("  api_key_fingerprint: %s\n", apiKeyFP)
	}
	return 0
}

func writeTantraSnapshotAtomically(path string, snap *TantraTrustSnapshotFile) error {
	dir := filepath.Dir(path)
	if dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return err
		}
	}
	out, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, out, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}

func appendTantraRegistryAudit(row map[string]interface{}) {
	dir := filepath.Dir(tantraRegistryAuditLog)
	if dir != "" && dir != "." {
		_ = os.MkdirAll(dir, 0o755)
	}
	raw, err := json.Marshal(row)
	if err != nil {
		return
	}
	raw = append(raw, '\n')
	f, err := os.OpenFile(tantraRegistryAuditLog, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer f.Close()
	_, _ = f.Write(raw)
}
