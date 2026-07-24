package main

// peer_key_registry.go — v15.9 Peer Public-Key Registry.
//
// Closes the TOFU (trust-on-first-use) weakness in the prior peer-receipt
// model. Before v15.9, /v1/downstream-ack verified peer receipts against the
// public key the peer embedded in the receipt body itself — meaning anyone
// who could land a POST on the endpoint could substitute their own keypair.
// The signature was internally consistent but bound to no registered identity.
//
// v15.9 adds:
//
//   1. A `peer_keys` array in live/trust_snapshot.json carrying the pinned
//      public key (and status) for each peer (bucket, core, insightflow).
//   2. `BootstrapPeerKeyRegistry()` at process boot, before any HTTP listener
//      accepts traffic.
//   3. `CheckPinned()` gate in `peer_common.go::VerifyReceipt` that:
//      - Looks up the peer's registered key.
//      - Compares it (constant time) against the embedded public_key_hex.
//      - Refuses ACTIVE-only status.
//      - Rejects receipts from unregistered peers when mode=strict.
//   4. `--register-peer-key` admin CLI to add / rotate entries on disk.
//
// PINNING MODE (SARATHI_PEER_KEY_PINNING env var):
//
//   "strict"   — every receipt MUST come from a registered peer with a
//                matching key. Unregistered peers are rejected. Use in
//                production.
//
//   "relaxed"  — DEFAULT. If a peer has an entry, it is pinned hard. If a
//                peer has no entry, the embedded key is accepted with a
//                loud stderr warning so the operator notices and pins it.
//                Lets existing deployments keep working while the operator
//                migrates from TOFU to registered keys.
//
// THIS FILE NEVER STORES PRIVATE KEYS. Peer private keys live ONLY with the
// peer that owns them — Sarathi only ever sees public keys.
//
// TAG: peer-key-registry-v15.9

import (
	"crypto/subtle"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"
)

// PeerKeyRegistryAuditLog is the append-only audit trail of registration events.
const PeerKeyRegistryAuditLog = "proof_logs/peer_key_registry_audit.jsonl"

// EnvPeerKeyPinning is the env var controlling the pinning mode.
const EnvPeerKeyPinning = "SARATHI_PEER_KEY_PINNING"

const (
	// PeerKeyPinningRelaxed (default): pin when a registry entry exists;
	// otherwise warn-and-accept the embedded key.
	PeerKeyPinningRelaxed = "relaxed"

	// PeerKeyPinningStrict: require a registry entry for every receipt;
	// reject unregistered peers outright. Use in production.
	PeerKeyPinningStrict = "strict"
)

// PeerKeyStatus mirrors the EvaluatorStatus lifecycle but is intentionally
// kept as a plain string to match how peer_keys is serialised on disk.
const (
	PeerKeyStatusActive    = "ACTIVE"
	PeerKeyStatusSuspended = "SUSPENDED"
	PeerKeyStatusRevoked   = "REVOKED"
)

// PeerKeyEntry is a single pinned peer-key row in the trust snapshot.
type PeerKeyEntry struct {
	Peer         string `json:"peer"`           // "bucket" | "core" | "insightflow"
	Name         string `json:"name,omitempty"` // human-readable label
	Status       string `json:"status"`         // ACTIVE | SUSPENDED | REVOKED
	PublicKeyHex string `json:"public_key_hex"` // 64-hex Ed25519 public key
	RegisteredAt string `json:"registered_at,omitempty"`
	Notes        string `json:"notes,omitempty"`
}

// peerKeySnapshotFile is the on-disk shape Sarathi cares about — only the
// peer_keys array. Other arrays (evaluators, tantra_evaluators) pass through
// untouched via the raw-map approach in cmd_peer_key_register.go.
type peerKeySnapshotFile struct {
	PeerKeys []PeerKeyEntry `json:"peer_keys,omitempty"`
}

// PeerKeyRegistry is the boot-loaded in-memory map of pinned keys.
type PeerKeyRegistry struct {
	mu     sync.RWMutex
	byPeer map[string]*PeerKeyEntry
	mode   string
}

var activePeerKeyRegistry *PeerKeyRegistry

// ActivePeerKeyRegistry returns the boot-loaded registry, or nil if
// BootstrapPeerKeyRegistry has not yet run. VerifyReceipt treats nil as
// "no pinning" (legacy TOFU; logs a one-time warning on first use).
func ActivePeerKeyRegistry() *PeerKeyRegistry { return activePeerKeyRegistry }

// SetActivePeerKeyRegistryForTest is the sanctioned test override.
func SetActivePeerKeyRegistryForTest(r *PeerKeyRegistry) { activePeerKeyRegistry = r }

// loadPeerKeyPinningMode reads SARATHI_PEER_KEY_PINNING. Defaults to relaxed.
func loadPeerKeyPinningMode() string {
	raw := strings.TrimSpace(strings.ToLower(os.Getenv(EnvPeerKeyPinning)))
	switch raw {
	case PeerKeyPinningStrict:
		return PeerKeyPinningStrict
	case PeerKeyPinningRelaxed, "":
		return PeerKeyPinningRelaxed
	default:
		// Unknown value → fail-closed at parse time. Treat as misconfiguration.
		panic(fmt.Sprintf(
			"peer_key_registry: %s=%q is not a valid mode (want %q or %q). "+
				"Process refuses to boot to prevent ambiguous pinning posture.",
			EnvPeerKeyPinning, raw, PeerKeyPinningRelaxed, PeerKeyPinningStrict,
		))
	}
}

// BootstrapPeerKeyRegistry loads peer_keys from the configured trust snapshot.
// Idempotent and safe to call once at process boot. Returns the populated
// registry; also stores it in the package singleton accessed via
// ActivePeerKeyRegistry().
//
// A missing snapshot file is acceptable in relaxed mode (empty registry).
// In strict mode the operator MUST register every expected peer before
// receipts will be accepted.
func BootstrapPeerKeyRegistry(snapshotPath string) (*PeerKeyRegistry, error) {
	reg := &PeerKeyRegistry{
		byPeer: make(map[string]*PeerKeyEntry),
		mode:   loadPeerKeyPinningMode(),
	}
	if strings.TrimSpace(snapshotPath) == "" {
		activePeerKeyRegistry = reg
		fmt.Fprintf(os.Stderr, "[peer_key_registry] no snapshot path; empty registry (mode=%s)\n", reg.mode)
		return reg, nil
	}
	data, err := os.ReadFile(snapshotPath)
	if err != nil {
		if os.IsNotExist(err) {
			activePeerKeyRegistry = reg
			fmt.Fprintf(os.Stderr, "[peer_key_registry] snapshot %s missing; empty registry (mode=%s)\n",
				snapshotPath, reg.mode)
			return reg, nil
		}
		return nil, fmt.Errorf("peer_key_registry: read %s: %w", snapshotPath, err)
	}
	var f peerKeySnapshotFile
	if err := json.Unmarshal(data, &f); err != nil {
		return nil, fmt.Errorf("peer_key_registry: parse %s: %w", snapshotPath, err)
	}
	accepted := 0
	for i := range f.PeerKeys {
		e := f.PeerKeys[i]
		if err := validatePeerKeyEntryShape(&e); err != nil {
			fmt.Fprintf(os.Stderr, "[peer_key_registry] WARN skip peer=%q: %v\n", e.Peer, err)
			continue
		}
		reg.byPeer[e.Peer] = &e
		accepted++
	}
	activePeerKeyRegistry = reg
	fmt.Fprintf(os.Stderr, "[peer_key_registry] loaded %d/%d peer key(s) from %s (mode=%s)\n",
		accepted, len(f.PeerKeys), snapshotPath, reg.mode)
	return reg, nil
}

// validatePeerKeyEntryShape enforces structural correctness at load time.
// A row that fails validation is dropped (not silently accepted) — the
// snapshot loader logs a warning and continues.
func validatePeerKeyEntryShape(e *PeerKeyEntry) error {
	if e == nil {
		return fmt.Errorf("nil entry")
	}
	peer := strings.TrimSpace(e.Peer)
	if peer == "" {
		return fmt.Errorf("peer is empty")
	}
	switch peer {
	case "bucket", "core", "insightflow":
		// OK — the three known peer kinds (matches PeerKind in peer_common.go).
	default:
		return fmt.Errorf("peer %q is not one of bucket/core/insightflow", peer)
	}
	pubBytes, err := hex.DecodeString(strings.TrimSpace(e.PublicKeyHex))
	if err != nil || len(pubBytes) != 32 {
		return fmt.Errorf("public_key_hex must be 32-byte hex (got len=%d, err=%v)", len(pubBytes), err)
	}
	if e.Status == "" {
		e.Status = PeerKeyStatusActive
	}
	switch strings.ToUpper(e.Status) {
	case PeerKeyStatusActive, PeerKeyStatusSuspended, PeerKeyStatusRevoked:
		// OK
	default:
		return fmt.Errorf("status %q is not one of ACTIVE/SUSPENDED/REVOKED", e.Status)
	}
	return nil
}

// Lookup returns a copy of the peer's registry entry, or (nil, false) if no
// row exists. Status filtering is intentionally NOT done here so callers can
// produce precise error messages (e.g., "registered but SUSPENDED" vs "not
// registered").
func (r *PeerKeyRegistry) Lookup(peer string) (*PeerKeyEntry, bool) {
	if r == nil {
		return nil, false
	}
	r.mu.RLock()
	defer r.mu.RUnlock()
	e, ok := r.byPeer[strings.TrimSpace(peer)]
	if !ok {
		return nil, false
	}
	cp := *e
	return &cp, true
}

// Mode returns the active pinning mode ("strict" or "relaxed").
func (r *PeerKeyRegistry) Mode() string {
	if r == nil {
		return PeerKeyPinningRelaxed
	}
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.mode
}

// Count returns the number of registered peer keys.
func (r *PeerKeyRegistry) Count() int {
	if r == nil {
		return 0
	}
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.byPeer)
}

// CheckPinned is the gate the peer-receipt verifier calls AFTER the
// Ed25519 signature has been verified. Returns (ok, reason).
//
// FOUR GATES (in evaluation order):
//
//   G1: cross-peer impersonation — `peerName` MUST be a known peer kind.
//       (Rejects any receipt with peer="evil_attacker".)
//
//   G2: registry presence — based on pinning mode:
//         strict  → entry MUST exist; missing entry is a hard reject.
//         relaxed → missing entry is accepted with a loud stderr warning,
//                   the embedded key is trusted under TOFU fallback.
//
//   G3: status — if entry exists, status MUST be ACTIVE. SUSPENDED and
//       REVOKED reject regardless of pinning mode.
//
//   G4: key pinning — embedded public_key_hex MUST equal registered key
//       (constant-time compare). Mismatch is a hard reject under both
//       modes — pinning, when present, is always enforced.
//
// CROSS-PEER IMPERSONATION DEFENCE: Because the registry is keyed by peer
// name, a receipt with peer="bucket" can only verify if its embedded key
// matches the BUCKET-registered key. An attacker who somehow obtained the
// InsightFlow private key cannot recycle it to forge bucket receipts —
// pinning rejects it at G4 even though the signature would internally verify.
func (r *PeerKeyRegistry) CheckPinned(peerName, embeddedPubHex string) (bool, string) {
	peerName = strings.TrimSpace(peerName)

	// G1: peer field must be a known peer kind.
	switch peerName {
	case "bucket", "core", "insightflow":
		// OK
	case "":
		return false, "peer field is empty"
	default:
		return false, fmt.Sprintf("peer %q is not one of bucket/core/insightflow", peerName)
	}

	// G2: registry presence.
	if r == nil {
		// Registry not initialised — only acceptable in legacy TOFU-only
		// deployments. The boot wiring in enforcement_adapter_main.go always
		// calls BootstrapPeerKeyRegistry, so this branch is for
		// startup-ordering safety.
		fmt.Fprintf(os.Stderr, "[peer_key_registry] WARN: not initialised at receipt time; falling back to TOFU\n")
		return true, ""
	}
	entry, found := r.Lookup(peerName)
	if !found {
		if r.Mode() == PeerKeyPinningStrict {
			return false, fmt.Sprintf("peer %q has no registered key (mode=strict)", peerName)
		}
		fmt.Fprintf(os.Stderr,
			"[peer_key_registry] WARN peer=%q has no pinned key; accepting embedded key under TOFU. "+
				"Pin it with: ./sarathi-enforcement-adapter --register-peer-key --peer=%s --public-key=%s\n",
			peerName, peerName, embeddedPubHex)
		return true, ""
	}

	// G3: status check.
	if strings.ToUpper(entry.Status) != PeerKeyStatusActive {
		return false, fmt.Sprintf("peer %q status=%s (must be ACTIVE)", peerName, entry.Status)
	}

	// G4: constant-time key match.
	if !constantTimeHexEqual(entry.PublicKeyHex, embeddedPubHex) {
		return false, fmt.Sprintf(
			"peer %q embedded public_key_hex does not match registered key (registered_fp=%s embedded_fp=%s)",
			peerName, fingerprint16(entry.PublicKeyHex), fingerprint16(embeddedPubHex),
		)
	}
	return true, ""
}

// constantTimeHexEqual compares two hex-encoded byte strings in constant
// time after lowercasing. Length-mismatch short-circuits (length is not a
// secret). Decoding errors compare-false. Used by G4 above.
func constantTimeHexEqual(a, b string) bool {
	la := strings.ToLower(strings.TrimSpace(a))
	lb := strings.ToLower(strings.TrimSpace(b))
	if len(la) != len(lb) {
		return false
	}
	// Decode both first so a malformed embedded hex can't bypass via odd-length tricks.
	ba, err := hex.DecodeString(la)
	if err != nil {
		return false
	}
	bb, err := hex.DecodeString(lb)
	if err != nil {
		return false
	}
	return subtle.ConstantTimeCompare(ba, bb) == 1
}

// fingerprint16 returns the first 16 hex chars of a hex public key for log
// emission. Useful when full keys would dominate the audit row width.
func fingerprint16(hexKey string) string {
	h := strings.ToLower(strings.TrimSpace(hexKey))
	if len(h) > 16 {
		return h[:16]
	}
	return h
}

// peerKeyRegistryAuditRow is the JSONL shape of one registration event.
type peerKeyRegistryAuditRow struct {
	Timestamp      string `json:"ts"`
	Action         string `json:"action"`
	Peer           string `json:"peer"`
	PublicKeyHex   string `json:"public_key_hex"`
	KeyFingerprint string `json:"key_fingerprint"`
	Replaced       bool   `json:"replaced"`
	SnapshotPath   string `json:"snapshot_path"`
}

// AppendPeerKeyRegistryAudit appends one registration event to the audit log.
// Best-effort — failure logs to stderr but does not block the CLI.
func AppendPeerKeyRegistryAudit(action, peer, pubHex, snapshotPath string, replaced bool) {
	row := peerKeyRegistryAuditRow{
		Timestamp:      time.Now().UTC().Format(time.RFC3339Nano),
		Action:         action,
		Peer:           peer,
		PublicKeyHex:   strings.ToLower(pubHex),
		KeyFingerprint: fingerprint16(pubHex),
		Replaced:       replaced,
		SnapshotPath:   snapshotPath,
	}
	raw, err := json.Marshal(&row)
	if err != nil {
		return
	}
	raw = append(raw, '\n')
	if err := os.MkdirAll("proof_logs", 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "[peer_key_registry] WARN: mkdir audit: %v\n", err)
		return
	}
	f, err := os.OpenFile(PeerKeyRegistryAuditLog, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[peer_key_registry] WARN: open audit: %v\n", err)
		return
	}
	defer f.Close()
	_, _ = f.Write(raw)
}
