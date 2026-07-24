package main

// translation_bucket_artifact.go — v15.5 Sovereign Translational Layer.
//
// Builds the BHIV-spec BucketArtifact from a Sarathi enforcement result. The
// artifact is content-addressed (artifact_id = sha256(canonical(payload))) and
// chained per trace_id via parent_hash. The fan-out wraps the
// PropagationEnvelope's canonical response bytes inside a BucketArtifact body
// before posting to /bucket/artifact, so downstream consumers receive the
// BHIV envelope shape.
//
// TAG: translation-layer

import (
	"fmt"
	"time"
)

// BuildBucketArtifact assembles a BucketArtifact from the sealed envelope.
// The chain is advanced ATOMICALLY: parent_hash is read, the artifact_id is
// computed inside the per-trace lock, and the new tip_hash is committed
// before this function returns. If two fan-outs race for the same trace_id,
// they serialize through the per-trace mutex in ParentHashStore.
//
// The verdict-bearing payload values come from the PropagationEnvelope so the
// builder never inspects the canonical response bytes directly. This keeps
// the bucket schema independent of the Sarathi response schema's evolution.
func BuildBucketArtifact(env *PropagationEnvelope) (*BucketArtifact, error) {
	if env == nil {
		return nil, fmt.Errorf("bucket_artifact: envelope is nil")
	}
	traceID := env.TraceID()
	if traceID == "" {
		return nil, fmt.Errorf("bucket_artifact: envelope has empty trace_id")
	}

	payload := BucketArtifactPayload{
		DecisionID:       env.DecisionID(),
		TraceID:          traceID,
		Verdict:          env.Verdict(),
		EvaluatorID:      SovereignBHIVCoreEvaluatorID,
		DecisionHash:     env.DecisionHash(),
		DecisionCoreHash: env.DecisionCoreHash(),
		EnforcementHash:  env.EnforcementHash(),
		ResponseHash:     env.ResponseHash(),
		ChainBindingHash: env.ChainBindingHash(),
		AgentID:          SovereignBHIVCoreEvaluatorID,
		ResourceID:       SovereignBHIVCoreEvaluatorID,
		Action:           "execute",
		Obligations:      []string{},
		EnforcedAt:       env.EnforcedAt(),
		SealedAt:         env.SealedAt(),
		// v15.12 — embed verbatim canonical bytes so the peer can compute
		// observed_response_hash = sha256(base64_decode(canonical_response_b64))
		// and compare to ResponseHash above. Decision integrity proof.
		CanonicalResponseB64: encodeCanonicalResponseB64(env.CanonicalResponseBytes()),
	}

	// Pull policy_reference / input_hash from the canonical response if the
	// builder wires them through metadata. PropagationEnvelope does not surface
	// metadata directly; the values live inside the canonical response bytes.
	// We leave them empty here unless callers populate via SetSovereignContext.
	// The Sovereign translator passes these via metadata on the ExternalDecision
	// which becomes part of the canonical bytes — they are recoverable by
	// re-parsing the canonical bytes at audit time.

	// Use envelope's sealed-at timestamp as the artifact wall-clock, falling
	// back to now() when sealed_at is absent. Bucket consumers ORDER artifacts
	// by timestamp_utc within a trace_id; ties are broken by parent_hash.
	tsUTC := env.SealedAt()
	if tsUTC == "" {
		tsUTC = time.Now().UTC().Format(time.RFC3339Nano)
	}

	// Atomic chain advance: lookup parent, compute artifact_id, append tip.
	parentHash, artifactID, count, err := globalParentHashStore.LookupAndAppend(traceID,
		func(parent string, isGenesis bool) (string, error) {
			candidate := &BucketArtifact{
				TimestampUTC:   tsUTC,
				SchemaVersion:  BucketArtifactSchemaV1,
				SourceModuleID: BucketSourceModuleID,
				ArtifactType:   BucketArtifactTypeDecide,
				ParentHash:     parent,
				Payload:        payload,
			}
			id, herr := CanonicalHashOfStruct(candidate.Payload)
			if herr != nil {
				return "", fmt.Errorf("bucket_artifact: payload hash: %w", herr)
			}
			return id, nil
		},
	)
	if err != nil {
		return nil, fmt.Errorf("bucket_artifact: chain advance failed: %w", err)
	}

	// Build the final artifact with the committed parent_hash and artifact_id.
	out := &BucketArtifact{
		ArtifactID:     artifactID,
		TimestampUTC:   tsUTC,
		SchemaVersion:  BucketArtifactSchemaV1,
		SourceModuleID: BucketSourceModuleID,
		ArtifactType:   BucketArtifactTypeDecide,
		ParentHash:     parentHash,
		Payload:        payload,
	}
	_ = count // exposed via --verify-bucket-chain CLI; not needed in caller.
	return out, nil
}

// MarshalBucketArtifactCanonical returns the canonical bytes of the artifact
// for posting to /bucket/artifact. Callers use these bytes verbatim.
func MarshalBucketArtifactCanonical(a *BucketArtifact) ([]byte, error) {
	if a == nil {
		return nil, fmt.Errorf("bucket_artifact: artifact is nil")
	}
	return CanonicalMarshal(a)
}
