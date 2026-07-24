package main

// service_boundary_propagation_hook.go — v15.11 production peer fan-out hook.
//
// EVOLUTION:
//
//   v15.10 (deprecated) — invoked BHIVTranslatedFanOut which wrapped the
//     canonical response in a BucketArtifact envelope (Path B). Caused the
//     `received_body_hash == response_hash` gate in VerifyReceipt to fail
//     because the wrapper bytes hash to a different value than Sarathi's
//     internal response_hash.
//
//   v15.11 (this file) — invokes the ecosystem clients DIRECTLY with the
//     raw canonical envelope bytes (Path A). Bucket / InsightFlow / Core
//     each compute SHA-256 over the body they received and, by
//     construction, that hash equals Sarathi's minted response_hash. The
//     receipt verifier check `received_body_hash == response_hash`
//     succeeds trivially. The peer-side response-hash verification model
//     in task.md ("extract fields from payload, compute hash, compare,
//     report to Sarathi") collapses to "hash the body you received,
//     report it."
//
// PATH A WIRE CONTRACT:
//
//   POST /bucket/artifact            body = raw canonical 20-field envelope
//   POST /insightflow_process        body = raw canonical 20-field envelope
//   POST /v1/enforce (Core post-exec) body = raw canonical 20-field envelope
//
//   Headers (all peers): 9 X-Sarathi-* propagation headers from
//     ecosystem_clients.postEnvelope. X-Sarathi-Response-Hash is the
//     authoritative value peers must reproduce.
//
//   Bucket-specific: X-Sarathi-Bucket-Parent-Hash carries the per-trace
//     chain anchor so Bucket can record it without inspecting the body.
//
// FAILURE MODEL:
//
//   - Hook runs in a goroutine; never blocks the inbound response.
//   - SARATHI_PROPAGATE_ON_INGEST=1 gate (default OFF) lets ops wire URLs
//     before turning fan-out on.
//   - Per-peer failures audited to proof_logs/peer_propagation_audit.jsonl
//     with status, hash, error code, latency.
//   - InsightFlow is "off-chain" (per existing ecosystem semantics): its
//     failure NEVER halts the chain or fails the request.
//   - Bucket failure is logged but does not retroactively fail the already-
//     sent HTTP response; the operator must check the audit log.
//
// TAG: production-propagation-hook-v15.11

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"time"
)

const (
	// EnvPropagateOnIngest is the operator opt-in flag for post-ingest fan-out.
	EnvPropagateOnIngest = "SARATHI_PROPAGATE_ON_INGEST"

	// PeerPropagationAuditLog records one row per fan-out attempt.
	PeerPropagationAuditLog = "proof_logs/peer_propagation_audit.jsonl"

	// HeaderBucketParentHash carries the per-trace chain anchor to Bucket.
	HeaderBucketParentHash = "X-Sarathi-Bucket-Parent-Hash"
)

var peerPropagationTotal uint64

// PropagationOnIngestEnabled reports whether SARATHI_PROPAGATE_ON_INGEST=1.
func PropagationOnIngestEnabled() bool {
	return strings.TrimSpace(os.Getenv(EnvPropagateOnIngest)) == "1"
}

// peerPropagationAuditRow is the JSONL shape of one fan-out result row.
// Per-peer hops are flattened so audit queries are simple grep/jq.
type peerPropagationAuditRow struct {
	Timestamp     string `json:"ts"`
	TraceID       string `json:"trace_id"`
	DecisionID    string `json:"decision_id"`
	ResponseHash  string `json:"response_hash"`
	ChainBinding  string `json:"chain_binding_hash"`
	BodyBytes     int    `json:"body_bytes"`
	BodyHash      string `json:"sarathi_outbound_body_hash"`

	BucketURL     string `json:"bucket_url,omitempty"`
	BucketStatus  int    `json:"bucket_http_status,omitempty"`
	BucketAckHash string `json:"bucket_ack_hash,omitempty"`
	BucketErr     string `json:"bucket_error,omitempty"`

	InsightURL    string `json:"insightflow_url,omitempty"`
	InsightStatus int    `json:"insightflow_http_status,omitempty"`
	InsightAck    string `json:"insightflow_ack_hash,omitempty"`
	InsightErr    string `json:"insightflow_error,omitempty"`

	CoreURL    string `json:"core_url,omitempty"`
	CoreStatus int    `json:"core_http_status,omitempty"`
	CoreAck    string `json:"core_ack_hash,omitempty"`
	CoreErr    string `json:"core_error,omitempty"`

	Notes string `json:"notes,omitempty"`
}

// firePostIngestPropagation kicks off the fan-out in a background goroutine.
// The hot path does only a nil + env-flag check; everything else runs
// asynchronously to keep handleIngestDecision's latency unchanged.
func firePostIngestPropagation(env *PropagationEnvelope) {
	if env == nil || !PropagationOnIngestEnabled() {
		return
	}
	atomic.AddUint64(&peerPropagationTotal, 1)
	go func(e *PropagationEnvelope) {
		defer func() {
			if rec := recover(); rec != nil {
				fmt.Fprintf(os.Stderr, "[propagation] panic recovered: %v\n", rec)
			}
		}()
		runPathAFanout(e)
	}(env)
}

// runPathAFanout — v15.12 — executes the WRAPPER fan-out (BucketArtifact +
// InsightFlow Schema D) via BHIVTranslatedFanOut. Each peer gets bytes in
// its own declared schema; the canonical 20-field response is embedded as
// `canonical_response_b64`. Per-peer body_hash is recorded into the
// OutboundHashStore so VerifyReceipt can apply the dual-hash gate when
// the receipt callback arrives.
//
// Despite the function name keeping "PathA" for backwards compatibility,
// this is the wrapper-path (Path B+ from the v15.11 design discussion) —
// peer schemas are preserved.
func runPathAFanout(env *PropagationEnvelope) {
	epsPtr, epsErr := LoadEcosystemEndpoints()
	row := peerPropagationAuditRow{
		Timestamp:    time.Now().UTC().Format(time.RFC3339Nano),
		TraceID:      env.TraceID(),
		DecisionID:   env.DecisionID(),
		ResponseHash: env.ResponseHash(),
		ChainBinding: env.ChainBindingHash(),
		BodyBytes:    len(env.CanonicalResponseBytes()),
		BodyHash:     env.ResponseHash(),
	}
	if epsErr != nil || epsPtr == nil {
		row.Notes = "ecosystem_endpoints_load_failed"
		if epsErr != nil {
			row.Notes = epsErr.Error()
		}
		appendPropagationAudit(&row)
		return
	}
	if isEcosystemPlaceholder(*epsPtr) {
		row.Notes = "ecosystem_endpoints_placeholder; SARATHI_*_URL env vars not set"
		appendPropagationAudit(&row)
		return
	}

	// v15.12 — per-peer body_hash recording happens inside each ecosystem
	// client call site below (postBucketArtifact / postInsightFlowShape /
	// CoreClient.Enforce + Record). The unified per-decision per-peer audit
	// trail lives at proof_logs/peer_outbound_hashes.jsonl, owned by
	// peer_outbound_hash_store.go.

	// v15.12 — Bucket + InsightFlow get peer-shaped wrappers via
	// BHIVTranslatedFanOut. Bucket gets the BucketArtifact wrapper with
	// payload.canonical_response_b64; InsightFlow Schema D carries the
	// same canonical_response_b64. Per-peer body_hash recorded into the
	// OutboundHashStore inside the postBucketArtifact / postInsightFlowShape
	// call sites.
	fanResult, fErr := BHIVTranslatedFanOut(env, *epsPtr)
	if fErr == nil && fanResult != nil {
		if fanResult.Bucket != nil {
			row.BucketURL = fanResult.Bucket.URL
			row.BucketStatus = fanResult.Bucket.HTTPStatus
			row.BucketAckHash = fanResult.Bucket.AckHash
			row.BucketErr = fanResult.Bucket.Error
		}
		if fanResult.InsightFlow != nil {
			// Surface the last InsightFlow hop outcome (typically the
			// /insightflow_process Schema D one — the wrapper carrying
			// canonical_response_b64).
			for _, h := range fanResult.InsightFlow.Hops {
				if h.Endpoint == "insightflow_process" {
					row.InsightURL = h.URL
					row.InsightStatus = h.HTTPStatus
					row.InsightAck = h.AckHash
					row.InsightErr = h.Error
					break
				}
			}
		}
	} else if fErr != nil {
		row.Notes = "bhiv_fanout: " + fErr.Error()
	}

	// In-chain: Core post-execution. Sarathi sends the raw canonical envelope
	// to /v1/enforce so Core records the post-execution result. Core's
	// receipt path verifies the raw envelope directly (no wrapper for the
	// Core post-exec hop; Core already accepts canonical bytes in v15.6).
	coreClient := NewCoreClient(epsPtr.Core)
	coreAck, cErr := coreClient.Enforce(env)
	row.CoreURL = epsPtr.Core.Enforce
	if cErr != nil {
		row.CoreErr = cErr.Error()
	}
	if coreAck != nil {
		row.CoreStatus = coreAck.Status
		row.CoreAck = coreAck.AckHash
	}
	// Record Core's outbound body_hash. Core gets the raw canonical envelope
	// so body_hash == response_hash by construction, but record it anyway
	// for symmetry — the dual-hash gate in VerifyReceipt is uniform.
	if store := ActivePeerOutboundHashStore(); store != nil {
		store.Record(OutboundHashEntry{
			DecisionID:    env.DecisionID(),
			Peer:          "core",
			TraceID:       env.TraceID(),
			ResponseHash:  env.ResponseHash(),
			BodyHash:      env.ResponseHash(),
			BodyBytes:     len(env.CanonicalResponseBytes()),
			WrapperSchema: "sarathi.response/v13.0",
		})
	}

	appendPropagationAudit(&row)
}

// isEcosystemPlaceholder detects the fail-loud DefaultEndpoints() placeholders.
func isEcosystemPlaceholder(eps EcosystemEndpoints) bool {
	return strings.Contains(eps.Bucket.ArtifactPost, "ngrok-url-not-set.local")
}

// appendPropagationAudit writes one JSONL row to PeerPropagationAuditLog.
func appendPropagationAudit(row *peerPropagationAuditRow) {
	dir := filepath.Dir(PeerPropagationAuditLog)
	if dir != "" && dir != "." {
		_ = os.MkdirAll(dir, 0o755)
	}
	raw, err := json.Marshal(row)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[propagation] WARN audit marshal: %v\n", err)
		return
	}
	raw = append(raw, '\n')
	f, err := os.OpenFile(PeerPropagationAuditLog, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[propagation] WARN audit open: %v\n", err)
		return
	}
	defer f.Close()
	_, _ = f.Write(raw)
}

// PropagationTotalCount returns the number of fan-out kicks since boot.
// Exported for metrics surfaces.
func PropagationTotalCount() uint64 {
	return atomic.LoadUint64(&peerPropagationTotal)
}
