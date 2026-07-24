package main

// tantra_trust_extension.go — TANTRA-aware extension of the existing
// TrustConsumer / EvaluatorTrustSnapshot model.
//
// Strategy: rather than modifying the existing struct in external_decision.go
// (which is reused by every legacy code path), this file adds a parallel
// table in the trust snapshot JSON for the TANTRA-specific columns
// (key_id, schema_version, algorithm) and wires the four-gate lookup the
// TANTRA verifier needs:
//
//   1. evaluator_id exists in registry              (existence)
//   2. status == ACTIVE                              (active)
//   3. registry schema_version == payload schema    (schema match)
//   4. registry key_id == signature.key_id          (key_id match)
//   5. registry algorithm == signature.alg          (algorithm match,
//                                                    additional CSO control)
//
// The new columns are loaded from an optional `tantra_evaluators` array in
// the trust snapshot JSON file. Snapshots without this array continue to
// load as before — TANTRA lookups simply return ERR_TANTRA_EVALUATOR_NOT_REGISTERED.
//
// FILE LAYOUT (live/trust_snapshot.json, additive):
//
//   {
//     "version": "1",
//     "evaluators": [ ...legacy entries... ],
//     "tantra_evaluators": [
//       {
//         "evaluator_id":   "bhiv.sovereign.decision.prod.v1",
//         "name":           "Sovereign BHIV Core",
//         "status":         "ACTIVE",
//         "schema_version": "tantra.decision.v1",
//         "algorithm":      "Ed25519",
//         "key_id":         "bhiv.sovereign.decision.prod.v1#ed25519-2026-05",
//         "public_key":     "<hex-or-base64url>",
//         "api_key_fingerprint": "<sha256_hex>"
//       }
//     ]
//   }
//
// The `public_key` encoding is algorithm-specific:
//   - "Ed25519"                  → hex(32 bytes)
//   - "Composite-MLDSA65-Ed25519" → base64url-no-pad TLV envelope
//
// This lets a single trust snapshot serve both providers.
//
// TAG: tantra-v15.7

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"
)

// TantraEvaluatorEntry is the on-disk shape of one TANTRA trust row.
type TantraEvaluatorEntry struct {
	EvaluatorID       string `json:"evaluator_id"`
	Name              string `json:"name"`
	Status            string `json:"status"` // ACTIVE / SUSPENDED / REVOKED
	SchemaVersion     string `json:"schema_version"`
	Algorithm         string `json:"algorithm"`
	KeyID             string `json:"key_id"`
	PublicKey         string `json:"public_key"`
	APIKeyFingerprint string `json:"api_key_fingerprint,omitempty"`
	RegisteredAt      string `json:"registered_at,omitempty"`
	Notes             string `json:"notes,omitempty"`
}

// TantraTrustSnapshotFile is the EXTENDED snapshot file shape. The legacy
// `evaluators` array continues to live on `TrustSnapshotFile`; this struct
// adds the TANTRA-side array. Loading uses both — see LoadTantraTrustExtension.
type TantraTrustSnapshotFile struct {
	Version          string                  `json:"version"`
	Evaluators       []EvaluatorTrustSnapshot `json:"evaluators,omitempty"`
	TantraEvaluators []TantraEvaluatorEntry   `json:"tantra_evaluators,omitempty"`
}

// LoadTantraTrustExtension reads the trust snapshot file and returns ONLY the
// TANTRA section. If the file is missing the section, returns an empty slice
// — not an error.
func LoadTantraTrustExtension(path string) ([]TantraEvaluatorEntry, error) {
	if strings.TrimSpace(path) == "" {
		return nil, fmt.Errorf("tantra_trust: snapshot path is empty")
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("tantra_trust: read %s: %w", path, err)
	}
	var f TantraTrustSnapshotFile
	if err := json.Unmarshal(data, &f); err != nil {
		return nil, fmt.Errorf("tantra_trust: parse %s: %w", path, err)
	}
	return f.TantraEvaluators, nil
}

// ============================================================================
// In-memory TANTRA trust registry
// ============================================================================

// TantraTrustConsumer is the TANTRA-aware lookup layer. It wraps any number of
// TantraEvaluatorEntry rows loaded from disk + adapts them through the active
// CryptoProvider so the registry stays algorithm-agnostic.
type TantraTrustConsumer struct {
	mu      sync.RWMutex
	byID    map[string]*tantraTrustEntry
	loaded  time.Time
}

type tantraTrustEntry struct {
	entry  TantraEvaluatorEntry
	pubKey PublicKeyMaterial
}

// NewTantraTrustConsumer builds a TantraTrustConsumer from a slice of entries.
// `provider` is the active CryptoProvider — used to parse the public keys
// at load time so verify is a hot-path no-allocation step.
//
// Validation performed at load time:
//   - evaluator_id parses as a TANTRA evaluator id
//   - schema_version is non-empty (no default — we want operator intent
//     visible in the snapshot)
//   - algorithm is "Ed25519" or "Composite-MLDSA65-Ed25519"
//   - algorithm matches the active provider (otherwise the verifier would
//     never be able to use this row — better to fail at boot)
//   - key_id parses as "<evaluator_id>#<rotation>"
//   - public_key parses under the active provider
//
// Rows that fail validation are dropped with a stderr warning — they cannot
// silently pass the lookup but the process continues. This matches the
// existing trust-snapshot loader's behaviour for malformed legacy entries.
//
// Returns the populated consumer + the count of rows accepted.
func NewTantraTrustConsumer(entries []TantraEvaluatorEntry, provider CryptoProvider) (*TantraTrustConsumer, int, error) {
	tc := &TantraTrustConsumer{
		byID:   make(map[string]*tantraTrustEntry),
		loaded: time.Now().UTC(),
	}
	accepted := 0
	for _, e := range entries {
		if err := validateTantraEntryShape(e); err != nil {
			fmt.Fprintf(os.Stderr, "[tantra_trust] WARN skip evaluator_id=%q: %v\n", e.EvaluatorID, err)
			continue
		}
		if CryptoAlgorithmID(e.Algorithm) != provider.Algorithm() {
			fmt.Fprintf(os.Stderr,
				"[tantra_trust] WARN skip evaluator_id=%q: algorithm %q != active provider %q\n",
				e.EvaluatorID, e.Algorithm, provider.Algorithm())
			continue
		}
		pub, err := provider.ParsePublicKey(e.PublicKey)
		if err != nil {
			fmt.Fprintf(os.Stderr,
				"[tantra_trust] WARN skip evaluator_id=%q: public_key parse: %v\n",
				e.EvaluatorID, err)
			continue
		}
		tc.byID[e.EvaluatorID] = &tantraTrustEntry{entry: e, pubKey: pub}
		accepted++
	}
	return tc, accepted, nil
}

func validateTantraEntryShape(e TantraEvaluatorEntry) error {
	if _, err := ParseTantraEvaluatorID(e.EvaluatorID); err != nil {
		return err
	}
	if strings.TrimSpace(e.SchemaVersion) == "" {
		return fmt.Errorf("schema_version is empty")
	}
	switch CryptoAlgorithmID(e.Algorithm) {
	case CryptoAlgEd25519, CryptoAlgCompositeMLDSA65Ed25519:
	default:
		return fmt.Errorf("algorithm %q is not a recognised CryptoAlgorithmID", e.Algorithm)
	}
	if strings.TrimSpace(e.KeyID) == "" {
		return fmt.Errorf("key_id is empty")
	}
	parsedID, _, err := SplitKeyID(e.KeyID)
	if err != nil {
		return fmt.Errorf("key_id: %w", err)
	}
	if parsedID.Raw != e.EvaluatorID {
		return fmt.Errorf("key_id prefix %q does not match evaluator_id %q", parsedID.Raw, e.EvaluatorID)
	}
	if strings.TrimSpace(e.PublicKey) == "" {
		return fmt.Errorf("public_key is empty")
	}
	if strings.ToUpper(strings.TrimSpace(e.Status)) == "" {
		return fmt.Errorf("status is empty")
	}
	return nil
}

// ============================================================================
// Four-gate lookup (Contract §4)
// ============================================================================

// TantraTrustLookupResult carries everything the verifier needs.
type TantraTrustLookupResult struct {
	Entry  TantraEvaluatorEntry
	PubKey PublicKeyMaterial
}

// Lookup performs the four-gate validation:
//
//   1. evaluator_id exists                          -> ErrTantraEvaluatorNotRegistered
//   2. status is ACTIVE                              -> ErrTantraEvaluatorNotActive
//   3. registry schema_version == payload schema    -> ErrTantraEvaluatorSchemaMismatch
//   4. registry key_id == signature.key_id          -> ErrTantraKeyIDMismatch
//
// Additional CSO gate (load-bearing for provider-mismatch detection):
//   5. registry algorithm == signature.alg          -> ErrTantraAlgMismatch
//
// On success returns the registered entry + parsed public key material.
func (tc *TantraTrustConsumer) Lookup(evaluatorID, payloadSchemaVersion, sigKeyID, sigAlg string) (*TantraTrustLookupResult, error) {
	tc.mu.RLock()
	defer tc.mu.RUnlock()
	entry, ok := tc.byID[evaluatorID]
	if !ok {
		return nil, &TantraValidationError{
			Code:   ErrTantraEvaluatorNotRegistered,
			Detail: fmt.Sprintf("evaluator_id %q not in TANTRA registry", evaluatorID),
		}
	}
	if strings.ToUpper(strings.TrimSpace(entry.entry.Status)) != "ACTIVE" {
		return nil, &TantraValidationError{
			Code:   ErrTantraEvaluatorNotActive,
			Detail: fmt.Sprintf("evaluator_id %q status=%s", evaluatorID, entry.entry.Status),
		}
	}
	if entry.entry.SchemaVersion != payloadSchemaVersion {
		return nil, &TantraValidationError{
			Code: ErrTantraEvaluatorSchemaMismatch,
			Detail: fmt.Sprintf(
				"evaluator_id %q registered schema_version=%q, payload schema_version=%q",
				evaluatorID, entry.entry.SchemaVersion, payloadSchemaVersion,
			),
		}
	}
	if entry.entry.KeyID != sigKeyID {
		return nil, &TantraValidationError{
			Code: ErrTantraKeyIDMismatch,
			Detail: fmt.Sprintf(
				"evaluator_id %q registered key_id=%q, signature.key_id=%q",
				evaluatorID, entry.entry.KeyID, sigKeyID,
			),
		}
	}
	if entry.entry.Algorithm != sigAlg {
		return nil, &TantraValidationError{
			Code: ErrTantraAlgMismatch,
			Detail: fmt.Sprintf(
				"evaluator_id %q registered algorithm=%q, signature.alg=%q",
				evaluatorID, entry.entry.Algorithm, sigAlg,
			),
		}
	}
	return &TantraTrustLookupResult{Entry: entry.entry, PubKey: entry.pubKey}, nil
}

// Count returns the number of accepted entries; used for boot banners.
func (tc *TantraTrustConsumer) Count() int {
	tc.mu.RLock()
	defer tc.mu.RUnlock()
	return len(tc.byID)
}

// ============================================================================
// Boot wiring
// ============================================================================

// activeTantraTrust is set once at boot by BootstrapTantraTrust. Verifier code
// reads it via ActiveTantraTrust().
var activeTantraTrust *TantraTrustConsumer

// BootstrapTantraTrust loads the TANTRA section from the configured snapshot
// path (SARATHI_TRUST_SNAPSHOT) under the active CryptoProvider. Idempotent
// and safe to call before/after InitCryptoProvider — but the provider MUST be
// initialised first since TANTRA entry validation uses it.
func BootstrapTantraTrust(snapshotPath string) (*TantraTrustConsumer, error) {
	if activeProvider == nil {
		return nil, fmt.Errorf("tantra_trust: BootstrapTantraTrust called before InitCryptoProvider")
	}
	if strings.TrimSpace(snapshotPath) == "" {
		// No snapshot path → empty registry. Verifier will reject every TANTRA
		// payload with ErrTantraEvaluatorNotRegistered, which is the correct
		// fail-closed behaviour.
		tc, _, _ := NewTantraTrustConsumer(nil, activeProvider)
		activeTantraTrust = tc
		return tc, nil
	}
	entries, err := LoadTantraTrustExtension(snapshotPath)
	if err != nil {
		return nil, err
	}
	tc, accepted, err := NewTantraTrustConsumer(entries, activeProvider)
	if err != nil {
		return nil, err
	}
	activeTantraTrust = tc
	fmt.Fprintf(os.Stderr, "[tantra_trust] loaded %d/%d entries from %s (provider=%s)\n",
		accepted, len(entries), snapshotPath, activeProvider.Algorithm())
	return tc, nil
}

// ActiveTantraTrust returns the boot-loaded TANTRA registry, or nil if
// BootstrapTantraTrust has not yet run. The verifier checks for nil and
// fails closed with ERR_TANTRA_EVALUATOR_NOT_REGISTERED.
func ActiveTantraTrust() *TantraTrustConsumer { return activeTantraTrust }

// SetActiveTantraTrustForTest replaces the active registry — test only.
func SetActiveTantraTrustForTest(tc *TantraTrustConsumer) { activeTantraTrust = tc }
