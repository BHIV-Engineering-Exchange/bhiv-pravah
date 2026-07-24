package main

// translation_insightflow.go — v15.5 Sovereign Translational Layer.
//
// Four shape-specific builders for the four InsightFlow POST endpoints. Each
// endpoint speaks a different schema; this file is the single place where
// fields are projected from the PropagationEnvelope into the right shape.
//
// Mapping (locked by user approval, see plan):
//   POST /sarathi_trigger     ⇒ Schema A (start-of-trace request envelope)
//   POST /core_execute        ⇒ Schema C (multi-hop tracking)
//   POST /insightflow_process ⇒ Schema D (PASS|FAIL + checks + run_metrics)
//   POST /bucket_persist      ⇒ Schema B (smallest fingerprint)
//   GET  /bucket/verify/{tid} ⇒ Schema D (read; same shape as process)
//
// TAG: translation-layer

import (
	"fmt"
	"time"
)

// BuildSchemaATrigger projects an envelope into the /sarathi_trigger shape.
// Schema A carries the request envelope so InsightFlow can hydrate the trace
// without an extra round trip.
func BuildSchemaATrigger(env *PropagationEnvelope) (*InsightFlowSchemaA, error) {
	if env == nil {
		return nil, fmt.Errorf("insightflow_a: envelope is nil")
	}
	if env.TraceID() == "" {
		return nil, fmt.Errorf("insightflow_a: envelope has empty trace_id")
	}
	priority := mapVerdictPriority(env.Verdict())
	return &InsightFlowSchemaA{
		TraceID:      env.TraceID(),
		Timestamp:    time.Now().UTC().Format(time.RFC3339Nano),
		SourceSystem: "Sarathi",
		EventType:    "sarathi_trigger",
		Payload: InsightFlowSchemaAPayload{
			RequestID: env.CorrelationID(),
			UserID:    SovereignBHIVCoreEvaluatorID,
			Query:     "execute " + SovereignBHIVCoreEvaluatorID,
			Data: map[string]interface{}{
				"decision_id":      env.DecisionID(),
				"verdict":          env.Verdict(),
				"decision_hash":    env.DecisionHash(),
				"response_hash":    env.ResponseHash(),
				"enforcement_hash": env.EnforcementHash(),
			},
			Metadata: InsightFlowSchemaAMeta{
				Priority: priority,
				Channel:  "api",
				Version:  InsightFlowSchemaAVersion,
			},
		},
	}, nil
}

// BuildSchemaBPersist projects an envelope into the /bucket_persist shape.
// Smallest fingerprint — observability only.
func BuildSchemaBPersist(env *PropagationEnvelope) (*InsightFlowSchemaB, error) {
	if env == nil {
		return nil, fmt.Errorf("insightflow_b: envelope is nil")
	}
	if env.TraceID() == "" {
		return nil, fmt.Errorf("insightflow_b: envelope has empty trace_id")
	}
	return &InsightFlowSchemaB{
		TraceID:     env.TraceID(),
		PayloadHash: env.ResponseHash(),
		Timestamp:   time.Now().UTC().Format(time.RFC3339Nano),
		SystemTag:   "Sarathi",
	}, nil
}

// BuildSchemaCExecute projects an envelope into the /core_execute shape.
// Schema C carries multi-hop metadata (origin/current/sequence/hop_count).
// event_sequence and hop_count are advanced through the global hop counter
// store.
func BuildSchemaCExecute(env *PropagationEnvelope) (*InsightFlowSchemaC, error) {
	if env == nil {
		return nil, fmt.Errorf("insightflow_c: envelope is nil")
	}
	traceID := env.TraceID()
	if traceID == "" {
		return nil, fmt.Errorf("insightflow_c: envelope has empty trace_id")
	}
	seq, err := globalHopCounter.Next(traceID)
	if err != nil {
		return nil, fmt.Errorf("insightflow_c: hop counter: %w", err)
	}
	return &InsightFlowSchemaC{
		TraceID:       traceID,
		OriginSystem:  "Sarathi",
		CurrentSystem: "Core",
		EventSequence: seq,
		Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
		Payload: InsightFlowSchemaCPayload{
			RequestID: env.CorrelationID(),
			UserID:    SovereignBHIVCoreEvaluatorID,
			Query:     "execute " + SovereignBHIVCoreEvaluatorID,
			Data: map[string]interface{}{
				"decision_id":   env.DecisionID(),
				"verdict":       env.Verdict(),
				"decision_hash": env.DecisionHash(),
			},
		},
		TraceMetadata: InsightFlowSchemaCTraceMeta{
			PayloadHash:   env.ResponseHash(),
			ParentTraceID: "",
			HopCount:      seq,
		},
	}, nil
}

// BuildSchemaDProcess projects an envelope into the /insightflow_process
// shape (also returned for GET /bucket/verify/{trace_id}). Verification
// status is PASS iff all three checks pass.
//
// Checks evaluated:
//   - mutation_check: response_hash == sha256(canonicalResponseBytes) (always
//     true for a freshly-sealed envelope; false if memory tampering occurs)
//   - loss_check: passed in by the caller (true iff every fan-out hop echoed
//     a matching ack_hash)
//   - order_check: PropagationEnvelope.VerifySelf() succeeds (chain-binding
//     hash recomputes)
//
// systemsVerified is the list of peers whose ack_hash echoed correctly. The
// caller assembles it from the fan-out result.
func BuildSchemaDProcess(env *PropagationEnvelope, lossCheck bool, systemsVerified []string, errorDetails []InsightFlowErrorDetail) (*InsightFlowSchemaD, error) {
	if env == nil {
		return nil, fmt.Errorf("insightflow_d: envelope is nil")
	}
	traceID := env.TraceID()
	if traceID == "" {
		return nil, fmt.Errorf("insightflow_d: envelope has empty trace_id")
	}

	// Mutation check: re-hash the canonical bytes and compare to stored
	// response_hash. This is the full INV-PROP-01 check executed in-process.
	canonical := env.CanonicalResponseBytes()
	mutationOK := ComputePayloadHashHex(canonical) == env.ResponseHash()

	// Order check: chain-binding self-verification. VerifySelf() also
	// re-hashes ingest bytes and the response — it is the strongest local
	// integrity check available.
	orderOK := env.VerifySelf() == nil

	status := "PASS"
	if !mutationOK || !lossCheck || !orderOK {
		status = "FAIL"
	}

	if systemsVerified == nil {
		systemsVerified = []string{}
	}
	if errorDetails == nil {
		errorDetails = []InsightFlowErrorDetail{}
	}

	// Run metrics: 1 run, 1 success or failure. Aggregation happens on the
	// InsightFlow side; per-event totals just reflect this one event.
	success, failure := 0, 0
	if status == "PASS" {
		success = 1
	} else {
		failure = 1
	}

	return &InsightFlowSchemaD{
		TraceID:         traceID,
		Status:          status,
		Checks:          InsightFlowSchemaDChecks{
			MutationCheck: mutationOK,
			LossCheck:     lossCheck,
			OrderCheck:    orderOK,
		},
		SystemsVerified: systemsVerified,
		ErrorDetails:    errorDetails,
		// v15.12 — additive carrier for the verbatim canonical 20-field
		// response so InsightFlow can compute observed_response_hash for
		// the dual-hash receipt callback.
		DecisionID:           env.DecisionID(),
		ResponseHash:         env.ResponseHash(),
		CanonicalResponseB64: encodeCanonicalResponseB64(env.CanonicalResponseBytes()),
		RunMetrics: InsightFlowSchemaDMetrics{
			TotalRuns: 1,
			Success:   success,
			Failure:   failure,
		},
	}, nil
}

// MarshalInsightFlowCanonical returns canonical bytes for any of the four
// schemas. Used by the fan-out router.
func MarshalInsightFlowCanonical(v interface{}) ([]byte, error) {
	if v == nil {
		return nil, fmt.Errorf("insightflow: payload is nil")
	}
	return CanonicalMarshal(v)
}

// mapVerdictPriority maps an enforcement verdict to an InsightFlow priority
// label. Documented heuristic: ESCALATE -> high (operator attention),
// DENY -> medium (audit attention), ALLOW -> low (routine).
func mapVerdictPriority(verdict string) string {
	switch verdict {
	case "ESCALATE":
		return "high"
	case "DENY":
		return "medium"
	default:
		return "low"
	}
}
