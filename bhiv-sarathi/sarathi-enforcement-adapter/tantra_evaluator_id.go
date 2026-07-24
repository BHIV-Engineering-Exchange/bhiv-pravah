package main

// tantra_evaluator_id.go — Parser and validator for TANTRA evaluator IDs.
//
// Contract §4 format:
//
//   bhiv.<system>.<component>.<environment>.v<major>
//
// Examples (all SHOULD pass):
//
//   bhiv.sovereign.decision.prod.v1
//   bhiv.sarathi.enforcement.prod.v1
//   bhiv.core.local.dev.v1
//
// Examples (MUST fail):
//
//   sovereign_bhiv_core                  (legacy v15.5 format — explicitly rejected)
//   bhiv.sovereign.decision.prod         (missing version)
//   BHIV.sovereign.decision.prod.v1      (case-sensitive: lowercase prefix only)
//   bhiv..decision.prod.v1               (empty segment)
//   bhiv.sovereign.decision.prod.v0      (version must be >= 1)
//   bhiv.sovereign.decision.prod.v1.extra (trailing segments)
//
// Anchored regex enforces the shape; an explicit four-segment split is then
// performed so the verifier can surface the offending field name in error
// detail strings.
//
// TAG: tantra-v15.7

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

// tantraEvaluatorIDRegex is anchored, case-sensitive, lowercase-only.
// Segments: [a-z0-9_]+ (no dots, no uppercase, no hyphens to keep the
// format unambiguous against other identifier schemes Sarathi uses).
var tantraEvaluatorIDRegex = regexp.MustCompile(
	`^bhiv\.([a-z0-9_]+)\.([a-z0-9_]+)\.([a-z0-9_]+)\.v([0-9]+)$`,
)

// TantraEvaluatorID is the parsed, validated, structured form. The original
// string is preserved in Raw so signature verification / canonical bytes use
// EXACTLY what came over the wire (case, etc.).
type TantraEvaluatorID struct {
	Raw         string
	System      string
	Component   string
	Environment string
	MajorVersion int
}

// String returns the canonical form (Raw).
func (id TantraEvaluatorID) String() string { return id.Raw }

// ParseTantraEvaluatorID returns a parsed identifier or a TantraValidationError
// with code ERR_TANTRA_EVALUATOR_ID_FORMAT and a precise detail string.
func ParseTantraEvaluatorID(raw string) (TantraEvaluatorID, error) {
	clean := strings.TrimSpace(raw)
	if clean == "" {
		return TantraEvaluatorID{}, &TantraValidationError{
			Code:   ErrTantraEvaluatorIDFormat,
			Detail: "evaluator_id is empty",
		}
	}
	m := tantraEvaluatorIDRegex.FindStringSubmatch(clean)
	if m == nil {
		return TantraEvaluatorID{}, &TantraValidationError{
			Code: ErrTantraEvaluatorIDFormat,
			Detail: fmt.Sprintf(
				"evaluator_id %q does not match bhiv.<system>.<component>.<environment>.v<major> "+
					"(lowercase, segments use [a-z0-9_]+, version >=1)",
				clean,
			),
		}
	}
	major, err := strconv.Atoi(m[4])
	if err != nil || major < 1 {
		return TantraEvaluatorID{}, &TantraValidationError{
			Code:   ErrTantraEvaluatorIDFormat,
			Detail: fmt.Sprintf("evaluator_id version v%s must be a positive integer >=1", m[4]),
		}
	}
	return TantraEvaluatorID{
		Raw:          clean,
		System:       m[1],
		Component:    m[2],
		Environment:  m[3],
		MajorVersion: major,
	}, nil
}

// IsTantraEvaluatorIDFormat returns true if raw parses successfully. Convenience
// wrapper for boundary checks where the structured form is not needed.
func IsTantraEvaluatorIDFormat(raw string) bool {
	_, err := ParseTantraEvaluatorID(raw)
	return err == nil
}

// SovereignDecisionEvaluatorID is the contract-mandated identifier for the
// upstream Sovereign Core evaluator.
const SovereignDecisionEvaluatorID = "bhiv.sovereign.decision.prod.v1"

// SarathiEnforcementEvaluatorID is the contract-mandated identifier Sarathi
// uses when emitting its own enforcement_binding attestations.
const SarathiEnforcementEvaluatorID = "bhiv.sarathi.enforcement.prod.v1"

// AssertTantraEvaluatorID is a defensive helper that panics if the constant
// string is wrong at compile/init time. Used in init() to guard refactors that
// might break one of the constants above.
func AssertTantraEvaluatorID(raw string) TantraEvaluatorID {
	id, err := ParseTantraEvaluatorID(raw)
	if err != nil {
		panic(fmt.Sprintf("tantra_evaluator_id: built-in constant %q is invalid: %v", raw, err))
	}
	return id
}

func init() {
	// Self-tests for built-in constants — fail-fast if anyone mutates them.
	_ = AssertTantraEvaluatorID(SovereignDecisionEvaluatorID)
	_ = AssertTantraEvaluatorID(SarathiEnforcementEvaluatorID)
}

// SplitKeyID parses a "<evaluator_id>#<rotation_tag>" string into its two
// halves. The rotation tag is opaque to Sarathi; we only validate the prefix
// before the '#' parses as a TANTRA evaluator_id, and that exactly one '#'
// separator is present.
//
// Returns (parsed_evaluator_id, rotation_tag, nil) on success or a
// TantraValidationError on failure.
func SplitKeyID(keyID string) (TantraEvaluatorID, string, error) {
	clean := strings.TrimSpace(keyID)
	idx := strings.IndexByte(clean, '#')
	if idx < 0 {
		return TantraEvaluatorID{}, "", &TantraValidationError{
			Code:   ErrTantraKeyIDMismatch,
			Detail: fmt.Sprintf("key_id %q is missing the '#<rotation>' suffix", clean),
		}
	}
	if strings.Count(clean, "#") != 1 {
		return TantraEvaluatorID{}, "", &TantraValidationError{
			Code:   ErrTantraKeyIDMismatch,
			Detail: fmt.Sprintf("key_id %q contains more than one '#' separator", clean),
		}
	}
	prefix := clean[:idx]
	suffix := clean[idx+1:]
	id, err := ParseTantraEvaluatorID(prefix)
	if err != nil {
		return TantraEvaluatorID{}, "", err
	}
	if strings.TrimSpace(suffix) == "" {
		return TantraEvaluatorID{}, "", &TantraValidationError{
			Code:   ErrTantraKeyIDMismatch,
			Detail: "key_id rotation suffix is empty",
		}
	}
	return id, suffix, nil
}
