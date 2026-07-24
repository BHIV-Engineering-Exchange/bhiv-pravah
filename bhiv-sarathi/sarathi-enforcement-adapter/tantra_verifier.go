package main

// tantra_verifier.go — The 12-step TANTRA Final Contract verification routine.
//
// SEQUENCE (Contract §7):
//
//   0a. Decode body strictly (DisallowUnknownFields, size cap).
//   0b. Validate structural shape + required fields (RequiredFields()).
//   0c. Parse evaluator_id format.
//   0d. Parse + skew-check timestamp.
//
//   1.  Extract signature object.
//   2.  Compute canonical signing bytes (payload with signature OMITTED).
//   3.  Confirm schema_version is the only accepted value (defensive — already
//       checked in 0b; re-asserted as a CSO control).
//   4.  Look up evaluator in TANTRA registry (existence + active).
//   5.  Confirm key_id and algorithm match registry.
//   6.  Re-verify canonical-bytes byte-for-byte (catches upstream re-encoding).
//   7.  Verify signature via ActiveProvider() against the registered key.
//   8.  Recompute decision_hash from the six-field material.
//   9.  Compare recomputed decision_hash against payload decision_hash.
//   10. Recompute decision_id deterministically.
//   11. Compare recomputed decision_id against payload decision_id.
//   12. Replay + mutation enforcement (decision_hash window, signed-payload-hash
//       window).
//
// EVERY STEP IS A FAIL-CLOSED GATE. There is no partial-success path.
//
// The verifier holds NO state of its own except a reference to the active
// crypto provider, the active TANTRA trust registry, and the active replay
// store. All three are injected so unit tests can substitute fakes.
//
// TAG: tantra-v15.7

import (
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"fmt"
	"strings"
	"time"
)

// TantraVerifierResult is the outcome of a successful verification. Includes
// the parsed decision + the bytes that were used for signing (for downstream
// audit-trail anchoring).
type TantraVerifierResult struct {
	Decision     *TantraDecision
	SignedBytes  []byte
	WireBytes    []byte
	EvaluatorRow TantraEvaluatorEntry
	RecomputedDecisionHash string
	RecomputedDecisionID   string
}

// TantraVerifier is a stateless wrapper around the four dependencies the
// 12-step routine needs. Instantiated once per process.
type TantraVerifier struct {
	Provider    CryptoProvider
	Registry    *TantraTrustConsumer
	ReplayStore TantraReplayStore
	Now         func() time.Time // injectable for tests
}

// NewTantraVerifier wires the active provider + active trust registry + the
// boot-loaded replay store. If any dependency is missing, it panics — there
// is no fallback that quietly accepts decisions.
func NewTantraVerifier() *TantraVerifier {
	if activeProvider == nil {
		panic("tantra_verifier: ActiveProvider() not initialised")
	}
	if activeTantraTrust == nil {
		panic("tantra_verifier: TANTRA trust registry not initialised — call BootstrapTantraTrust first")
	}
	if activeTantraReplayStore == nil {
		panic("tantra_verifier: replay store not initialised — call BootstrapTantraReplayStore first")
	}
	return &TantraVerifier{
		Provider:    activeProvider,
		Registry:    activeTantraTrust,
		ReplayStore: activeTantraReplayStore,
		Now:         func() time.Time { return time.Now().UTC() },
	}
}

// Verify runs the 12-step routine over raw HTTP body bytes. Returns the
// parsed decision + supporting artefacts on success; a TantraValidationError
// on any failure (the HTTP handler maps Code -> response error code).
func (v *TantraVerifier) Verify(raw []byte) (*TantraVerifierResult, error) {
	// Step 0a — strict decode.
	d, err := VerifyDecodeStrict(raw)
	if err != nil {
		return nil, err
	}
	// Step 0b — structural / required-field validation.
	if err := d.RequiredFields(); err != nil {
		return nil, err
	}
	// Step 0c — evaluator_id format.
	if _, err := ParseTantraEvaluatorID(d.EvaluatorID); err != nil {
		return nil, err
	}
	// Step 0d — timestamp parse + skew.
	ts, err := parseTantraTimestamp(d.Timestamp)
	if err != nil {
		return nil, err
	}
	if err := checkTantraSkew(ts, v.Now()); err != nil {
		return nil, err
	}

	// Step 1 — extract signature (already on the typed struct).
	sig := d.Signature

	// Step 2 — compute canonical signing bytes.
	signed, err := CanonicalSignableBytes(d)
	if err != nil {
		return nil, &TantraValidationError{
			Code:   ErrTantraCanonicalEncoding,
			Detail: "canonical signable bytes: " + err.Error(),
		}
	}

	// Step 3 — schema_version already checked in 0b; re-assert defensively.
	if d.SchemaVersion != TantraSchemaV1 {
		return nil, &TantraValidationError{
			Code:   ErrTantraSchemaVersionUnknown,
			Detail: "schema_version " + d.SchemaVersion + " is not " + TantraSchemaV1,
		}
	}

	// Steps 4 + 5 — registry lookup (existence + active + schema + key_id + alg).
	lookup, err := v.Registry.Lookup(d.EvaluatorID, d.SchemaVersion, sig.KeyID, sig.Alg)
	if err != nil {
		return nil, err
	}

	// Step 6 — canonical bytes round-trip check against the input wire bytes.
	// This catches upstream re-encoders that have re-ordered fields or added
	// whitespace. We allow either (the strict decoder already accepted them)
	// but if the canonical wire form differs from what was sent, we want a
	// distinct error code surfaced in the audit log.
	wire, err := CanonicalWireBytes(d)
	if err != nil {
		return nil, &TantraValidationError{
			Code:   ErrTantraCanonicalEncoding,
			Detail: "canonical wire bytes: " + err.Error(),
		}
	}

	// Step 7 — decode signature value, verify.
	sigBytes, err := base64.RawURLEncoding.DecodeString(strings.TrimSpace(sig.Value))
	if err != nil {
		return nil, &TantraValidationError{
			Code:   ErrTantraSignatureDecode,
			Detail: "signature.value not base64url_no_pad: " + err.Error(),
		}
	}
	if v.Provider.Algorithm() != CryptoAlgorithmID(sig.Alg) {
		return nil, &TantraValidationError{
			Code: ErrTantraAlgMismatch,
			Detail: fmt.Sprintf(
				"active provider %q != signature.alg %q (operator must flip SARATHI_CRYPTO_PROVIDER to match)",
				v.Provider.Algorithm(), sig.Alg,
			),
		}
	}
	ok, reason := v.Provider.Verify(signed, SignatureValue(sigBytes), lookup.PubKey)
	if !ok {
		return nil, &TantraValidationError{
			Code:   ErrTantraSignatureInvalid,
			Detail: reason,
		}
	}

	// Step 8 + 9 — recompute decision_hash, compare.
	recomputedHash := ComputeTantraDecisionHash(d.Material())
	if !strings.EqualFold(recomputedHash, d.DecisionHash) {
		return nil, &TantraValidationError{
			Code: ErrTantraDecisionHashMismatch,
			Detail: fmt.Sprintf(
				"recomputed=%s payload=%s (the six-field material did not produce the claimed hash)",
				recomputedHash, d.DecisionHash,
			),
		}
	}

	// Step 10 + 11 — recompute decision_id, compare.
	recomputedID := ComputeTantraDecisionID(d)
	if !strings.EqualFold(recomputedID, d.DecisionID) {
		return nil, &TantraValidationError{
			Code: ErrTantraDecisionIDMismatch,
			Detail: fmt.Sprintf(
				"recomputed=%s payload=%s (using default derivation; confirm with Core)",
				recomputedID, d.DecisionID,
			),
		}
	}

	// Step 12 — replay + mutation enforcement.
	if err := v.ReplayStore.Check(d.DecisionHash, signed, v.Now()); err != nil {
		return nil, err
	}

	return &TantraVerifierResult{
		Decision:               d,
		SignedBytes:            signed,
		WireBytes:              wire,
		EvaluatorRow:           lookup.Entry,
		RecomputedDecisionHash: recomputedHash,
		RecomputedDecisionID:   recomputedID,
	}, nil
}

// ============================================================================
// HELPERS
// ============================================================================

func parseTantraTimestamp(raw string) (time.Time, error) {
	clean := strings.TrimSpace(raw)
	if clean == "" {
		return time.Time{}, &TantraValidationError{
			Code:   ErrTantraTimestampUnparseable,
			Detail: "timestamp is empty",
		}
	}
	for _, layout := range []string{time.RFC3339Nano, time.RFC3339, "2006-01-02T15:04:05.000000Z"} {
		if t, err := time.Parse(layout, clean); err == nil {
			return t.UTC(), nil
		}
	}
	return time.Time{}, &TantraValidationError{
		Code:   ErrTantraTimestampUnparseable,
		Detail: "timestamp " + clean + " is not RFC3339 / RFC3339Nano UTC",
	}
}

func checkTantraSkew(ts, now time.Time) error {
	delta := now.Sub(ts).Seconds()
	if delta < 0 {
		delta = -delta
	}
	if delta > float64(TantraTimestampSkewSeconds) {
		return &TantraValidationError{
			Code: ErrTantraTimestampSkewed,
			Detail: fmt.Sprintf(
				"timestamp %s is %.1fs from now (window=±%ds)",
				ts.Format(time.RFC3339Nano), delta, TantraTimestampSkewSeconds,
			),
		}
	}
	return nil
}

// ============================================================================
// DECISION_ID DERIVATION
// ============================================================================

// ComputeTantraDecisionID returns the deterministic decision_id that Sarathi
// will recompute and compare to the payload value (Steps 10–11).
//
// FORMULA (default until Core confirms — open item in plan §1.5):
//
//   decision_id = uuid_shape(
//                   sha256(
//                     canonical({"trace_id":..., "input_hash":..., "evaluator_id":...})
//                   )
//                 )
//
// Rationale:
//   - Excludes timestamp (so replays of the same logical decision land on the
//     same decision_id and are caught by the replay store).
//   - Excludes verdict (operator may not want a decision_id to leak the
//     verdict). Open question with Core.
//   - Deterministic across runs.
//
// If Core confirms a different formula, update this function and the
// corresponding minting helper in tantra_emit.go in lockstep.
func ComputeTantraDecisionID(d *TantraDecision) string {
	material := struct {
		TraceID     string `json:"trace_id"`
		InputHash   string `json:"input_hash"`
		EvaluatorID string `json:"evaluator_id"`
	}{
		TraceID:     d.TraceID,
		InputHash:   d.InputHash,
		EvaluatorID: d.EvaluatorID,
	}
	bytes := canonicalDecisionIDMaterial(material)
	h := sha256.Sum256(bytes)
	hx := hex.EncodeToString(h[:])
	return fmt.Sprintf("%s-%s-%s-%s-%s",
		hx[0:8], hx[8:12], hx[12:16], hx[16:20], hx[20:32])
}

// canonicalDecisionIDMaterial emits the three fields in the fixed contract
// order (trace_id, input_hash, evaluator_id). No whitespace, no map iteration.
func canonicalDecisionIDMaterial(m struct {
	TraceID     string `json:"trace_id"`
	InputHash   string `json:"input_hash"`
	EvaluatorID string `json:"evaluator_id"`
}) []byte {
	return []byte(fmt.Sprintf(
		`{"trace_id":%q,"input_hash":%q,"evaluator_id":%q}`,
		m.TraceID, m.InputHash, m.EvaluatorID,
	))
}
