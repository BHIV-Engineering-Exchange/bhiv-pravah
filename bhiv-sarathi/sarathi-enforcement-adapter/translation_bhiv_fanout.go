package main

// translation_bhiv_fanout.go — v15.5 Sovereign Translational Layer.
//
// Drives the production BHIV fan-out using the translation-layer shapes:
//   - POST /bucket/artifact            ← BucketArtifact v1.0 (chained parent_hash)
//   - POST /sarathi_trigger            ← InsightFlow Schema A
//   - POST /core_execute               ← InsightFlow Schema C
//   - POST /insightflow_process        ← InsightFlow Schema D
//   - POST /bucket_persist             ← InsightFlow Schema B
//
// This is an additive entry point — the existing legacy fan-out via
// MultiSystemRouter.RoutePropagation() (which sends raw canonical envelope
// bytes) remains in place for in-process tests and the live-integration
// peer simulators. Production deployments use BHIVTranslatedFanOut after the
// sealed envelope is built.
//
// Failure semantics:
//   - Bucket fan-out is in-chain — its failure halts the chain and is
//     reflected in the returned BHIVTranslatedFanOutResult.bucket field.
//   - InsightFlow fan-out is observability-only — every endpoint is attempted
//     regardless of the others' outcomes. Per-endpoint results live in
//     result.insightflow.Hops[].
//
// TAG: translation-layer

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// BHIVTranslatedFanOutResult is the consolidated result of the BHIV fan-out.
type BHIVTranslatedFanOutResult struct {
	TraceID     string                  `json:"trace_id"`
	Bucket      *BHIVBucketHop          `json:"bucket"`
	InsightFlow *InsightFlowFanoutResult `json:"insightflow"`
	StartedAt   string                  `json:"started_at"`
	FinishedAt  string                  `json:"finished_at"`
}

// BHIVBucketHop captures the outcome of the Bucket POST.
type BHIVBucketHop struct {
	URL          string `json:"url"`
	HTTPStatus   int    `json:"http_status,omitempty"`
	ArtifactID   string `json:"artifact_id,omitempty"`
	ParentHash   string `json:"parent_hash,omitempty"`
	BodyHash     string `json:"body_hash"`
	AckHash      string `json:"ack_hash,omitempty"`
	Delivered    bool   `json:"delivered"`
	Error        string `json:"error,omitempty"`
	LatencyMs    int64  `json:"latency_ms"`
}

// BHIVTranslatedFanOut runs the production BHIV fan-out for a sealed
// envelope. Returns the consolidated result; the caller decides whether to
// halt the parent operation on a Bucket failure (chain integrity).
func BHIVTranslatedFanOut(env *PropagationEnvelope, eps EcosystemEndpoints) (*BHIVTranslatedFanOutResult, error) {
	if env == nil {
		return nil, fmt.Errorf("bhiv_fanout: envelope is nil")
	}
	traceID := env.TraceID()
	if traceID == "" {
		return nil, fmt.Errorf("bhiv_fanout: envelope has empty trace_id")
	}

	res := &BHIVTranslatedFanOutResult{
		TraceID:   traceID,
		StartedAt: time.Now().UTC().Format(time.RFC3339Nano),
	}

	// Step 1: Bucket POST — in-chain. Build artifact (advances parent_hash
	// chain atomically), marshal canonical, post, parse ack.
	bucketHop := postBucketArtifact(env, eps.Bucket.ArtifactPost)
	res.Bucket = bucketHop

	// Step 2: InsightFlow fan-out — off-chain. Continues regardless of Bucket
	// success.
	ifResult, ifErr := RouteInsightFlowFanout(env, eps.InsightFlow)
	if ifErr != nil {
		// Wrap a synthetic result so the caller still sees the trace.
		ifResult = &InsightFlowFanoutResult{
			TraceID:   traceID,
			StartedAt: time.Now().UTC().Format(time.RFC3339Nano),
			ErrorDetails: []InsightFlowErrorDetail{
				{System: "InsightFlow:fanout", Issue: ifErr.Error()},
			},
			FinishedAt: time.Now().UTC().Format(time.RFC3339Nano),
		}
	}
	res.InsightFlow = ifResult
	res.FinishedAt = time.Now().UTC().Format(time.RFC3339Nano)

	return res, nil
}

// postBucketArtifact builds the BucketArtifact, advances the parent_hash
// chain, and posts to the configured Bucket endpoint. The chain advance
// happens INSIDE BuildBucketArtifact so a failure to post does NOT
// retroactively undo the chain — the next attempt for the same trace_id
// will compute against the advanced tip. This is the same trade-off the
// existing peer_bucket.go path makes (idempotent on identical bytes;
// distinct bytes for the same decision_id surface as a 409 mismatch).
func postBucketArtifact(env *PropagationEnvelope, url string) *BHIVBucketHop {
	hop := &BHIVBucketHop{URL: url}
	if strings.TrimSpace(url) == "" {
		hop.Error = "bucket_url_empty"
		return hop
	}

	start := time.Now()
	defer func() {
		hop.LatencyMs = time.Since(start).Milliseconds()
	}()

	artifact, err := BuildBucketArtifact(env)
	if err != nil {
		hop.Error = "build: " + err.Error()
		return hop
	}
	hop.ArtifactID = artifact.ArtifactID
	hop.ParentHash = artifact.ParentHash

	body, err := MarshalBucketArtifactCanonical(artifact)
	if err != nil {
		hop.Error = "canonical_marshal: " + err.Error()
		return hop
	}
	hop.BodyHash = ComputePayloadHashHex(body)

	client := &http.Client{Timeout: EcosystemClientDefaultTimeout}
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		hop.Error = "request_build: " + err.Error()
		return hop
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("ngrok-skip-browser-warning", "true")
	for k, v := range env.ToHeaderMap() {
		req.Header.Set(k, v)
	}
	req.Header.Set("X-Sarathi-Schema-Version", BucketArtifactSchemaV1)
	// v15.12 dual-hash transport-integrity header: SHA-256 of the wrapper
	// bytes Sarathi sends on the wire. Peer hashes the body it receives
	// and confirms received_body_hash == this value.
	req.Header.Set("X-Sarathi-Body-Hash", hop.BodyHash)

	// v15.12 record the minted (body_hash, response_hash) tuple in the
	// outbound store so VerifyReceipt can look it up when the peer posts
	// its receipt callback.
	if store := ActivePeerOutboundHashStore(); store != nil {
		store.Record(OutboundHashEntry{
			DecisionID:    env.DecisionID(),
			Peer:          "bucket",
			TraceID:       env.TraceID(),
			ResponseHash:  env.ResponseHash(),
			BodyHash:      hop.BodyHash,
			BodyBytes:     len(body),
			WrapperSchema: BucketArtifactSchemaV1,
		})
	}

	resp, err := client.Do(req)
	if err != nil {
		hop.Error = "post: " + err.Error()
		return hop
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	hop.HTTPStatus = resp.StatusCode

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		hop.Error = fmt.Sprintf("status=%d body=%s", resp.StatusCode,
			truncateForLog(string(respBody), 200))
		return hop
	}

	// Parse ack_hash. Bucket peers typically return both X-Sarathi-Ack-Hash
	// header and a JSON body with ack_hash; tolerate either.
	hop.AckHash = strings.TrimSpace(resp.Header.Get(HeaderAckHash))
	if hop.AckHash == "" {
		var ack struct {
			AckHash string `json:"ack_hash"`
		}
		_ = json.Unmarshal(respBody, &ack)
		hop.AckHash = strings.TrimSpace(ack.AckHash)
	}
	hop.Delivered = true
	return hop
}
