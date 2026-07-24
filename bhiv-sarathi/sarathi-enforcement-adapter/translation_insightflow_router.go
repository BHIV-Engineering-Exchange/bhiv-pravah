package main

// translation_insightflow_router.go — v15.5 Sovereign Translational Layer.
//
// Fan-out helper that posts the four shape-specific InsightFlow payloads to
// the four InsightFlow endpoints. The existing InsightFlowClient methods
// (SarathiTrigger, CoreExecute, Process, BucketPersist) all share the same
// uniform digest payload through `postEnvelope(... digest=true)`. This router
// supersedes that with shape-specific payloads.
//
// The router does NOT halt the chain on any single InsightFlow failure.
// InsightFlow is observability-only (off-chain in propagation terms), so
// failures are recorded but never propagate as PropagationStopError.
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

// InsightFlowFanoutResult records what happened at every endpoint.
type InsightFlowFanoutResult struct {
	TraceID         string                       `json:"trace_id"`
	Hops            []InsightFlowFanoutHop       `json:"hops"`
	SystemsVerified []string                     `json:"systems_verified"`
	ErrorDetails    []InsightFlowErrorDetail     `json:"error_details"`
	LossCheck       bool                         `json:"loss_check"`
	StartedAt       string                       `json:"started_at"`
	FinishedAt      string                       `json:"finished_at"`
}

// InsightFlowFanoutHop records the outcome at a single endpoint.
type InsightFlowFanoutHop struct {
	Endpoint     string `json:"endpoint"`
	URL          string `json:"url"`
	Schema       string `json:"schema"`
	HTTPStatus   int    `json:"http_status,omitempty"`
	AckHash      string `json:"ack_hash,omitempty"`
	BodyHash     string `json:"body_hash"`
	Delivered    bool   `json:"delivered"`
	Error        string `json:"error,omitempty"`
	LatencyMs    int64  `json:"latency_ms"`
}

// RouteInsightFlowFanout posts the 4 shape-specific payloads to InsightFlow.
// Each hop runs sequentially because InsightFlow's per-trace ordering matters
// for the dashboard. Failures do not halt the loop; every hop is attempted.
//
// The Process hop (Schema D) is sent LAST so it can include the loss_check
// and systems_verified observations from the preceding three hops.
func RouteInsightFlowFanout(env *PropagationEnvelope, eps InsightFlowEndpoints) (*InsightFlowFanoutResult, error) {
	if env == nil {
		return nil, fmt.Errorf("if_router: envelope is nil")
	}
	traceID := env.TraceID()
	if traceID == "" {
		return nil, fmt.Errorf("if_router: envelope has empty trace_id")
	}
	res := &InsightFlowFanoutResult{
		TraceID:   traceID,
		Hops:      make([]InsightFlowFanoutHop, 0, 4),
		StartedAt: time.Now().UTC().Format(time.RFC3339Nano),
	}

	client := &http.Client{Timeout: EcosystemClientDefaultTimeout}

	// Hop 1: /sarathi_trigger ⇒ Schema A
	if eps.SarathiTrigger != "" {
		a, err := BuildSchemaATrigger(env)
		hop := postInsightFlowShape(client, eps.SarathiTrigger, "sarathi_trigger",
			InsightFlowSchemaAVersion, a, err, env)
		res.Hops = append(res.Hops, hop)
		if hop.Delivered {
			res.SystemsVerified = append(res.SystemsVerified, "InsightFlow:sarathi_trigger")
		} else if hop.Error != "" {
			res.ErrorDetails = append(res.ErrorDetails, InsightFlowErrorDetail{
				System: "InsightFlow:sarathi_trigger", Issue: hop.Error,
			})
		}
	}

	// Hop 2: /core_execute ⇒ Schema C
	if eps.CoreExecute != "" {
		c, err := BuildSchemaCExecute(env)
		hop := postInsightFlowShape(client, eps.CoreExecute, "core_execute",
			InsightFlowSchemaCVersion, c, err, env)
		res.Hops = append(res.Hops, hop)
		if hop.Delivered {
			res.SystemsVerified = append(res.SystemsVerified, "InsightFlow:core_execute")
		} else if hop.Error != "" {
			res.ErrorDetails = append(res.ErrorDetails, InsightFlowErrorDetail{
				System: "InsightFlow:core_execute", Issue: hop.Error,
			})
		}
	}

	// Hop 3: /bucket_persist ⇒ Schema B
	if eps.BucketPersist != "" {
		b, err := BuildSchemaBPersist(env)
		hop := postInsightFlowShape(client, eps.BucketPersist, "bucket_persist",
			InsightFlowSchemaBVersion, b, err, env)
		res.Hops = append(res.Hops, hop)
		if hop.Delivered {
			res.SystemsVerified = append(res.SystemsVerified, "InsightFlow:bucket_persist")
		} else if hop.Error != "" {
			res.ErrorDetails = append(res.ErrorDetails, InsightFlowErrorDetail{
				System: "InsightFlow:bucket_persist", Issue: hop.Error,
			})
		}
	}

	// loss_check: PASS iff every attempted hop above echoed a matching
	// ack_hash. Endpoints not configured (empty URL) do not count against
	// loss_check — the operator opted out of those hops.
	res.LossCheck = computeLossCheck(res.Hops)

	// Hop 4 (last): /insightflow_process ⇒ Schema D
	if eps.InsightFlowProcess != "" {
		d, err := BuildSchemaDProcess(env, res.LossCheck, res.SystemsVerified, res.ErrorDetails)
		hop := postInsightFlowShape(client, eps.InsightFlowProcess, "insightflow_process",
			InsightFlowSchemaDVersion, d, err, env)
		res.Hops = append(res.Hops, hop)
		if hop.Delivered {
			res.SystemsVerified = append(res.SystemsVerified, "InsightFlow:insightflow_process")
		} else if hop.Error != "" {
			res.ErrorDetails = append(res.ErrorDetails, InsightFlowErrorDetail{
				System: "InsightFlow:insightflow_process", Issue: hop.Error,
			})
		}
	}

	res.FinishedAt = time.Now().UTC().Format(time.RFC3339Nano)
	return res, nil
}

// postInsightFlowShape canonicalizes the payload, POSTs to url, and parses
// the ack_hash echo. The fan-out is observability — non-2xx responses are
// recorded as undelivered but never block the rest of the loop.
func postInsightFlowShape(client *http.Client, url, endpointName, schemaVersion string,
	payload interface{}, buildErr error, env *PropagationEnvelope) InsightFlowFanoutHop {

	hop := InsightFlowFanoutHop{
		Endpoint: endpointName,
		URL:      url,
		Schema:   schemaVersion,
	}
	start := time.Now()
	defer func() {
		hop.LatencyMs = time.Since(start).Milliseconds()
	}()

	if buildErr != nil {
		hop.Error = "build_failed: " + buildErr.Error()
		return hop
	}

	body, err := MarshalInsightFlowCanonical(payload)
	if err != nil {
		hop.Error = "canonical_marshal_failed: " + err.Error()
		return hop
	}
	hop.BodyHash = ComputePayloadHashHex(body)

	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		hop.Error = "request_build: " + err.Error()
		return hop
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("ngrok-skip-browser-warning", "true")
	// Propagate the standard X-Sarathi-* headers verbatim so InsightFlow's
	// existing pivots keep working.
	if env != nil {
		for k, v := range env.ToHeaderMap() {
			req.Header.Set(k, v)
		}
	}
	req.Header.Set("X-Sarathi-Schema-Version", schemaVersion)
	// Identify the digest-only contract: every InsightFlow hop is
	// fingerprint-style (no full enforcement body, no token).
	req.Header.Set("X-Sarathi-Digest-Only", "1")
	// v15.12 dual-hash transport-integrity header — SHA-256 of the wrapper
	// bytes Sarathi sends. InsightFlow peer hashes the body it receives
	// and confirms received_body_hash == this value.
	req.Header.Set("X-Sarathi-Body-Hash", hop.BodyHash)

	// v15.12 record (body_hash, response_hash) in the outbound store ONLY
	// for the schema that carries CanonicalResponseB64 (Schema D /
	// insightflow_process). Other InsightFlow shapes (A/B/C) are pure
	// digests; their receipts aren't expected to verify
	// observed_response_hash against response_hash.
	if env != nil && endpointName == "insightflow_process" {
		if store := ActivePeerOutboundHashStore(); store != nil {
			store.Record(OutboundHashEntry{
				DecisionID:    env.DecisionID(),
				Peer:          "insightflow",
				TraceID:       env.TraceID(),
				ResponseHash:  env.ResponseHash(),
				BodyHash:      hop.BodyHash,
				BodyBytes:     len(body),
				WrapperSchema: schemaVersion,
			})
		}
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

	// Try to extract ack_hash from the JSON body. Tolerant: any echoed
	// ack_hash that matches body_hash counts as delivered. If the peer
	// doesn't return ack_hash at all, the hop is still delivered (matches
	// existing digest-hop semantics in postEnvelope).
	var ack struct {
		AckHash string `json:"ack_hash"`
	}
	_ = json.Unmarshal(respBody, &ack)
	hop.AckHash = strings.TrimSpace(ack.AckHash)
	hop.Delivered = true // 2xx ⇒ delivered. ack_hash optional.
	return hop
}

// computeLossCheck returns true iff every attempted hop reports Delivered.
func computeLossCheck(hops []InsightFlowFanoutHop) bool {
	if len(hops) == 0 {
		return false
	}
	for _, h := range hops {
		if !h.Delivered {
			return false
		}
	}
	return true
}
