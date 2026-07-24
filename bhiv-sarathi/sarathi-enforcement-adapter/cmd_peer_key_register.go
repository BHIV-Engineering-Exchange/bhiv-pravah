package main

// cmd_peer_key_register.go — `--register-peer-key` admin CLI (v15.9).
//
// Inserts or updates a peer's PINNED public key in live/trust_snapshot.json
// under the `peer_keys` array. Sarathi's VerifyReceipt then refuses any
// receipt from that peer whose embedded public_key_hex does not match.
//
// SECURITY POSTURE:
//   - Caller supplies the PUBLIC key only. Private keys NEVER travel through
//     this CLI; they live with the peer that owns them.
//   - Strict format validation before write (hex, 32 bytes, known peer kind).
//   - Atomic snapshot write (tmp + rename) so a crash mid-write cannot
//     corrupt the file or leave a half-truncated row.
//   - Preserves every other top-level key in the snapshot (evaluators,
//     tantra_evaluators, etc.) via raw-map round-tripping — no field loss
//     across upgrades.
//   - One audit row per registration appended to
//     proof_logs/peer_key_registry_audit.jsonl.
//
// TAG: peer-key-registry-v15.9

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

func runRegisterPeerKey(args []string) int {
	flags, _ := parseCLIFlags(args)
	peer := strings.TrimSpace(flags["peer"])
	pubKey := strings.TrimSpace(flags["public-key"])
	name := strings.TrimSpace(flags["name"])
	notes := strings.TrimSpace(flags["notes"])
	snapshotPath := resolveSnapshotPath(flags)

	if peer == "" || pubKey == "" {
		fmt.Fprintln(os.Stderr, "register-peer-key: --peer and --public-key are required")
		fmt.Fprintln(os.Stderr, "Usage:")
		fmt.Fprintln(os.Stderr, "  --register-peer-key --peer=bucket --public-key=<64-hex>")
		fmt.Fprintln(os.Stderr, "                       [--name=\"Bucket production\"] [--notes=\"...\"]")
		fmt.Fprintln(os.Stderr, "                       [--snapshot=./live/trust_snapshot.json]")
		return 2
	}

	switch peer {
	case "bucket", "core", "insightflow":
		// OK
	default:
		fmt.Fprintf(os.Stderr,
			"register-peer-key: --peer must be one of bucket/core/insightflow (got %q)\n", peer)
		return 2
	}

	// Validate the public key parses to 32 raw bytes.
	pubBytes, err := hex.DecodeString(pubKey)
	if err != nil || len(pubBytes) != 32 {
		fmt.Fprintf(os.Stderr,
			"register-peer-key: --public-key must be 32-byte (64-char) hex Ed25519 public key (got len=%d hex chars, err=%v)\n",
			len(pubKey), err)
		return 2
	}
	pubKey = strings.ToLower(pubKey)

	// Read the existing snapshot as a raw map so we DO NOT clobber unknown
	// fields the loader might not yet model (evaluators, tantra_evaluators,
	// future fields). We only touch the peer_keys array.
	var raw map[string]json.RawMessage
	if data, rerr := os.ReadFile(snapshotPath); rerr == nil {
		_ = json.Unmarshal(data, &raw)
	}
	if raw == nil {
		raw = map[string]json.RawMessage{}
	}

	var peerKeys []PeerKeyEntry
	if pkRaw, ok := raw["peer_keys"]; ok && len(pkRaw) > 0 {
		_ = json.Unmarshal(pkRaw, &peerKeys)
	}

	row := PeerKeyEntry{
		Peer:         peer,
		Name:         name,
		Status:       PeerKeyStatusActive,
		PublicKeyHex: pubKey,
		RegisteredAt: time.Now().UTC().Format(time.RFC3339Nano),
		Notes:        notes,
	}

	replaced := false
	for i := range peerKeys {
		if peerKeys[i].Peer == peer {
			peerKeys[i] = row
			replaced = true
			break
		}
	}
	if !replaced {
		peerKeys = append(peerKeys, row)
	}

	newRaw, err := json.Marshal(peerKeys)
	if err != nil {
		fmt.Fprintf(os.Stderr, "register-peer-key: marshal peer_keys: %v\n", err)
		return 1
	}
	raw["peer_keys"] = newRaw
	if _, ok := raw["version"]; !ok {
		v, _ := json.Marshal("v15.9")
		raw["version"] = v
	}

	out, err := json.MarshalIndent(raw, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "register-peer-key: marshal snapshot: %v\n", err)
		return 1
	}

	if err := writePeerKeySnapshotAtomically(snapshotPath, out); err != nil {
		fmt.Fprintf(os.Stderr, "register-peer-key: write snapshot: %v\n", err)
		return 1
	}

	AppendPeerKeyRegistryAudit("register_peer_key", peer, pubKey, snapshotPath, replaced)

	verb := "registered"
	if replaced {
		verb = "updated"
	}
	fmt.Printf("Successfully %s peer key for peer=%s\n", verb, peer)
	fmt.Printf("  status:           ACTIVE\n")
	fmt.Printf("  public_key_hex:   %s\n", pubKey)
	fmt.Printf("  key_fingerprint:  %s\n", fingerprint16(pubKey))
	fmt.Printf("  snapshot:         %s\n", snapshotPath)
	fmt.Println()
	fmt.Println("Pinning is now enforced for this peer. The /v1/downstream-ack handler")
	fmt.Printf("will refuse any receipt from peer=%q whose embedded public_key_hex does\n", peer)
	fmt.Println("not match the registered value above.")
	fmt.Println()
	fmt.Println("To enforce strict mode (require a registered key for EVERY peer),")
	fmt.Println("set SARATHI_PEER_KEY_PINNING=strict before --service.")
	return 0
}

func writePeerKeySnapshotAtomically(path string, data []byte) error {
	dir := filepath.Dir(path)
	if dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return err
		}
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}
