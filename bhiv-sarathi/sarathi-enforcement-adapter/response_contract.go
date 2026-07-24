package main

// response_contract.go — Deterministic Response Enforcement Layer (v13 Final Lock).
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Enforcement Adapter (PEP)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   The enforcement kernel (Enforce, PDP, ExecutionEngine) is already correct
//   and cannot be bypassed. The v13 Final Lock task is narrower: make the
//   OUTPUT CONTRACT deterministic. Previously, SarathiEnforcementPipeline.Execute()
//   returned different map shapes depending on which return site was taken —
//   pre-gate rejects returned bare maps with no enforcement/execution envelope
//   at all, so any reader that inspected top-level keys got Go's nil (rendered
//   by fmt as the literal string "<nil>"). The RPSA-01 and RPSA-02 harness
//   failures were a symptom of this: the enforcement WAS producing DENY, but
//   the response was not surfacing it at the top level.
//
// WHAT THIS FILE OWNS:
//   1. A canonical response envelope (CanonicalResponseSchema) — every field
//      is required, every field has a sentinel value for unknown states, and
//      every return site in Execute() produces one.
//   2. A closed set of standardized error codes (ErrXxx constants) that every
//      failure MUST map to — no free text, no generic errors.
//   3. A request-normalization pass (NormalizeIdentifiers) that explicitly
//      rejects mixed-case identifiers and path-traversal sequences BEFORE the
//      request is hashed — so the chain is consistent and RPSA-01/02 surface
//      as deterministic DENY/CodePathTraversal / DENY/CodeNonCanonicalCase.
//   4. An output-contract validator (ValidateResponseContract) that inspects
//      the final map and, if any required field is missing, rewrites the
//      response to a canonical DENY with CodeContractViolation. No response
//      leaves the kernel without a full schema (task.md Phase 4).
//   5. A standardized proof logger (LogAttackProof) that emits the 6 required
//      fields (attack_type, input_payload, expected, actual, error_code,
//      trace_id) to stdout and to proof_logs/v13_response_contract.jsonl
//      (task.md Phase 6).
//
// NON-GOALS:
//   - No changes to Enforce(), pdp_engine.go, capability_token.go,
//     execution_engine_sim.go, or any invariant-bearing file.
//   - No auto-lowercase / auto-clean that would silently permit attacker
//     variants — the contract REJECTS, it does not sanitize.
//
// INDUSTRY ALIGNMENT:
//   - NIST SP 800-207 (Zero Trust Architecture): every PDP decision must
//     translate into an explicit enforcement signal at the PEP boundary —
//     no implicit/empty responses.
//   - OWASP Input Validation Cheat Sheet: canonicalize before validate;
//     reject, don't sanitize; explicit path-traversal detection.
//   - Google Zanzibar / AWS IAM / AWS Cedar: every authorization response
//     carries an explicit decision + request_id + reason triple, never null.

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path"
	"path/filepath"
	"strings"
	"sync"
	"time"
	"unicode/utf8"

	"golang.org/x/text/unicode/norm"
)

// ================================================================
// CANONICAL SCHEMA CONSTANTS
// ================================================================

// SchemaVersion identifies the canonical response schema version.
// Encoded into every response so consumers can verify contract compatibility.
const SchemaVersion = "sarathi.response/v13.0"

// Verdict enum — every response MUST carry one of these.
const (
	VerdictAllow    = "ALLOW"
	VerdictDeny     = "DENY"
	VerdictEscalate = "ESCALATE"
)

// ExecutionState enum — every response MUST carry one of these.
const (
	StatePermitted    = "EXECUTION_PERMITTED"
	StateBlocked      = "EXECUTION_BLOCKED"
	StateNotAttempted = "EXECUTION_NOT_ATTEMPTED" // pre-gate reject; never reached Enforce()
	StateRpaViolation = "EXECUTION_RPA_VIOLATION" // RPA path incomplete/reordered
	StateContractErr  = "EXECUTION_CONTRACT_VIOLATION"
)

// Sentinels used where a real hash/id is impossible (e.g. pre-gate rejects
// that occur BEFORE the enforcement chain is touched).
const (
	PreGateDecisionIDPrefix = "PRE-GATE-"
	PreGateEnforcementHash  = "PRE-GATE-NO-ENFORCEMENT"
	PreGateStage            = "PRE_GATE"
	ContractDecisionIDPrefix = "CONTRACT-VIOLATION-"
	ContractEnforcementHash  = "CONTRACT-VIOLATION-NO-ENFORCEMENT"
)

// RequiredResponseFields lists every field that MUST appear at the top level
// of every response returned from Execute(). ValidateResponseContract verifies
// this list — missing a field forces an CodeContractViolation DENY.
var RequiredResponseFields = []string{
	"schema_version",
	"decision_id",
	"verdict",
	"execution_state",
	"error_code",
	"reason",
	"trace_id",
	"correlation_id",
	"enforcement_hash",
	"timestamp",
	"request",
	"enforcement",
	"execution",
	"trace_context",
	"observability",
}

// PropagationResponseFields lists the additional top-level fields surfaced by
// CanonicalFromPropagation for the v14.5 cross-system propagation layer.
// These are NOT in RequiredResponseFields because legacy (non-PDP) paths
// do not populate them — the propagation path adds them on top of the v13.0
// schema. A PDP-ingested response carries both sets; a legacy response
// carries only RequiredResponseFields.
var PropagationResponseFields = []string{
	"response_hash",
	"chain_binding_hash",
	"propagation_chain",
	"pdp_decision_id",
	"execution_id",
}

// ================================================================
// ERROR CODE DICTIONARY
// ================================================================
//
// Every failure in the kernel maps to exactly one of these codes. No free
// text, no generic errors. Each constant is also the JSON string surfaced to
// the caller. The PdpReasonToErrorCode and PostureReasonToErrorCode helpers
// below translate the existing free-text reasons from pdp_engine.go and the
// posture verifier into this dictionary, so no invariant-bearing file is
// touched.

const (
	// Success
	CodeOK = "OK"

	// Pre-gate rejections
	CodeRateLimited            = "ERR_RATE_LIMITED"
	CodePostureMissing         = "ERR_POSTURE_MISSING"
	CodePostureExpired         = "ERR_POSTURE_EXPIRED"
	CodePostureReplayed        = "ERR_POSTURE_REPLAYED"
	CodePostureUnknownIssuer   = "ERR_POSTURE_UNKNOWN_ISSUER"
	CodePostureSignatureInvalid = "ERR_POSTURE_SIGNATURE_INVALID"
	CodePostureDenied          = "ERR_POSTURE_DENIED"
	CodePostureTampered        = "ERR_POSTURE_TAMPERED"
	CodePostureGeneric         = "ERR_POSTURE_REJECTED"

	// Input validation (Phase 3: parsing hardening)
	CodeInvalidAgentID     = "ERR_INVALID_AGENT_ID"
	CodeInvalidResourceID  = "ERR_INVALID_RESOURCE_ID"
	CodePathTraversal      = "ERR_PATH_TRAVERSAL"
	CodeNonCanonicalCase   = "ERR_NON_CANONICAL_CASE"
	CodeInvalidAction      = "ERR_INVALID_ACTION"
	CodeInvalidCorrelation = "ERR_INVALID_CORRELATION_ID"
	CodeInputEncoding      = "ERR_INPUT_INVALID_ENCODING"
	CodeInputTooLong       = "ERR_INPUT_TOO_LONG"

	// PDP path (mapped from pdp_engine.go reasons)
	CodePolicyVersionMismatch = "ERR_POLICY_VERSION_MISMATCH"
	CodeAgentNotFound         = "ERR_AGENT_NOT_FOUND"
	CodeAgentSuspended        = "ERR_AGENT_SUSPENDED"
	CodeAgentRevoked          = "ERR_AGENT_REVOKED"
	CodeAgentTerminated       = "ERR_AGENT_TERMINATED"
	CodeResourceNotFound      = "ERR_RESOURCE_NOT_FOUND"
	CodeNoMatchingRule        = "ERR_NO_MATCHING_RULE"
	CodeNoAllowRule           = "ERR_NO_ALLOW_RULE"
	CodeExplicitDeny          = "ERR_EXPLICIT_DENY"
	CodeClassificationCeiling = "ERR_CLASSIFICATION_CEILING_EXCEEDED"
	CodeClassificationParse   = "ERR_CLASSIFICATION_PARSE_FAILURE"
	CodePdpHashMismatch       = "ERR_PDP_HASH_MISMATCH"
	CodePdpMarshalFailure     = "ERR_PDP_MARSHAL_FAILURE"
	CodeValidationFailed      = "ERR_VALIDATION_FAILED"
	CodePdpGenericDeny        = "ERR_PDP_DENY"

	// Post-enforcement / execution
	CodeRpaIntegrityViolation = "ERR_RPA_INTEGRITY_VIOLATION"
	CodeNoToken               = "ERR_NO_TOKEN"
	CodeTokenReplay           = "ERR_TOKEN_REPLAY"
	CodeTokenExpired          = "ERR_TOKEN_EXPIRED"
	CodeTokenSignatureInvalid = "ERR_TOKEN_SIGNATURE_INVALID"
	CodeExecutionBlocked      = "ERR_EXECUTION_BLOCKED"

	// Contract violations (fail-closed catch-all)
	CodeContractViolation = "ERR_CONTRACT_VIOLATION"
	CodeInternal          = "ERR_INTERNAL"
	CodeEscalated         = "ERR_ESCALATED"

	// v14.4: Bridge-level error codes (Gap G normalization)
	CodeBridgeInactive       = "ERR_BRIDGE_INACTIVE"
	CodeBridgeNotStarted     = "ERR_BRIDGE_NOT_STARTED"
	CodeCallerNotRegistered  = "ERR_CALLER_NOT_REGISTERED"
	CodeCallerInactive       = "ERR_CALLER_INACTIVE"
	CodePassportUnavailable  = "ERR_PASSPORT_UNAVAILABLE"
	CodePassportInvalid      = "ERR_PASSPORT_INVALID"
	CodeServiceNotReady      = "ERR_SERVICE_NOT_READY"

	// v14.5: Cross-System Deterministic Propagation Layer error codes.
	// These fire when the byte-equality chain from Sarathi → Core/InsightFlow/Bucket
	// is broken at any hop. Every one halts propagation immediately.
	CodeDeterminismViolation    = "ERR_DETERMINISM_VIOLATION"
	CodePropagationByteMismatch = "ERR_PROPAGATION_BYTE_MISMATCH"
	CodePDPDecisionInvalid      = "ERR_PDP_DECISION_INVALID"
	CodeResponseHashMismatch    = "ERR_RESPONSE_HASH_MISMATCH"
	CodePropagationChainBroken  = "ERR_PROPAGATION_CHAIN_BROKEN"
	CodeIntelligenceLayerBreach = "ERR_INTELLIGENCE_LAYER_BREACH"

	// v14.6: Global Determinism Validation + Distributed Enforcement Proof.
	// Fire when distributed-determinism invariants break outside the in-process
	// chain: transport-layer mutation (CodeTransportIntegrityViolation), a
	// Bucket read-back whose stored bytes diverge from Sarathi's sealed output
	// (CodeBucketReadbackMismatch), or cross-node byte-drift when the same
	// fixture produces different envelopes on different Sarathi instances
	// (CodeMultiNodeDrift). Each is a DETERMINISM VIOLATION at the system
	// boundary and maps one-to-one with a success criterion in task.md v14.6.
	CodeTransportIntegrityViolation = "ERR_TRANSPORT_INTEGRITY_VIOLATION"
	CodeBucketReadbackMismatch      = "ERR_BUCKET_READBACK_MISMATCH"
	CodeMultiNodeDrift              = "ERR_MULTI_NODE_DRIFT"

	// v14.7: Live Integration Closure error codes.
	// Fire when the live downstream integration (real BHIV Core, InsightFlow,
	// Bucket peer processes) fails the post-propagation gate. Each maps 1:1
	// to a specific failure mode of the closed-loop verification contract
	// documented in KB_10_LIVE_INTEGRATION_v14_7.md.
	CodeDownstreamSchemaMismatch  = "ERR_DOWNSTREAM_SCHEMA_MISMATCH"
	CodeDownstreamPersistFailed   = "ERR_DOWNSTREAM_PERSIST_FAILED"
	CodeDownstreamAckTimeout      = "ERR_DOWNSTREAM_ACK_TIMEOUT"
	CodeDownstreamReceiptInvalid  = "ERR_DOWNSTREAM_RECEIPT_INVALID"
	CodeLiveIntegrationGateFailed = "ERR_LIVE_INTEGRATION_GATE_FAILED"

	// v14.8: Sovereign Authority Closure error codes.
	// Fire when parallel-execution comparator detects silent divergence
	// between Sarathi and the legacy enforcer, when the legacy shim is
	// unreachable, or when cross-machine network / clock-skew health
	// drops below the operator-configured tolerance. Documented in
	// KB_11_SOVEREIGN_AUTHORITY_v14_8.md.
	CodeShadowDivergence               = "ERR_SHADOW_DIVERGENCE"
	CodeLegacyShimUnavailable          = "ERR_LEGACY_SHIM_UNAVAILABLE"
	CodeCrossMachineClockSkewExcessive = "ERR_CROSS_MACHINE_CLOCK_SKEW_EXCESSIVE"
	CodeCrossMachineUnreachable        = "ERR_CROSS_MACHINE_UNREACHABLE"

	// v15.0: Sovereign Identity Closure error codes.
	// Fire when the inbound HTTP boundary cannot prove a POST originated from
	// a registered evaluator. These codes are emitted BEFORE the existing
	// API-key check when SARATHI_INBOUND_AUTH != off. Boot-gate codes fire
	// during service startup, prior to binding the listener, when the
	// operator sets SARATHI_ENV=production with an unsafe configuration.
	// Full spec: KB_12_INBOUND_IDENTITY_v15_0.md.
	CodeInboundSignatureMissing     = "ERR_INBOUND_SIGNATURE_MISSING"
	CodeInboundSignatureInvalid     = "ERR_INBOUND_SIGNATURE_INVALID"
	CodeInboundTimestampSkewed      = "ERR_INBOUND_TIMESTAMP_SKEWED"
	CodeInboundNonceReplay          = "ERR_INBOUND_NONCE_REPLAY"
	CodeEvaluatorNotRegistered      = "ERR_EVALUATOR_NOT_REGISTERED"
	CodeEvaluatorSuspended          = "ERR_EVALUATOR_SUSPENDED"
	CodeEvaluatorRevoked            = "ERR_EVALUATOR_REVOKED"
	CodeTrustRegistryEmpty          = "ERR_TRUST_REGISTRY_EMPTY"
	CodeSimulationHandlerInProd     = "ERR_SIMULATION_HANDLER_IN_PRODUCTION"
	CodeInboundAuthOffInProduction  = "ERR_INBOUND_AUTH_OFF_IN_PRODUCTION"

	// v15.1: Network Surface Closure error codes.
	// Fire when the HTTP /v1/ingest-decision boundary rejects an external PDP
	// decision, or when the production boot-time pre-flight on
	// SARATHI_TRUST_REMOTE_URL fails (insecure scheme or unreachable host).
	// Full spec: KB_13_NETWORK_SURFACE_CLOSURE_v15_1.md.
	CodeIngestDecisionInvalid     = "ERR_INGEST_DECISION_INVALID"
	CodeTrustRemoteURLInsecure    = "ERR_TRUST_REMOTE_URL_INSECURE"
	CodeTrustRemoteURLUnreachable = "ERR_TRUST_REMOTE_URL_UNREACHABLE"

	// v15.6: Bridge-facing JWT Authority error codes.
	// Surfaced by the failure-demo "sarathi_unavailable_for_bridge" scenario
	// when a verifier (mock Bridge) cannot refresh JWKS during a Sarathi
	// outage AND its cached set does not contain the kid of the token it
	// just received. The "fail-closed" outcome of this scenario is the
	// proof point: an external verifier with NO local mint capability
	// rejects the request rather than synthesizing a fallback.
	// Full spec: KB_16_JWT_AUTHORITY_v15_6.md.
	CodeAuthorityUnreachableFailClosed = "ERR_AUTHORITY_UNREACHABLE_FAIL_CLOSED"
	CodeJWTAuthorityEphemeralInBridgeMode = "ERR_JWT_AUTHORITY_EPHEMERAL_IN_BRIDGE_MODE"
	CodeJWTAuthorityKeyMissing            = "ERR_JWT_AUTHORITY_KEY_MISSING"
	CodeJWTAuthorityIssuerInsecure        = "ERR_JWT_AUTHORITY_ISSUER_INSECURE"
	CodeJWTAuthorityKidMismatch           = "ERR_JWT_AUTHORITY_KID_MISMATCH"
	CodeJWTIntrospectionKeyWeak           = "ERR_JWT_INTROSPECTION_KEY_WEAK"
	CodeJWTAuthorityTLSRequired           = "ERR_JWT_AUTHORITY_TLS_REQUIRED"
)

// ================================================================
// IDENTIFIER NORMALIZATION (Phase 3: Parsing Hardening)
// ================================================================

// MaxNormalizedFieldLength caps agent/resource/correlation IDs.
// Matches execution_request.go MaxFieldLength = 256.
const MaxNormalizedFieldLength = 256

// NormalizeIdentifiers applies OWASP-aligned input hardening to the three
// user-supplied identifiers BEFORE the request is hashed. The function:
//
//  1. Applies Unicode NFKC normalization so visually-confusable code points
//     collapse to their canonical form (OWASP Input Validation Cheat Sheet).
//  2. REJECTS mixed-case agent/resource identifiers with CodeNonCanonicalCase.
//     The registry uses lowercase keys (see registry_interface.go:40-84);
//     silently lowercasing attacker input would let probes like "Gov-Agent-001"
//     match a real agent. OWASP explicitly recommends reject, don't sanitize.
//  3. REJECTS path-traversal sequences in resource_id with CodePathTraversal.
//     Resource IDs must be flat tokens (matches registry_interface.go, which
//     looks up resources as flat map keys). Any "..", "/", "\", NUL, or
//     path.Clean-divergent input is rejected.
//  4. Enforces length and UTF-8 validity checks that mirror the existing
//     validation in execution_request.go, but surfaces them as deterministic
//     error codes instead of free text.
//
// On success returns the (normalized) identifiers and an empty error code.
// On failure returns ("", "", "", errCode) where errCode is one of the
// Err* constants defined above.
//
// Empty-string inputs are passed through unchanged with an empty error code
// so the existing execution_request.go validation still fires and produces
// its standard MISSING_* errors, preserving legacy behavior for the
// enforcement_adapter_main.go partial-input regression tests.
func NormalizeIdentifiers(agentID, resourceID, action string) (string, string, string, string) {
	// Pass-through for fully empty inputs — existing validation handles them.
	if agentID == "" && resourceID == "" && action == "" {
		return agentID, resourceID, action, ""
	}

	// ---- agent_id ----
	normAgent, code := normalizeIdentifier("agent_id", agentID, false)
	if code != "" {
		return "", "", "", code
	}

	// ---- resource_id (path-traversal sensitive) ----
	normResource, code := normalizeIdentifier("resource_id", resourceID, true)
	if code != "" {
		return "", "", "", code
	}

	// ---- action ----
	// Actions are drawn from a small fixed vocabulary (read/write/execute/delete).
	// We do NOT reject mixed case here: normalize to lowercase so "Read" maps to
	// "read" and the existing execution_request.go validActions set still fires.
	// Action spoofing is caught by the existing validation, so this is safe.
	normAction := strings.ToLower(strings.TrimSpace(action))
	if action != "" && !utf8.ValidString(action) {
		return "", "", "", CodeInputEncoding
	}

	return normAgent, normResource, normAction, ""
}

// normalizeIdentifier implements the per-field rules. If pathSensitive is
// true, the field is also checked for traversal sequences.
func normalizeIdentifier(fieldName, value string, pathSensitive bool) (string, string) {
	if value == "" {
		// Let existing validation handle empty → MISSING_* errors.
		return value, ""
	}

	// UTF-8 validity first — pre-decode check per OWASP.
	if !utf8.ValidString(value) {
		return "", CodeInputEncoding
	}

	// NFKC normalization (OWASP: Normalization Form KC is the recommended
	// form for input validation purposes).
	normalized := norm.NFKC.String(value)

	if len(normalized) > MaxNormalizedFieldLength {
		return "", CodeInputTooLong
	}

	// Reject control characters including NUL.
	for _, r := range normalized {
		if r < 0x20 || r == 0x7f {
			if fieldName == "resource_id" {
				return "", CodePathTraversal
			}
			return "", CodeInvalidAgentID
		}
	}

	// Case canonicalization: REJECT, don't silently lowercase. The registry
	// uses lowercase keys and attacker probes with mixed case must DENY with
	// a distinct error code so operators can see the probe in logs.
	if strings.ToLower(normalized) != normalized {
		return "", CodeNonCanonicalCase
	}

	// Path-traversal detection (resource_id only).
	if pathSensitive {
		if code := detectPathTraversal(normalized); code != "" {
			return "", code
		}
	}

	return normalized, ""
}

// detectPathTraversal rejects any value that is not a flat token. Flat means:
// no slashes, no backslashes, no ".." segments, no leading ".", and
// path.Clean is an identity (i.e. the value is already in canonical form).
// This is deliberately stricter than path.Clean — attackers often rely on
// inputs that pass naive Clean checks (e.g. "a/./b" becomes "a/b").
func detectPathTraversal(value string) string {
	if strings.ContainsAny(value, "/\\") {
		return CodePathTraversal
	}
	if strings.Contains(value, "..") {
		return CodePathTraversal
	}
	if strings.HasPrefix(value, ".") {
		return CodePathTraversal
	}
	// path.Clean idempotence — any transformation means the input was
	// non-canonical.
	if path.Clean(value) != value {
		return CodePathTraversal
	}
	// filepath.Clean for Windows-style escapes (backslashes already caught
	// above, but defensive).
	if filepath.ToSlash(filepath.Clean(value)) != value {
		return CodePathTraversal
	}
	return ""
}

// ================================================================
// PDP REASON -> ERROR CODE MAPPING
// ================================================================

// PdpReasonToErrorCode translates the existing pdp_engine.go free-text
// reasons (INVALID_AGENT_ID, AGENT_NOT_FOUND, EXPLICIT_DENY, …) into the
// canonical ErrXxx dictionary. This keeps pdp_engine.go untouched while
// giving every response a stable error_code field.
func PdpReasonToErrorCode(reason string) string {
	// Exact-match table for known codes.
	switch reason {
	case "", "PDP_DECISION_ACCEPTED":
		return CodeOK
	case "INVALID_AGENT_ID":
		return CodeInvalidAgentID
	case "INVALID_RESOURCE_ID":
		return CodeInvalidResourceID
	case "INVALID_ACTION":
		return CodeInvalidAction
	case "AGENT_NOT_FOUND":
		return CodeAgentNotFound
	case "RESOURCE_NOT_FOUND":
		return CodeResourceNotFound
	case "NO_MATCHING_RULE":
		return CodeNoMatchingRule
	case "NO_ALLOW_RULE":
		return CodeNoAllowRule
	case "EXPLICIT_DENY":
		return CodeExplicitDeny
	case "AGENT_CLASSIFICATION_PARSE_FAILURE",
		"RESOURCE_CLASSIFICATION_PARSE_FAILURE":
		return CodeClassificationParse
	}

	// Prefix-based matches for reasons that carry data.
	switch {
	case strings.HasPrefix(reason, "AGENT_SUSPENDED"):
		return CodeAgentSuspended
	case strings.HasPrefix(reason, "AGENT_REVOKED"):
		return CodeAgentRevoked
	case strings.HasPrefix(reason, "AGENT_TERMINATED"):
		return CodeAgentTerminated
	case strings.HasPrefix(reason, "AGENT_"):
		// Any other AGENT_<STATUS> — treat as suspended-equivalent.
		return CodeAgentSuspended
	case strings.HasPrefix(reason, "VALIDATION_FAILED"):
		return CodeValidationFailed
	case strings.HasPrefix(reason, "POLICY_VERSION_MISMATCH"):
		return CodePolicyVersionMismatch
	case strings.HasPrefix(reason, "REQUEST_HASH_MISMATCH"),
		strings.HasPrefix(reason, "REQUEST_MARSHAL_ERROR"):
		return CodePdpHashMismatch
	case strings.HasPrefix(reason, "CLASSIFICATION_CEILING"):
		return CodeClassificationCeiling
	}

	// Fail-closed: unknown reasons land on the generic deny code.
	return CodePdpGenericDeny
}

// PostureReasonToErrorCode maps the posture verifier free-text reasons
// (declared in enforcement_adapter.go / PostureVerifier.Admit) to the
// canonical dictionary.
func PostureReasonToErrorCode(reason string) string {
	switch {
	case reason == "":
		return CodePostureGeneric
	case strings.Contains(reason, "POSTURE_SIGNAL_EXPIRED"):
		return CodePostureExpired
	case strings.Contains(reason, "POSTURE_SIGNAL_REPLAYED"):
		return CodePostureReplayed
	case strings.Contains(reason, "POSTURE_ISSUER_UNKNOWN"):
		return CodePostureUnknownIssuer
	case strings.Contains(reason, "POSTURE_SIGNAL_INVALID"):
		return CodePostureSignatureInvalid
	case strings.Contains(reason, "AGENT_POSTURE_DENIED"):
		return CodePostureDenied
	case strings.Contains(reason, "POSTURE_SIGNAL_MISSING"),
		strings.Contains(reason, "missing"):
		return CodePostureMissing
	case strings.Contains(reason, "TAMPER") || strings.Contains(reason, "tamper"):
		return CodePostureTampered
	}
	return CodePostureGeneric
}

// BlockReasonToErrorCode maps the capability_token.go BlockXxx constants
// (used in ExecutionResult.BlockReason) to the canonical dictionary.
func BlockReasonToErrorCode(reason string) string {
	switch {
	case reason == "":
		return CodeOK
	case strings.HasPrefix(reason, "NO_TOKEN"):
		return CodeNoToken
	case strings.HasPrefix(reason, "INVALID_SIGNATURE"):
		return CodeTokenSignatureInvalid
	case strings.HasPrefix(reason, "HASH_MISMATCH"):
		return CodeTokenSignatureInvalid
	case strings.HasPrefix(reason, "TOKEN_EXPIRED"):
		return CodeTokenExpired
	case strings.HasPrefix(reason, "TOKEN_ALREADY_USED"),
		strings.HasPrefix(reason, "TOKEN_REPLAY"):
		return CodeTokenReplay
	case strings.HasPrefix(reason, "ENFORCEMENT_HASH_NOT_IN_CHAIN"):
		return CodeRpaIntegrityViolation
	}
	return CodeExecutionBlocked
}

// BridgeReasonToErrorCode maps bridge-level block reasons to standardized
// error codes from the v14.4 error dictionary. This closes Gap G: all error
// paths now use consistent error codes instead of free-text strings.
func BridgeReasonToErrorCode(reason string) string {
	switch {
	case reason == "":
		return CodeOK
	case strings.Contains(reason, "BRIDGE_INACTIVE"):
		return CodeBridgeInactive
	case strings.Contains(reason, "BRIDGE_NOT_STARTED"):
		return CodeBridgeNotStarted
	case strings.Contains(reason, "CALLER_NOT_REGISTERED"):
		return CodeCallerNotRegistered
	case strings.Contains(reason, "CALLER_INACTIVE"), strings.Contains(reason, "CALLER_SUSPENDED"):
		return CodeCallerInactive
	case strings.Contains(reason, "PASSPORT_AUTHORITY_UNAVAILABLE"):
		return CodePassportUnavailable
	case strings.Contains(reason, "PASSPORT_INVALID"), strings.Contains(reason, "passport"):
		return CodePassportInvalid
	case strings.Contains(reason, "SERVICE_NOT_READY"):
		return CodeServiceNotReady
	case strings.Contains(reason, "RATE_LIMIT"):
		return CodeRateLimited
	case strings.Contains(reason, "PERMISSION_DENIED"):
		return CodeExplicitDeny
	case strings.Contains(reason, "VALIDATION"):
		return CodeValidationFailed
	}
	return CodeExecutionBlocked
}

// ================================================================
// DETERMINISTIC IDENTIFIERS
// ================================================================

// DeterministicDecisionID produces a stable decision_id for return sites
// that occur BEFORE the PDP issues one (pre-gate rejects, contract
// violations). The id is derived from SHA-256(stage|correlation_id) so
// repeated probes with the same correlation_id produce the same id, which
// lets operators de-dupe attacker retries.
func DeterministicDecisionID(prefix, stage, correlationID string) string {
	h := sha256.Sum256([]byte(stage + "|" + correlationID))
	return prefix + hex.EncodeToString(h[:6])
}

// ================================================================
// CANONICAL RESPONSE BUILDERS
// ================================================================

// canonicalTimestamp is the single format used for the top-level timestamp
// field across every response. Matches the format already used in
// execution_response.go for consistency.
func canonicalTimestamp() string {
	return time.Now().UTC().Format("2006-01-02T15:04:05.000000Z")
}

// emptyEnforcementEnvelope is the sentinel map used when a response is
// produced BEFORE enforcement could be evaluated (pre-gate reject,
// validation-level reject). Every field is explicit — no nils — so any
// downstream reader gets a consistent shape.
func emptyEnforcementEnvelope(decisionID, verdict, errCode, reason, enfHash, correlationID string) map[string]interface{} {
	return map[string]interface{}{
		"correlation_id":       correlationID,
		"verdict":              verdict,
		"decision_id":          decisionID,
		"policy_version":       "",
		"policy_hash":          "",
		"request_hash":         "",
		"pdp_decision_hash":    "NO_PDP_EVALUATION",
		"enforcement_hash":     enfHash,
		"enforcement_nonce":    "",
		"enforcement_stage":    PreGateStage,
		"enforcement_reason":   reason,
		"pdp_reason":           reason,
		"determining_rules":    []string{},
		"truth_classification": "UNKNOWN",
		"agent_role":           "UNKNOWN",
		"resource_type":        "UNKNOWN",
		"stage_reached":        0,
		"enforced_at":          canonicalTimestamp(),
		"valid_until":          canonicalTimestamp(),
		"registry_version":     int64(0),
		"rpa_hash":             "",
		"obligations":          []string{},
		"has_capability_token": false,
		"error_code":           errCode,
	}
}

// emptyExecutionEnvelope is the sentinel execution map used when the request
// never reaches ExecutionEngine (pre-gate reject, contract violation).
func emptyExecutionEnvelope(state, errCode, reason, correlationID string) map[string]interface{} {
	return map[string]interface{}{
		"executed":            false,
		"execution_state":     state,
		"execution_sequence":  0,
		"execution_hash":      "",
		"prev_execution_hash": "",
		"correlation_id":      correlationID,
		"decision_id":         "",
		"enforcement_hash":    "",
		"timestamp":           canonicalTimestamp(),
		"block_reason":        fmt.Sprintf("%s: %s", errCode, reason),
		"error_code":          errCode,
	}
}

// emptyObservabilityEnvelope is the sentinel observability map used at
// every return site so consumers can always read trace shape info.
func emptyObservabilityEnvelope(rpaEnforcement, detail string) map[string]interface{} {
	return map[string]interface{}{
		"pipeline_path_hash":   "",
		"pipeline_path_stages": []string{},
		"pipeline_duration_ns": int64(0),
		"rpa_enforcement":      rpaEnforcement,
		"rpa_detail":           detail,
	}
}

// traceContextMap safely renders a *TraceContext into a map without panicking
// if the pointer is nil.
func traceContextMap(tc *TraceContext) map[string]interface{} {
	if tc == nil {
		return map[string]interface{}{
			"trace_id":    "",
			"span_id":     "",
			"parent_span": "",
			"trace_flags": byte(0),
			"sampled":     false,
		}
	}
	return map[string]interface{}{
		"trace_id":    tc.TraceID,
		"span_id":     tc.SpanID,
		"parent_span": tc.ParentSpan,
		"trace_flags": tc.TraceFlags,
		"sampled":     tc.Sampled,
	}
}

// requestMap safely renders an *ExecutionRequest into a map.
func requestMap(req *ExecutionRequest) map[string]interface{} {
	if req == nil {
		return map[string]interface{}{
			"agent_id":       "",
			"resource_id":    "",
			"action":         "",
			"correlation_id": "",
			"policy_version": "",
			"request_hash":   "",
			"is_valid":       false,
		}
	}
	return req.ToMap()
}

// rawRequestMap builds a map for the ExecutionRequest parameters when the
// request object itself could not be constructed (e.g. normalization rejected
// the input before NewExecutionRequest was called).
func rawRequestMap(agentID, resourceID, action, correlationID, policyVersion string) map[string]interface{} {
	return map[string]interface{}{
		"agent_id":       agentID,
		"resource_id":    resourceID,
		"action":         action,
		"correlation_id": correlationID,
		"policy_version": policyVersion,
		"request_hash":   "",
		"is_valid":       false,
	}
}

// CanonicalDenyFromValidation constructs a canonical DENY response for the
// normalization-layer rejection path. Called from Execute() BEFORE the
// ExecutionRequest is constructed, so it takes the raw parameters.
func CanonicalDenyFromValidation(
	errCode, agentID, resourceID, action, correlationID, policyVersion string,
	traceCtx *TraceContext,
) map[string]interface{} {
	reason := fmt.Sprintf("INPUT_NORMALIZATION_REJECTED: %s", errCode)
	traceID := ""
	if traceCtx != nil {
		traceID = traceCtx.TraceID
	}
	decisionID := DeterministicDecisionID(PreGateDecisionIDPrefix, "INPUT_NORMALIZATION", correlationID)

	resp := map[string]interface{}{
		"schema_version":     SchemaVersion,
		"decision_id":        decisionID,
		"verdict":            VerdictDeny,
		"execution_state":    StateNotAttempted,
		"error_code":         errCode,
		"reason":             reason,
		"trace_id":           traceID,
		"correlation_id":     correlationID,
		"enforcement_hash":   PreGateEnforcementHash,
		"timestamp":          canonicalTimestamp(),
		"enforcement_token":  "",
		"execution_id":       "",
		"request":            rawRequestMap(agentID, resourceID, action, correlationID, policyVersion),
		"enforcement":        emptyEnforcementEnvelope(decisionID, VerdictDeny, errCode, reason, PreGateEnforcementHash, correlationID),
		"execution":          emptyExecutionEnvelope(StateNotAttempted, errCode, reason, correlationID),
		"trace_context":      traceContextMap(traceCtx),
		"observability":      emptyObservabilityEnvelope("NOT_ATTEMPTED", reason),
		"pre_gate": map[string]interface{}{
			"stage":    "INPUT_NORMALIZATION",
			"admitted": false,
			"reason":   reason,
		},
	}
	return resp
}

// CanonicalDenyFromPreGate constructs a canonical DENY response for pre-gate
// rejections (rate limit, posture verification). Called from Execute() with
// the already-constructed ExecutionRequest.
func CanonicalDenyFromPreGate(
	stage, reason, errCode string,
	req *ExecutionRequest,
	traceCtx *TraceContext,
) map[string]interface{} {
	traceID := ""
	if traceCtx != nil {
		traceID = traceCtx.TraceID
	}
	correlationID := ""
	if req != nil {
		correlationID = req.CorrelationID()
	}
	decisionID := DeterministicDecisionID(PreGateDecisionIDPrefix, stage, correlationID)

	resp := map[string]interface{}{
		"schema_version":    SchemaVersion,
		"decision_id":       decisionID,
		"verdict":           VerdictDeny,
		"execution_state":   StateNotAttempted,
		"error_code":        errCode,
		"reason":            reason,
		"trace_id":          traceID,
		"correlation_id":    correlationID,
		"enforcement_hash":  PreGateEnforcementHash,
		"timestamp":         canonicalTimestamp(),
		"enforcement_token": "",
		"execution_id":      "",
		"request":           requestMap(req),
		"enforcement":       emptyEnforcementEnvelope(decisionID, VerdictDeny, errCode, reason, PreGateEnforcementHash, correlationID),
		"execution":         emptyExecutionEnvelope(StateNotAttempted, errCode, reason, correlationID),
		"trace_context":     traceContextMap(traceCtx),
		"observability":     emptyObservabilityEnvelope("NOT_ATTEMPTED", reason),
		"pre_gate": map[string]interface{}{
			"stage":    stage,
			"admitted": false,
			"reason":   reason,
		},
	}
	return resp
}

// CanonicalFromEnforcement constructs a canonical response from a real
// ExecutionResponse + ExecutionResult produced by Enforce() +
// ExecutionEngine. Used for the happy path AND for ALLOW-denied paths
// where Enforce() returned DENY for policy reasons.
func CanonicalFromEnforcement(
	enfResp *ExecutionResponse,
	execResult *ExecutionResult,
	req *ExecutionRequest,
	traceCtx *TraceContext,
	pathHash string,
	stages []string,
	durationNs int64,
	rpaEnforcement string,
) map[string]interface{} {
	enfMap := map[string]interface{}{}
	if enfResp != nil {
		enfMap = enfResp.ToMap()
	}

	execMap := map[string]interface{}{}
	if execResult != nil {
		execMap = execResult.ToMap()
	}

	// Derive canonical top-level values from the nested envelopes.
	verdict := VerdictDeny
	decisionID := ""
	correlationID := ""
	enfHash := ""
	reason := ""
	if enfResp != nil {
		verdict = enfResp.Verdict()
		if verdict == "" {
			verdict = VerdictDeny
		}
		decisionID = enfResp.DecisionID()
		correlationID = enfResp.CorrelationID()
		enfHash = enfResp.EnforcementHash()
		reason = enfResp.EnforcementReason()
		if reason == "" {
			reason = enfResp.PDPReason()
		}
	}
	if correlationID == "" && req != nil {
		correlationID = req.CorrelationID()
	}

	// Derive execution_state from the ExecutionResult when present;
	// otherwise synthesize from the verdict. ALLOW + executed == PERMITTED,
	// every other combination → BLOCKED.
	execState := StateBlocked
	if execResult != nil {
		execState = execResult.Status
		if execState == "" {
			execState = StateBlocked
		}
	} else if verdict == VerdictAllow {
		execState = StatePermitted
	}

	// Derive error_code: OK for a successful ALLOW+PERMITTED, otherwise map
	// from the most-specific failure signal available.
	errCode := CodeOK
	switch {
	case verdict == VerdictEscalate:
		errCode = CodeEscalated
	case execResult != nil && execResult.BlockReason != "":
		errCode = BlockReasonToErrorCode(execResult.BlockReason)
	case verdict == VerdictDeny && enfResp != nil:
		pdpReason := enfResp.PDPReason()
		if pdpReason == "" {
			pdpReason = enfResp.EnforcementReason()
		}
		errCode = PdpReasonToErrorCode(pdpReason)
		if errCode == CodeOK {
			errCode = CodePdpGenericDeny
		}
	case verdict == VerdictAllow && execState != StatePermitted:
		errCode = CodeExecutionBlocked
	}

	// If reason is still empty, synthesize from error_code so the "reason"
	// field is never empty (contract requirement).
	if reason == "" {
		if errCode == CodeOK {
			reason = "ALLOW"
		} else {
			reason = errCode
		}
	}

	if decisionID == "" {
		decisionID = DeterministicDecisionID(PreGateDecisionIDPrefix, "ENFORCEMENT_NO_DECISION_ID", correlationID)
	}
	if enfHash == "" {
		enfHash = PreGateEnforcementHash
	}

	traceID := ""
	if traceCtx != nil {
		traceID = traceCtx.TraceID
	}

	// Inject error_code into nested envelopes for consumers that read
	// nested fields (integration_gate_tests.go uses this pattern).
	enfMap["error_code"] = errCode
	execMap["error_code"] = errCode
	if _, ok := execMap["execution_state"]; !ok {
		execMap["execution_state"] = execState
	}

	// v14.4: Derive enforcement_token and execution_id from execution result.
	enfToken := ""
	execID := ""
	if execResult != nil {
		enfToken = execResult.TokenID
		if execResult.ExecutionHash != "" {
			execID = fmt.Sprintf("EXEC-%d-%s", execResult.ExecutionSequence, execResult.ExecutionHash[:min(8, len(execResult.ExecutionHash))])
		}
	}

	resp := map[string]interface{}{
		"schema_version":    SchemaVersion,
		"decision_id":       decisionID,
		"verdict":           verdict,
		"execution_state":   execState,
		"error_code":        errCode,
		"reason":            reason,
		"trace_id":          traceID,
		"correlation_id":    correlationID,
		"enforcement_hash":  enfHash,
		"timestamp":         canonicalTimestamp(),
		"enforcement_token": enfToken,
		"execution_id":      execID,
		"request":           requestMap(req),
		"enforcement":       enfMap,
		"execution":         execMap,
		"trace_context":     traceContextMap(traceCtx),
		"observability": map[string]interface{}{
			"pipeline_path_hash":   pathHash,
			"pipeline_path_stages": stages,
			"pipeline_duration_ns": durationNs,
			"rpa_enforcement":      rpaEnforcement,
		},
	}
	return resp
}

// CanonicalFromPropagation builds a canonical response map tailored for the
// v14.5 Cross-System Deterministic Propagation Layer. It is the response
// payload that rides inside PropagationEnvelope.canonicalResponseBytes
// (sealed at envelope creation) and is propagated byte-for-byte to BHIV Core,
// InsightFlow, and Bucket.
//
// Compared to CanonicalFromEnforcement it adds the five top-level fields
// PropagationResponseFields lists:
//
//	response_hash         — Sha256Hex(canonical bytes of THIS map before seal).
//	                         Set to "" by this builder; the envelope seal path
//	                         overwrites it with the actual hash after it has
//	                         frozen the bytes. This preserves idempotent
//	                         re-serialization (the map → bytes pass is
//	                         deterministic because the hash is not self-referential).
//	chain_binding_hash    — Sha256Hex of canonical join of propagation_chain.
//	chain                 — ordered [decision_hash, core_hash, enforcement_hash,
//	                         response_hash_placeholder]. The last slot is filled
//	                         after canonical bytes are produced.
//	pdp_decision_id       — the upstream PDP's decision_id (authoritative).
//	execution_id          — Raj's downstream execution identifier.
//
// The function is a pure composer. It performs NO policy evaluation, NO
// semantic derivation beyond what the ExternalDecision/ExternalEnforcementResult
// already contain. The verdict comes from d.Verdict, the enforcement_hash
// from r.EnforcementHash — untouched.
//
// TAG: no-policy-logic
func CanonicalFromPropagation(
	d *ExternalDecision,
	r *ExternalEnforcementResult,
	executionID string,
	traceCtx *TraceContext,
	correlationID string,
	durationNs int64,
) map[string]interface{} {
	if d == nil || r == nil {
		return CanonicalInternalError(
			"canonical_from_propagation: nil inputs",
			"", "", "", correlationID, traceCtx,
		)
	}

	verdict := string(d.Verdict)
	if verdict == "" {
		verdict = VerdictDeny
	}

	// execution_state follows strict verdict mapping — no semantic
	// reinterpretation. ALLOW ⇒ PERMITTED, any other ⇒ BLOCKED.
	execState := StateBlocked
	errCode := CodePdpGenericDeny
	reason := r.BlockReason
	switch verdict {
	case VerdictAllow:
		execState = StatePermitted
		errCode = CodeOK
		if reason == "" {
			reason = "ALLOW"
		}
	case VerdictEscalate:
		execState = StateBlocked
		errCode = CodeEscalated
		if reason == "" {
			reason = "ESCALATED"
		}
	default:
		// DENY (default): reason stays as r.BlockReason if present.
		if reason == "" {
			reason = d.Reason
		}
		if reason == "" {
			reason = CodePdpGenericDeny
		}
	}

	traceID := ""
	spanID := ""
	if traceCtx != nil {
		traceID = traceCtx.TraceID
		spanID = traceCtx.SpanID
	}

	// propagation_chain with placeholder for response_hash (filled after seal).
	// Order is fixed — NEVER resorted.
	propChain := []interface{}{
		d.DecisionHash,
		d.DecisionCoreHash,
		r.EnforcementHash,
		"", // response_hash placeholder — envelope seal fills this
	}

	// request_block mirrors CanonicalFromEnforcement but is built from
	// the ExternalDecision fields (no ExecutionRequest available on this path).
	reqMap := map[string]interface{}{
		"agent_id":       d.AgentID,
		"resource_id":    d.ResourceID,
		"action":         d.Action,
		"correlation_id": correlationID,
	}

	enfMap := map[string]interface{}{
		"decision_id":          d.DecisionID,
		"verdict":              verdict,
		"enforced":             r.Enforced,
		"enforcement_hash":     r.EnforcementHash,
		"decision_hash":        d.DecisionHash,
		"decision_core_hash":   d.DecisionCoreHash,
		"request_binding_hash": r.RequestBindingHash,
		"correlation_id":       correlationID,
		"enforced_at":          r.EnforcedAt,
		"mode":                 r.Mode,
		"reason":               reason,
		"error_code":           errCode,
	}

	execMap := map[string]interface{}{
		"execution_state":  execState,
		"execution_id":     executionID,
		"enforcement_hash": r.EnforcementHash,
		"decision_id":      d.DecisionID,
		"correlation_id":   correlationID,
		"error_code":       errCode,
		"timestamp":        canonicalTimestamp(),
	}

	tokenID := ""
	if r.Token != nil {
		tokenID = r.Token.TokenID()
	}

	resp := map[string]interface{}{
		// v13.0 required fields
		"schema_version":    SchemaVersion,
		"decision_id":       d.DecisionID,
		"verdict":           verdict,
		"execution_state":   execState,
		"error_code":        errCode,
		"reason":            reason,
		"trace_id":          traceID,
		"correlation_id":    correlationID,
		"enforcement_hash":  r.EnforcementHash,
		"timestamp":         canonicalTimestamp(),
		"enforcement_token": tokenID,
		"execution_id":      executionID,
		"request":           reqMap,
		"enforcement":       enfMap,
		"execution":         execMap,
		"trace_context": map[string]interface{}{
			"trace_id": traceID,
			"span_id":  spanID,
		},
		"observability": map[string]interface{}{
			"pipeline_path_hash":   "",
			"pipeline_path_stages": []interface{}{"pdp_ingest", "enforce", "seal", "propagate"},
			"pipeline_duration_ns": durationNs,
			"rpa_enforcement":      "PROPAGATION_LAYER",
		},

		// v14.5 propagation additions
		"pdp_decision_id":    d.DecisionID,
		"response_hash":      "", // filled by envelope seal path
		"chain_binding_hash": "", // filled by envelope seal path
		"propagation_chain":  propChain,
	}
	return resp
}

// CanonicalFromRpaViolation constructs a canonical DENY response for the
// RPA integrity-violation path (v14.1 anti-fooling gate).
func CanonicalFromRpaViolation(
	enfResp *ExecutionResponse,
	req *ExecutionRequest,
	traceCtx *TraceContext,
	rpaDetail, pathHash string,
	stages []string,
	durationNs int64,
) map[string]interface{} {
	// Start from the enforcement envelope and overlay RPA-violation state.
	enfMap := map[string]interface{}{}
	if enfResp != nil {
		enfMap = enfResp.ToMap()
	}

	decisionID := ""
	correlationID := ""
	enfHash := ""
	if enfResp != nil {
		decisionID = enfResp.DecisionID()
		correlationID = enfResp.CorrelationID()
		enfHash = enfResp.EnforcementHash()
	}
	if correlationID == "" && req != nil {
		correlationID = req.CorrelationID()
	}
	if decisionID == "" {
		decisionID = DeterministicDecisionID(PreGateDecisionIDPrefix, "RPA_VIOLATION", correlationID)
	}
	if enfHash == "" {
		enfHash = PreGateEnforcementHash
	}

	reason := "RPA_INTEGRITY_VIOLATION: " + rpaDetail
	errCode := CodeRpaIntegrityViolation

	traceID := ""
	if traceCtx != nil {
		traceID = traceCtx.TraceID
	}

	enfMap["error_code"] = errCode

	execMap := map[string]interface{}{
		"execution_state":  StateRpaViolation,
		"block_reason":     reason,
		"executed":         false,
		"enforcement_hash": enfHash,
		"decision_id":      decisionID,
		"correlation_id":   correlationID,
		"error_code":       errCode,
		"timestamp":        canonicalTimestamp(),
	}

	resp := map[string]interface{}{
		"schema_version":    SchemaVersion,
		"decision_id":       decisionID,
		"verdict":           VerdictDeny,
		"execution_state":   StateRpaViolation,
		"error_code":        errCode,
		"reason":            reason,
		"trace_id":          traceID,
		"correlation_id":    correlationID,
		"enforcement_hash":  enfHash,
		"timestamp":         canonicalTimestamp(),
		"enforcement_token": "",
		"execution_id":      "",
		"request":           requestMap(req),
		"enforcement":       enfMap,
		"execution":         execMap,
		"trace_context":     traceContextMap(traceCtx),
		"observability": map[string]interface{}{
			"pipeline_path_hash":   pathHash,
			"pipeline_path_stages": stages,
			"pipeline_duration_ns": durationNs,
			"rpa_enforcement":      "BLOCKED",
			"rpa_violation":        rpaDetail,
		},
	}
	return resp
}

// CanonicalInternalError constructs a canonical DENY response for a
// panic-recovery path. Used by the defer block in Execute().
func CanonicalInternalError(
	panicValue interface{},
	agentID, resourceID, action, correlationID string,
	traceCtx *TraceContext,
) map[string]interface{} {
	reason := fmt.Sprintf("INTERNAL_PANIC_RECOVERED: %v", panicValue)
	traceID := ""
	if traceCtx != nil {
		traceID = traceCtx.TraceID
	}
	decisionID := DeterministicDecisionID(PreGateDecisionIDPrefix, "INTERNAL_PANIC", correlationID)

	return map[string]interface{}{
		"schema_version":    SchemaVersion,
		"decision_id":       decisionID,
		"verdict":           VerdictDeny,
		"execution_state":   StateBlocked,
		"error_code":        CodeInternal,
		"reason":            reason,
		"trace_id":          traceID,
		"correlation_id":    correlationID,
		"enforcement_hash":  PreGateEnforcementHash,
		"timestamp":         canonicalTimestamp(),
		"enforcement_token": "",
		"execution_id":      "",
		"request":           rawRequestMap(agentID, resourceID, action, correlationID, ""),
		"enforcement":       emptyEnforcementEnvelope(decisionID, VerdictDeny, CodeInternal, reason, PreGateEnforcementHash, correlationID),
		"execution":         emptyExecutionEnvelope(StateBlocked, CodeInternal, reason, correlationID),
		"trace_context":     traceContextMap(traceCtx),
		"observability":     emptyObservabilityEnvelope("PANIC_RECOVERED", reason),
	}
}

// ================================================================
// OUTPUT CONTRACT VALIDATOR (task.md Phase 4)
// ================================================================

// ValidateResponseContract inspects a response map and verifies that every
// field listed in RequiredResponseFields is present AND non-empty AND
// non-nil. Returns (true, nil) on success, (false, missingList) on failure.
//
// "Empty" means:
//   - string: value == "" or value == "<nil>"
//   - nil interface
//   - missing key
//   - a map/slice that is nil (empty but non-nil is OK)
func ValidateResponseContract(resp map[string]interface{}) (bool, []string) {
	if resp == nil {
		return false, RequiredResponseFields
	}
	missing := make([]string, 0)
	for _, field := range RequiredResponseFields {
		v, ok := resp[field]
		if !ok {
			missing = append(missing, field)
			continue
		}
		if v == nil {
			missing = append(missing, field)
			continue
		}
		switch x := v.(type) {
		case string:
			if x == "" || x == "<nil>" {
				missing = append(missing, field)
			}
		case map[string]interface{}:
			if x == nil {
				missing = append(missing, field)
			}
		}
	}
	return len(missing) == 0, missing
}

// EnforceResponseContract is the final gate before any response leaves
// Execute(). If the provided map fails ValidateResponseContract, a fresh
// canonical DENY with CodeContractViolation is synthesized and returned in
// place of the incomplete response. The replacement is built from literal
// constants and the request/traceCtx already in scope, so it cannot itself
// be missing a field.
//
// This is task.md Phase 4 verbatim: "Add validation layer: if response
// incomplete → force DENY. No response leaves system without full schema."
func EnforceResponseContract(
	resp map[string]interface{},
	req *ExecutionRequest,
	traceCtx *TraceContext,
) map[string]interface{} {
	ok, missing := ValidateResponseContract(resp)
	if ok {
		return resp
	}

	correlationID := ""
	agentID := ""
	resourceID := ""
	action := ""
	if req != nil {
		correlationID = req.CorrelationID()
		agentID = req.AgentID()
		resourceID = req.ResourceID()
		action = req.Action()
	}
	if correlationID == "" {
		// Last-resort: pull correlation_id from the broken response if
		// possible — at least preserves the trace linkage.
		if v, present := resp["correlation_id"].(string); present && v != "" {
			correlationID = v
		}
	}

	traceID := ""
	if traceCtx != nil {
		traceID = traceCtx.TraceID
	}
	reason := fmt.Sprintf("RESPONSE_CONTRACT_VIOLATION: missing_fields=%s", strings.Join(missing, ","))
	decisionID := DeterministicDecisionID(ContractDecisionIDPrefix, "CONTRACT_VIOLATION", correlationID)

	return map[string]interface{}{
		"schema_version":    SchemaVersion,
		"decision_id":       decisionID,
		"verdict":           VerdictDeny,
		"execution_state":   StateContractErr,
		"error_code":        CodeContractViolation,
		"reason":            reason,
		"trace_id":          traceID,
		"correlation_id":    correlationID,
		"enforcement_hash":  ContractEnforcementHash,
		"timestamp":         canonicalTimestamp(),
		"enforcement_token": "",
		"execution_id":      "",
		"request":           rawRequestMap(agentID, resourceID, action, correlationID, ""),
		"enforcement":       emptyEnforcementEnvelope(decisionID, VerdictDeny, CodeContractViolation, reason, ContractEnforcementHash, correlationID),
		"execution":         emptyExecutionEnvelope(StateContractErr, CodeContractViolation, reason, correlationID),
		"trace_context":     traceContextMap(traceCtx),
		"observability":     emptyObservabilityEnvelope("CONTRACT_FORCED_DENY", reason),
		"contract_violation": map[string]interface{}{
			"missing_fields":   missing,
			"original_fields":  collectResponseKeys(resp),
			"forced_by":        "EnforceResponseContract",
		},
	}
}

// collectResponseKeys returns a sorted list of keys that WERE present in the
// original (broken) response — useful for post-mortem diagnostics.
func collectResponseKeys(resp map[string]interface{}) []string {
	keys := make([]string, 0, len(resp))
	for k := range resp {
		keys = append(keys, k)
	}
	return keys
}

// ================================================================
// STANDARDIZED PROOF LOGGING (task.md Phase 6)
// ================================================================
//
// LogAttackProof emits a single standardized proof-log line to stdout AND
// appends the same record as JSON to proof_logs/v13_response_contract.jsonl.
// The 6 fields are task.md Phase 6 verbatim.

var (
	proofLogMu sync.Mutex
	proofLogFile *os.File
)

// ProofLogRecord is the on-disk shape of a proof-log entry.
type ProofLogRecord struct {
	AttackType       string      `json:"attack_type"`
	AttackID         string      `json:"attack_id,omitempty"`
	Phase            string      `json:"phase,omitempty"`
	InputPayload     interface{} `json:"input_payload"`
	Expected         string      `json:"expected"`
	Actual           string      `json:"actual"`
	ErrorCode        string      `json:"error_code"`
	TraceID          string      `json:"trace_id"`
	Timestamp        string      `json:"timestamp"`
	SchemaVersion    string      `json:"schema_version"`
	EnforcementHash  string      `json:"enforcement_hash,omitempty"`
	ExecutionState   string      `json:"execution_state,omitempty"`
	DecisionID       string      `json:"decision_id,omitempty"`
	EnforcementToken string      `json:"enforcement_token,omitempty"`
	ExecutionID      string      `json:"execution_id,omitempty"`
}

// LogAttackProof writes a proof-log line to stdout and appends it to
// proof_logs/v13_response_contract.jsonl. Thread-safe.
func LogAttackProof(
	attackType, attackID, phase string,
	inputPayload interface{},
	expected, actual, errorCode, traceID string,
) {
	rec := ProofLogRecord{
		AttackType:    attackType,
		AttackID:      attackID,
		Phase:         phase,
		InputPayload:  inputPayload,
		Expected:      expected,
		Actual:        actual,
		ErrorCode:     errorCode,
		TraceID:       traceID,
		Timestamp:     canonicalTimestamp(),
		SchemaVersion: SchemaVersion,
	}
	data, err := json.Marshal(rec)
	if err != nil {
		// Fail-safe: print a minimal record so the proof chain is never silent.
		fmt.Printf("PROOF_LOG_MARSHAL_ERROR: attack_type=%s error=%v\n", attackType, err)
		return
	}

	proofLogMu.Lock()
	defer proofLogMu.Unlock()

	// Lazy-open the append-only log file on first use.
	if proofLogFile == nil {
		if err := os.MkdirAll("proof_logs", 0o755); err != nil {
			fmt.Printf("PROOF_LOG_MKDIR_ERROR: %v\n", err)
			return
		}
		f, err := os.OpenFile(
			filepath.Join("proof_logs", "v13_response_contract.jsonl"),
			os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644,
		)
		if err != nil {
			fmt.Printf("PROOF_LOG_OPEN_ERROR: %v\n", err)
			return
		}
		proofLogFile = f
	}
	if _, err := proofLogFile.Write(append(data, '\n')); err != nil {
		fmt.Printf("PROOF_LOG_WRITE_ERROR: %v\n", err)
	}
}

// LogAttackProofEnriched writes an enriched proof-log entry that includes
// enforcement_hash, execution_state, decision_id, enforcement_token, and
// execution_id extracted from the full response map. Thread-safe.
func LogAttackProofEnriched(
	attackType, attackID, phase string,
	inputPayload interface{},
	expected, actual string,
	response map[string]interface{},
) {
	getStr := func(m map[string]interface{}, key string) string {
		if v, ok := m[key]; ok {
			if s, ok := v.(string); ok {
				return s
			}
		}
		return ""
	}

	rec := ProofLogRecord{
		AttackType:       attackType,
		AttackID:         attackID,
		Phase:            phase,
		InputPayload:     inputPayload,
		Expected:         expected,
		Actual:           actual,
		ErrorCode:        getStr(response, "error_code"),
		TraceID:          getStr(response, "trace_id"),
		Timestamp:        canonicalTimestamp(),
		SchemaVersion:    SchemaVersion,
		EnforcementHash:  getStr(response, "enforcement_hash"),
		ExecutionState:   getStr(response, "execution_state"),
		DecisionID:       getStr(response, "decision_id"),
		EnforcementToken: getStr(response, "enforcement_token"),
		ExecutionID:      getStr(response, "execution_id"),
	}
	data, err := json.Marshal(rec)
	if err != nil {
		fmt.Printf("PROOF_LOG_MARSHAL_ERROR: attack_type=%s error=%v\n", attackType, err)
		return
	}

	proofLogMu.Lock()
	defer proofLogMu.Unlock()

	if proofLogFile == nil {
		if err := os.MkdirAll("proof_logs", 0o755); err != nil {
			fmt.Printf("PROOF_LOG_MKDIR_ERROR: %v\n", err)
			return
		}
		f, err := os.OpenFile(
			filepath.Join("proof_logs", "v13_response_contract.jsonl"),
			os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644,
		)
		if err != nil {
			fmt.Printf("PROOF_LOG_OPEN_ERROR: %v\n", err)
			return
		}
		proofLogFile = f
	}
	if _, err := proofLogFile.Write(append(data, '\n')); err != nil {
		fmt.Printf("PROOF_LOG_WRITE_ERROR: %v\n", err)
	}
}

// CloseProofLog flushes and closes the proof log. Called from the harness
// teardown path.
func CloseProofLog() {
	proofLogMu.Lock()
	defer proofLogMu.Unlock()
	if proofLogFile != nil {
		_ = proofLogFile.Sync()
		_ = proofLogFile.Close()
		proofLogFile = nil
	}
}

// ================================================================
// CANONICAL FIELD READER
// ================================================================
//
// canonicalString extracts a canonical top-level string field from a
// response map. It returns the empty string (NOT "<nil>") on any failure
// so attack-harness comparisons never match the literal string "<nil>".
// Use this whenever a caller (harness, test, logger) reads the top-level
// schema fields defined in RequiredResponseFields.
func canonicalString(resp map[string]interface{}, field string) string {
	if resp == nil {
		return ""
	}
	v, ok := resp[field]
	if !ok || v == nil {
		return ""
	}
	if s, ok := v.(string); ok {
		if s == "<nil>" {
			return ""
		}
		return s
	}
	return fmt.Sprintf("%v", v)
}
