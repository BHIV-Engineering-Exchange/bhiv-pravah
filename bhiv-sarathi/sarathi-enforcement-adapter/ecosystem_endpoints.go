// ecosystem_endpoints.go (v15.2 Real-BHIV Ecosystem Wiring)
//
// Single source of truth for every BHIV-facing URL. Replaces the four scattered
// SARATHI_ROUTE_*_URL reads in multi_system_router.go and adds the 10 BHIV API
// endpoints the user provided:
//
//   Bucket  (3): POST /bucket/artifact, GET /bucket/artifact/{id},
//                GET  /bucket/artifacts?trace_id={id}
//   InsightFlow (4): POST /sarathi_trigger, /core_execute,
//                    /insightflow_process, /bucket_persist
//   Core    (3): POST /v1/enforce, /v1/execute, GET /health
//
// At deploy time the operator either:
//   (a) sets the per-endpoint env vars listed below to the actual BHIV
//       routable URLs, OR
//   (b) edits DefaultEndpoints() in this file to bake URLs into the binary.
//
// No other code path hardcodes a URL. To swap localhost for real IPs, edit
// here once.
//
// TAG: ecosystem-wiring

package main

import (
	"fmt"
	"net/url"
	"os"
	"strings"
)

// ----------------------------------------------------------------------------
// Endpoint structs
// ----------------------------------------------------------------------------

// CoreEndpoints carries the BHIV Core endpoints exposed across Raj's four
// services: Core API (port 8003), MCP Bridge (port 8000), Sovereign Core
// (port 9001), and Sarathi Enforcer (port 9002 — Sarathi-side, exposed by
// us via the alias routes in service_boundary.go).
//
// Wire-contract reference (Raj, BHIV Core team):
//   POST /execute_task        Core API     8003
//   POST /execute_sequence    Core API     8003
//   GET  /health              Core API     8003
//   POST /handle_task         MCP Bridge   8000
//   POST /sovereign/decide    Sovereign    9001  (decision ingestion)
//   GET  /health              Sovereign    9001
//   POST /sarathi/enforce     Sarathi      9002  (Sarathi-exposed alias)
//   GET  /sarathi/validate-token?token=… 9002
//   GET  /health              Sarathi      9002
type CoreEndpoints struct {
	// Enforce — primary in-chain propagation target. Receives the sealed
	// envelope; preserves the v14.7+ wire contract. Historically points to
	// /v1/enforce; in BHIV ecosystem may point to /execute_task.
	Enforce string

	// Execute — secondary action endpoint used by parallel-real-traffic
	// comparison and by InsightFlow's /core_execute side-channel.
	Execute string

	// Health — liveness probe consumed by service boot pre-flight + cross-
	// machine telemetry. GET only.
	Health string

	// ExecuteTask — Core API /execute_task (port 8003). Single-task execution.
	// New v15.3 from Raj's BHIV Core spec.
	ExecuteTask string

	// ExecuteSequence — Core API /execute_sequence (port 8003). Multi-task
	// sequence execution. New v15.3 from Raj's BHIV Core spec.
	ExecuteSequence string

	// HandleTask — MCP Bridge /handle_task (port 8000). Main task ingestion
	// path: Core → MCP Bridge → Sovereign decide → Sarathi enforce.
	HandleTask string

	// SovereignDecide — Sovereign Core /sovereign/decide (port 9001). The
	// decision ingestion endpoint where input is judged (ALLOW/DENY) and a
	// signed decision (with decision_hash, trace_id, policy_reference) is
	// returned. This is the upstream PDP that produces decisions Sarathi
	// then enforces.
	SovereignDecide string

	// SovereignHealth — Sovereign Core /health (port 9001).
	SovereignHealth string
}

// InsightFlowEndpoints carries the 5 BHIV InsightFlow endpoints exactly as the
// FastAPI /docs surface advertises them.
type InsightFlowEndpoints struct {
	// SarathiTrigger — entry trigger from Sarathi to InsightFlow.
	// /sarathi_trigger_post in BHIV's OpenAPI.
	SarathiTrigger string

	// CoreExecute — InsightFlow's view of a Core execute action.
	// /core_execute_post in BHIV's OpenAPI.
	CoreExecute string

	// InsightFlowProcess — primary observability ingest (digest only).
	// /insightflow_process_post in BHIV's OpenAPI.
	InsightFlowProcess string

	// BucketPersist — InsightFlow-mediated bucket persistence signal.
	// /bucket_persist_post in BHIV's OpenAPI.
	BucketPersist string

	// VerifyBucket — InsightFlow's bucket-trace verification endpoint.
	// /bucket/verify/{trace_id} — GET. New v15.3 from BHIV's OpenAPI.
	// Used by Vijay's side to confirm trace continuity in cross-system
	// validation.
	VerifyBucket string
}

// BucketEndpoints carries the 3 BHIV Bucket endpoints.
type BucketEndpoints struct {
	// ArtifactPost — store the sealed canonical bytes as an artifact.
	// Maps to POST /bucket/artifact.
	ArtifactPost string

	// ArtifactGet — retrieve a single artifact by decision_id (used by
	// bucket_readback_verifier.go).  Trailing /{id} appended at call time.
	ArtifactGet string

	// ArtifactsByTrace — list every artifact for a trace_id (NEW: trace-level
	// verification). Trailing ?trace_id=... appended at call time.
	ArtifactsByTrace string
}

// EcosystemEndpoints aggregates all 10 BHIV endpoints into one config struct.
type EcosystemEndpoints struct {
	Core        CoreEndpoints
	InsightFlow InsightFlowEndpoints
	Bucket      BucketEndpoints

	// Source captures how the endpoints were resolved (env / default / mixed).
	// Used by README.md operators and by --vc-session pre-flight reports.
	Source string
}

// ----------------------------------------------------------------------------
// Environment variable names (single source of truth)
// ----------------------------------------------------------------------------

const (
	// Core (legacy 3 — kept for v15.2 backward compat)
	EnvCoreEnforceURL = "SARATHI_CORE_ENFORCE_URL"
	EnvCoreExecuteURL = "SARATHI_CORE_EXECUTE_URL"
	EnvCoreHealthURL  = "SARATHI_CORE_HEALTH_URL"

	// Core full BHIV surface (Raj's v15.3 spec)
	EnvCoreExecuteTaskURL     = "SARATHI_CORE_EXECUTE_TASK_URL"
	EnvCoreExecuteSequenceURL = "SARATHI_CORE_EXECUTE_SEQUENCE_URL"
	EnvCoreHandleTaskURL      = "SARATHI_CORE_HANDLE_TASK_URL"
	EnvCoreSovereignDecideURL = "SARATHI_CORE_SOVEREIGN_DECIDE_URL"
	EnvCoreSovereignHealthURL = "SARATHI_CORE_SOVEREIGN_HEALTH_URL"

	// InsightFlow (4 + 1 NEW v15.3 verify_bucket)
	EnvInsightTriggerURL       = "SARATHI_INSIGHT_TRIGGER_URL"
	EnvInsightExecuteURL       = "SARATHI_INSIGHT_EXECUTE_URL"
	EnvInsightProcessURL       = "SARATHI_INSIGHT_PROCESS_URL"
	EnvInsightBucketPersistURL = "SARATHI_INSIGHT_BUCKET_PERSIST_URL"
	EnvInsightVerifyBucketURL  = "SARATHI_INSIGHT_VERIFY_BUCKET_URL"

	// Bucket
	EnvBucketArtifactPostURL    = "SARATHI_BUCKET_ARTIFACT_POST_URL"
	EnvBucketArtifactGetURL     = "SARATHI_BUCKET_ARTIFACT_GET_URL"
	EnvBucketArtifactsTraceURL  = "SARATHI_BUCKET_ARTIFACTS_TRACE_URL"

	// Legacy fallbacks (kept for v14.x backward compat)
	EnvLegacyCoreURL        = "SARATHI_ROUTE_CORE_URL"
	EnvLegacyInsightFlowURL = "SARATHI_ROUTE_INSIGHTFLOW_URL"
	EnvLegacyBucketURL      = "SARATHI_ROUTE_BUCKET_URL"
)

// ----------------------------------------------------------------------------
// DefaultEndpoints — operator-edits-here surface
// ----------------------------------------------------------------------------

// DefaultEndpoints returns the deployment defaults. v15.4 removes the
// prior demo IP defaults; every URL is now a fail-loud placeholder of the
// form
//   http://ngrok-url-not-set.local:NNNN/<path>
// which parses successfully (so Validate() does not abort boot) but fails
// at HTTP-call time with an obvious error and triggers the placeholder
// guard in cmd_post_task.go::RunPostTaskToCore.
//
// The operator's only correct path is to set the env vars listed in the
// const block above — easiest done via scripts/ngrok_env.sh (or .ps1) at
// session start.
//
// To pin a fixed deployment URL into the binary, edit this function. To
// override at deploy time, set per-endpoint env vars (preferred — keeps the
// binary immutable across environments).
func DefaultEndpoints() EcosystemEndpoints {
	const placeholder = "ngrok-url-not-set.local"
	return EcosystemEndpoints{
		Core: CoreEndpoints{
			// Legacy 3 (kept for v14.x wire compat with /v1/enforce naming).
			Enforce: "http://" + placeholder + ":8003/execute_task",
			Execute: "http://" + placeholder + ":8003/execute_task",
			Health:  "http://" + placeholder + ":8003/health",

			// Full BHIV Core surface (Raj's spec).
			ExecuteTask:     "http://" + placeholder + ":8003/execute_task",
			ExecuteSequence: "http://" + placeholder + ":8003/execute_sequence",
			HandleTask:      "http://" + placeholder + ":8000/handle_task",
			SovereignDecide: "http://" + placeholder + ":9001/sovereign/decide",
			SovereignHealth: "http://" + placeholder + ":9001/health",
		},
		InsightFlow: InsightFlowEndpoints{
			SarathiTrigger:     "http://" + placeholder + ":8001/sarathi_trigger",
			CoreExecute:        "http://" + placeholder + ":8001/core_execute",
			InsightFlowProcess: "http://" + placeholder + ":8001/insightflow_process",
			BucketPersist:      "http://" + placeholder + ":8001/bucket_persist",
			VerifyBucket:       "http://" + placeholder + ":8001/bucket/verify",
		},
		Bucket: BucketEndpoints{
			ArtifactPost:     "http://" + placeholder + ":8000/bucket/artifact",
			ArtifactGet:      "http://" + placeholder + ":8000/bucket/artifact",
			ArtifactsByTrace: "http://" + placeholder + ":8000/bucket/artifacts",
		},
		Source: "default",
	}
}

// PlaceholderHostMarker is the host substring embedded in every default URL
// returned by DefaultEndpoints(). Callers that need to refuse to make a
// network request against an unset endpoint should check for this marker
// in the resolved URL and abort before dialling. Operators must source
// scripts/ngrok_env.sh (or scripts/ngrok_env.ps1) at session start.
const PlaceholderHostMarker = "ngrok-url-not-set.local"

// ----------------------------------------------------------------------------
// v15.6 Bridge-facing JWT Authority paths.
// ----------------------------------------------------------------------------
//
// These are the HTTP paths the new outbound JWT authority publishes. They are
// referenced from jwt_authority_handlers.go (route registration), from the
// discovery doc builder in jwt_authority_jwks.go, and from documentation +
// validation scripts. Single source of truth — never hardcode any of these
// strings elsewhere.
const (
	// JWKSPath is the public JWK Set endpoint Bridge fetches once at
	// startup and caches per RFC 7517 / RFC 8037.
	JWKSPath = "/sarathi/.well-known/jwks.json"

	// AuthorityDiscoveryPath is the OIDC-style discovery document (RFC 8414
	// adapted). Advertises the JWKS URI, the token endpoint
	// (= /sarathi/enforce), and the introspection endpoint.
	AuthorityDiscoveryPath = "/sarathi/.well-known/sarathi-authority"

	// TokenIntrospectPath is the RFC 7662 introspection endpoint. Optional
	// (Bridge can verify offline against JWKS); used when the operator
	// wants per-call revocation / consumption status.
	TokenIntrospectPath = "/sarathi/v1/token/introspect"
)

// ----------------------------------------------------------------------------
// Environment loader
// ----------------------------------------------------------------------------

// LoadEcosystemEndpoints resolves all 10 endpoints with the precedence:
//   1. Per-endpoint env var (preferred)
//   2. Legacy SARATHI_ROUTE_*_URL env var (mapped to the in-chain endpoint)
//   3. DefaultEndpoints() constant
//
// Returns an error if any final URL is empty or syntactically malformed.
// Source is set to "env" if any per-endpoint var was present, "legacy" if
// only legacy vars set the URLs, "default" if no env vars were used, or
// "mixed" if both env styles contributed.
func LoadEcosystemEndpoints() (*EcosystemEndpoints, error) {
	defaults := DefaultEndpoints()
	out := defaults

	envHit := false
	legacyHit := false

	// ---- Core ----------------------------------------------------------
	if v := strings.TrimSpace(os.Getenv(EnvCoreEnforceURL)); v != "" {
		out.Core.Enforce = v
		envHit = true
	} else if v := strings.TrimSpace(os.Getenv(EnvLegacyCoreURL)); v != "" {
		out.Core.Enforce = v
		legacyHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvCoreExecuteURL)); v != "" {
		out.Core.Execute = v
		envHit = true
	} else if v := strings.TrimSpace(os.Getenv(EnvLegacyCoreURL)); v != "" {
		// Derive /execute path from legacy base URL by replacing trailing
		// /enforce with /execute. If no /enforce suffix, append /execute.
		out.Core.Execute = deriveSiblingPath(v, "/v1/enforce", "/v1/execute")
		legacyHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvCoreHealthURL)); v != "" {
		out.Core.Health = v
		envHit = true
	} else if v := strings.TrimSpace(os.Getenv(EnvLegacyCoreURL)); v != "" {
		out.Core.Health = deriveSiblingPath(v, "/v1/enforce", "/health")
		legacyHit = true
	}
	// Full BHIV Core surface (Raj's v15.3 spec) — each endpoint resolves
	// from its own env var; if unset it keeps the placeholder URL and the
	// wiring check (§14) will mark it UNREACHABLE.
	if v := strings.TrimSpace(os.Getenv(EnvCoreExecuteTaskURL)); v != "" {
		out.Core.ExecuteTask = v
		envHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvCoreExecuteSequenceURL)); v != "" {
		out.Core.ExecuteSequence = v
		envHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvCoreHandleTaskURL)); v != "" {
		out.Core.HandleTask = v
		envHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvCoreSovereignDecideURL)); v != "" {
		out.Core.SovereignDecide = v
		envHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvCoreSovereignHealthURL)); v != "" {
		out.Core.SovereignHealth = v
		envHit = true
	}

	// ---- InsightFlow ---------------------------------------------------
	if v := strings.TrimSpace(os.Getenv(EnvInsightTriggerURL)); v != "" {
		out.InsightFlow.SarathiTrigger = v
		envHit = true
	} else if v := strings.TrimSpace(os.Getenv(EnvLegacyInsightFlowURL)); v != "" {
		out.InsightFlow.SarathiTrigger = deriveSiblingPath(v, "/v1/observe", "/sarathi_trigger")
		legacyHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvInsightExecuteURL)); v != "" {
		out.InsightFlow.CoreExecute = v
		envHit = true
	} else if v := strings.TrimSpace(os.Getenv(EnvLegacyInsightFlowURL)); v != "" {
		out.InsightFlow.CoreExecute = deriveSiblingPath(v, "/v1/observe", "/core_execute")
		legacyHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvInsightProcessURL)); v != "" {
		out.InsightFlow.InsightFlowProcess = v
		envHit = true
	} else if v := strings.TrimSpace(os.Getenv(EnvLegacyInsightFlowURL)); v != "" {
		// Legacy /v1/observe maps semantically to /insightflow_process in BHIV.
		out.InsightFlow.InsightFlowProcess = v
		legacyHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvInsightBucketPersistURL)); v != "" {
		out.InsightFlow.BucketPersist = v
		envHit = true
	} else if v := strings.TrimSpace(os.Getenv(EnvLegacyInsightFlowURL)); v != "" {
		out.InsightFlow.BucketPersist = deriveSiblingPath(v, "/v1/observe", "/bucket_persist")
		legacyHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvInsightVerifyBucketURL)); v != "" {
		out.InsightFlow.VerifyBucket = v
		envHit = true
	} else if v := strings.TrimSpace(os.Getenv(EnvLegacyInsightFlowURL)); v != "" {
		out.InsightFlow.VerifyBucket = deriveSiblingPath(v, "/v1/observe", "/bucket/verify")
		legacyHit = true
	}

	// ---- Bucket --------------------------------------------------------
	if v := strings.TrimSpace(os.Getenv(EnvBucketArtifactPostURL)); v != "" {
		out.Bucket.ArtifactPost = v
		envHit = true
	} else if v := strings.TrimSpace(os.Getenv(EnvLegacyBucketURL)); v != "" {
		out.Bucket.ArtifactPost = v
		legacyHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvBucketArtifactGetURL)); v != "" {
		out.Bucket.ArtifactGet = v
		envHit = true
	} else if v := strings.TrimSpace(os.Getenv(EnvLegacyBucketURL)); v != "" {
		out.Bucket.ArtifactGet = v
		legacyHit = true
	}
	if v := strings.TrimSpace(os.Getenv(EnvBucketArtifactsTraceURL)); v != "" {
		out.Bucket.ArtifactsByTrace = v
		envHit = true
	} else if v := strings.TrimSpace(os.Getenv(EnvLegacyBucketURL)); v != "" {
		out.Bucket.ArtifactsByTrace = deriveSiblingPath(v, "/v1/audit", "/bucket/artifacts")
		legacyHit = true
	}

	switch {
	case envHit && legacyHit:
		out.Source = "mixed"
	case envHit:
		out.Source = "env"
	case legacyHit:
		out.Source = "legacy"
	default:
		out.Source = "default"
	}

	if err := out.Validate(); err != nil {
		return &out, err
	}
	return &out, nil
}

// Validate asserts every URL is non-empty and parseable. Returns the first
// failure as an error suitable for boot-time refusal. The v15.4 unset-
// default placeholder host (`ngrok-url-not-set.local`, see
// PlaceholderHostMarker) is NOT rejected here — it parses successfully so
// boot can proceed for non-network code paths, but cmd_post_task.go and
// any other caller making a real HTTP request must check for the marker
// and fail loud with operator-actionable instructions.
func (e *EcosystemEndpoints) Validate() error {
	checks := []struct {
		name string
		url  string
	}{
		{EnvCoreEnforceURL, e.Core.Enforce},
		{EnvCoreExecuteURL, e.Core.Execute},
		{EnvCoreHealthURL, e.Core.Health},
		{EnvCoreExecuteTaskURL, e.Core.ExecuteTask},
		{EnvCoreExecuteSequenceURL, e.Core.ExecuteSequence},
		{EnvCoreHandleTaskURL, e.Core.HandleTask},
		{EnvCoreSovereignDecideURL, e.Core.SovereignDecide},
		{EnvCoreSovereignHealthURL, e.Core.SovereignHealth},
		{EnvInsightTriggerURL, e.InsightFlow.SarathiTrigger},
		{EnvInsightExecuteURL, e.InsightFlow.CoreExecute},
		{EnvInsightProcessURL, e.InsightFlow.InsightFlowProcess},
		{EnvInsightBucketPersistURL, e.InsightFlow.BucketPersist},
		{EnvInsightVerifyBucketURL, e.InsightFlow.VerifyBucket},
		{EnvBucketArtifactPostURL, e.Bucket.ArtifactPost},
		{EnvBucketArtifactGetURL, e.Bucket.ArtifactGet},
		{EnvBucketArtifactsTraceURL, e.Bucket.ArtifactsByTrace},
	}
	for _, c := range checks {
		if strings.TrimSpace(c.url) == "" {
			return fmt.Errorf("ecosystem_endpoints: %s is empty", c.name)
		}
		u, err := url.Parse(c.url)
		if err != nil {
			return fmt.Errorf("ecosystem_endpoints: %s parse error: %w", c.name, err)
		}
		if u.Scheme != "http" && u.Scheme != "https" {
			return fmt.Errorf("ecosystem_endpoints: %s scheme must be http(s), got %q", c.name, u.Scheme)
		}
		if u.Host == "" {
			return fmt.Errorf("ecosystem_endpoints: %s host is empty", c.name)
		}
	}
	return nil
}

// AllURLs returns every configured URL as a flat slice for pre-flight probes
// and telemetry tagging. Includes the legacy 3 + new 5 Core endpoints + 5
// InsightFlow + 3 Bucket = 16 total.
func (e *EcosystemEndpoints) AllURLs() []string {
	return []string{
		e.Core.Enforce,
		e.Core.Execute,
		e.Core.Health,
		e.Core.ExecuteTask,
		e.Core.ExecuteSequence,
		e.Core.HandleTask,
		e.Core.SovereignDecide,
		e.Core.SovereignHealth,
		e.InsightFlow.SarathiTrigger,
		e.InsightFlow.CoreExecute,
		e.InsightFlow.InsightFlowProcess,
		e.InsightFlow.BucketPersist,
		e.InsightFlow.VerifyBucket,
		e.Bucket.ArtifactPost,
		e.Bucket.ArtifactGet,
		e.Bucket.ArtifactsByTrace,
	}
}

// IsLoopback returns true if every URL points at 127.0.0.1 or localhost. Used
// by SARATHI_CROSS_MACHINE_STRICT to refuse loopback-only deployments.
func (e *EcosystemEndpoints) IsLoopback() bool {
	for _, raw := range e.AllURLs() {
		u, err := url.Parse(raw)
		if err != nil {
			return false
		}
		host := u.Hostname()
		if host != "127.0.0.1" && host != "localhost" && host != "::1" {
			return false
		}
	}
	return true
}

// HasAnyLoopback returns true if at least one URL points at loopback. Useful
// for warnings (vs. IsLoopback's all-or-nothing check).
func (e *EcosystemEndpoints) HasAnyLoopback() bool {
	for _, raw := range e.AllURLs() {
		u, err := url.Parse(raw)
		if err != nil {
			continue
		}
		host := u.Hostname()
		if host == "127.0.0.1" || host == "localhost" || host == "::1" {
			return true
		}
	}
	return false
}

// ArtifactGetURLFor builds GET /bucket/artifact/{decision_id}.
func (e *EcosystemEndpoints) ArtifactGetURLFor(decisionID string) string {
	base := strings.TrimRight(e.Bucket.ArtifactGet, "/")
	return base + "/" + safeDecisionID(decisionID)
}

// ArtifactsByTraceURLFor builds GET /bucket/artifacts?trace_id={trace_id}.
func (e *EcosystemEndpoints) ArtifactsByTraceURLFor(traceID string) string {
	base := e.Bucket.ArtifactsByTrace
	sep := "?"
	if strings.Contains(base, "?") {
		sep = "&"
	}
	return base + sep + "trace_id=" + url.QueryEscape(traceID)
}

// ----------------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------------

// deriveSiblingPath replaces oldSuffix with newSuffix in raw. If raw does not
// end with oldSuffix, the function strips a trailing slash and appends
// newSuffix as-is. The result is always a complete URL.
func deriveSiblingPath(raw, oldSuffix, newSuffix string) string {
	raw = strings.TrimRight(raw, "/")
	if strings.HasSuffix(raw, oldSuffix) {
		return strings.TrimSuffix(raw, oldSuffix) + newSuffix
	}
	if strings.HasPrefix(newSuffix, "/") {
		return raw + newSuffix
	}
	return raw + "/" + newSuffix
}
