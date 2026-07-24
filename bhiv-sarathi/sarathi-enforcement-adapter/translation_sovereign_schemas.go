package main

// translation_sovereign_schemas.go — Outbound translation wire shapes (v15.7).
//
// HISTORY: this file used to also hold the 9-field SovereignDecideResponse
// shape and the bhiv.sovereign.decide/v1.0 inbound schema. The inbound path
// was replaced by TANTRA (tantra.decision.v1) in v15.7; see
// service_boundary_tantra.go + tantra_*.go. The constants below are still
// shared by the OUTBOUND translation files (translation_bucket_artifact.go,
// translation_insightflow.go), so the file is retained at a reduced scope.
//
// Output schemas (Bucket + InsightFlow) live here so every cross-system wire
// format is in one place.
//
// TAG: translation-layer

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
)

// ============================================================================
// Schema version constants (one place, one owner)
// ============================================================================

// Sarathi → Bucket
const (
	BucketArtifactSchemaV1   = "bhiv.bucket.artifact/v1.0"
	BucketSourceModuleID     = "sarathi.enforcement_adapter"
	BucketArtifactTypeDecide = "enforcement_decision"
)

// Sarathi → InsightFlow
const (
	InsightFlowSchemaAVersion = "bhiv.insightflow.trigger/v1.0"
	InsightFlowSchemaBVersion = "bhiv.insightflow.persist/v1.0"
	InsightFlowSchemaCVersion = "bhiv.insightflow.execute/v1.0"
	InsightFlowSchemaDVersion = "bhiv.insightflow.process/v1.0"
)

// SovereignBHIVCoreEvaluatorID is the only issuer the /sarathi/enforce path
// will accept. The /v1/ingest-decision self-test path accepts any registered
// evaluator (e.g. "self_test").
const SovereignBHIVCoreEvaluatorID = "sovereign_bhiv_core"

// BucketArtifactGenesisHash is the chain anchor used as parent_hash for the
// FIRST artifact in any trace. The value was provided by the Bucket team
// (Siddhesh, 2026-05-08) and is the genesis/anchor hash their chain expects.
// It is treated as an opaque registered constant — Sarathi does NOT recompute
// it from a sentinel string. Change requires coordination with the Bucket
// team to migrate the chain.
//
// If a future Bucket-team change rotates this value, override at runtime via
// SARATHI_BUCKET_GENESIS_HASH env var (read at process start by
// loadBucketGenesisHash below); the registered constant remains the default.
const BucketArtifactRegisteredGenesisHash = "642a0cee554bb172a8b3f8f83c4c49f10b1908290c98d92e04ba32c6aee23e97"

// BucketArtifactGenesisHash resolves to the env-overridable genesis. The
// `var` form (rather than `const`) lets us substitute via env var without
// touching call sites.
var BucketArtifactGenesisHash = loadBucketGenesisHash()

// loadBucketGenesisHash returns the configured Bucket-team genesis hash. It
// prefers SARATHI_BUCKET_GENESIS_HASH env var (operator override for chain
// migrations) and falls back to BucketArtifactRegisteredGenesisHash.
func loadBucketGenesisHash() string {
	if v := os.Getenv("SARATHI_BUCKET_GENESIS_HASH"); v != "" {
		return v
	}
	return BucketArtifactRegisteredGenesisHash
}

// _ = sha256.Sum256 / hex.EncodeToString are imported by other files in the
// translation package; keep imports explicit here for the env-loaded variant.
var _ = sha256.Size
var _ = hex.EncodedLen

// ============================================================================
// BucketArtifact — Sarathi → Bucket envelope
// ============================================================================

// BucketArtifact is the BHIV-spec body posted to POST /bucket/artifact AFTER
// the Sarathi enforcement decision is sealed. It is content-addressed via
// artifact_id = sha256(canonical(payload)) and chained per trace_id via
// parent_hash. The Bucket peer stores the artifact verbatim; replay of a
// trace_id reconstructs the chain from artifact_id → parent_hash → ... →
// BucketArtifactGenesisHash.
// NOTE: trace_id is NOT a top-level field. The deployed Bucket's
// /bucket/schema-info allows only {artifact_id, timestamp_utc, schema_version,
// source_module_id, artifact_type, parent_hash, payload, hash} and rejects any
// other top-level key as "Schema drift". trace_id lives inside payload.
type BucketArtifact struct {
	ArtifactID     string                `json:"artifact_id"`      // sha256(canonical(payload))
	TimestampUTC   string                `json:"timestamp_utc"`    // RFC3339Nano UTC, sealed time
	SchemaVersion  string                `json:"schema_version"`   // BucketArtifactSchemaV1
	SourceModuleID string                `json:"source_module_id"` // BucketSourceModuleID
	ArtifactType   string                `json:"artifact_type"`    // BucketArtifactTypeDecide
	ParentHash     string                `json:"parent_hash"`      // chained per trace_id
	Payload        BucketArtifactPayload `json:"payload"`
}

// BucketArtifactPayload carries the full Sarathi enforcement record. By living
// inside `payload` the BHIV envelope stays stable while the inner record can
// be extended without breaking the bucket schema.
type BucketArtifactPayload struct {
	DecisionID       string   `json:"decision_id"`
	TraceID          string   `json:"trace_id"` // verbatim from Core (lives in payload, not top-level)
	Verdict          string   `json:"verdict"`
	EvaluatorID      string   `json:"evaluator_id"`
	DecisionHash     string   `json:"decision_hash"`
	DecisionCoreHash string   `json:"decision_core_hash"`
	EnforcementHash  string   `json:"enforcement_hash"`
	ResponseHash     string   `json:"response_hash"`
	ChainBindingHash string   `json:"chain_binding_hash"`
	PolicyReference  string   `json:"policy_reference,omitempty"`
	InputHash        string   `json:"input_hash,omitempty"`
	AgentID          string   `json:"agent_id"`
	ResourceID       string   `json:"resource_id"`
	Action           string   `json:"action"`
	Obligations      []string `json:"obligations,omitempty"`
	EnforcedAt       string   `json:"enforced_at"`
	SealedAt         string   `json:"sealed_at"`
	LayerBindingHash string   `json:"layer_binding_hash,omitempty"`
	// v15.12 — base64-std of the verbatim canonical 20-field enforcement
	// response Sarathi sealed. Peers base64-decode this and SHA-256 the
	// result to compute observed_response_hash, which they put in the
	// callback receipt. Lets the peer verify decision integrity without
	// needing to reconstruct canonical bytes from the projected fields above.
	CanonicalResponseB64 string `json:"canonical_response_b64,omitempty"`
}

// ============================================================================
// InsightFlow Schemas A / B / C / D — Sarathi → InsightFlow
// ============================================================================

// InsightFlowSchemaA — POST /sarathi_trigger.
// Trigger event fired at start-of-trace. Carries the human-readable request
// envelope so InsightFlow can hydrate the trace without a Sarathi callback.
type InsightFlowSchemaA struct {
	TraceID      string                    `json:"trace_id"`
	Timestamp    string                    `json:"timestamp"`
	SourceSystem string                    `json:"source_system"` // "Sarathi"
	EventType    string                    `json:"event_type"`    // "sarathi_trigger"
	Payload      InsightFlowSchemaAPayload `json:"payload"`
}

// InsightFlowSchemaAPayload is the inner envelope of Schema A.
type InsightFlowSchemaAPayload struct {
	RequestID string                 `json:"request_id"` // = correlation_id
	UserID    string                 `json:"user_id"`    // = agent_id
	Query     string                 `json:"query"`      // = action + " " + resource_id
	Data      map[string]interface{} `json:"data"`       // decision metadata projection
	Metadata  InsightFlowSchemaAMeta `json:"metadata"`
}

// InsightFlowSchemaAMeta carries dispatch metadata.
type InsightFlowSchemaAMeta struct {
	Priority string `json:"priority"` // ESCALATE→high, DENY→medium, ALLOW→low
	Channel  string `json:"channel"`  // caller_system / "api"
	Version  string `json:"version"`  // schema_version of source
}

// InsightFlowSchemaB — POST /bucket_persist.
// Smallest fingerprint (4 fields). Observability-only persistence signal —
// the real bucket write happens at /bucket/artifact.
type InsightFlowSchemaB struct {
	TraceID     string `json:"trace_id"`
	PayloadHash string `json:"payload_hash"` // = response_hash
	Timestamp   string `json:"timestamp"`
	SystemTag   string `json:"system_tag"` // "Sarathi"
}

// InsightFlowSchemaC — POST /core_execute.
// Multi-hop tracking envelope — origin/current/sequence/hop_count let
// InsightFlow build a hop graph. Used at the cross-system jump from Sarathi
// to BHIV Core.
type InsightFlowSchemaC struct {
	TraceID       string                      `json:"trace_id"`
	OriginSystem  string                      `json:"origin_system"`  // "Sarathi"
	CurrentSystem string                      `json:"current_system"` // "Core"
	EventSequence int                         `json:"event_sequence"` // monotonic per trace
	Timestamp     string                      `json:"timestamp"`
	Payload       InsightFlowSchemaCPayload   `json:"payload"`
	TraceMetadata InsightFlowSchemaCTraceMeta `json:"trace_metadata"`
}

// InsightFlowSchemaCPayload is the inner envelope of Schema C.
type InsightFlowSchemaCPayload struct {
	RequestID string                 `json:"request_id"`
	UserID    string                 `json:"user_id"`
	Query     string                 `json:"query"`
	Data      map[string]interface{} `json:"data"`
}

// InsightFlowSchemaCTraceMeta carries hop-tracking metadata for Schema C.
type InsightFlowSchemaCTraceMeta struct {
	PayloadHash   string `json:"payload_hash"`     // = response_hash
	ParentTraceID string `json:"parent_trace_id"`  // empty for root
	HopCount      int    `json:"hop_count"`
}

// InsightFlowSchemaD — POST /insightflow_process and GET /bucket/verify/{trace_id}.
// Verification status envelope — PASS|FAIL + check breakdown + run_metrics.
type InsightFlowSchemaD struct {
	TraceID         string                  `json:"trace_id"`
	Status          string                  `json:"status"` // PASS | FAIL
	Checks          InsightFlowSchemaDChecks `json:"checks"`
	SystemsVerified []string                `json:"systems_verified"`
	ErrorDetails    []InsightFlowErrorDetail `json:"error_details"`
	RunMetrics      InsightFlowSchemaDMetrics `json:"run_metrics"`
	// v15.12 — additive carrier for the verbatim canonical 20-field
	// enforcement response. Same purpose as BucketArtifactPayload.CanonicalResponseB64.
	DecisionID           string `json:"decision_id,omitempty"`
	ResponseHash         string `json:"response_hash,omitempty"`
	CanonicalResponseB64 string `json:"canonical_response_b64,omitempty"`
}

// InsightFlowSchemaDChecks is the verification-check breakdown.
type InsightFlowSchemaDChecks struct {
	MutationCheck bool `json:"mutation_check"` // true if response_hash recomputes
	LossCheck     bool `json:"loss_check"`     // true if all hops echoed ack_hash
	OrderCheck    bool `json:"order_check"`    // true if chain_binding_hash verifies
}

// InsightFlowErrorDetail is one entry in error_details[].
type InsightFlowErrorDetail struct {
	System string `json:"system"`
	Issue  string `json:"issue"`
}

// InsightFlowSchemaDMetrics is the run-level metric tally.
type InsightFlowSchemaDMetrics struct {
	TotalRuns int `json:"total_runs"`
	Success   int `json:"success"`
	Failure   int `json:"failure"`
}
