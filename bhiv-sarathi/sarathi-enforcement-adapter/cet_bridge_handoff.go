package main

// cet_bridge_handoff.go — Sarathi -> Bridge handoff artifact for the TANTRA
// convergence chain.
//
// In the convergence chain (Core -> CET -> Sarathi -> Bridge -> Runtime ->
// InsightFlow -> Bucket) the hop AFTER Sarathi is Bridge. Bridge validates the
// contract, the enforcement / capability token, the bucket reference, and the
// hash continuity, then forwards to Runtime for execution.
//
// This file builds the EXACT outbound contract Sarathi prepares for that hop:
// the locked identity, the explicit enforcement decision, the capability-token
// reference Bridge will verify, the X-Sarathi-* headers Bridge will read, and
// the continuity hashes Bridge re-checks.
//
// TRANSMISSION HONESTY:
//   This artifact carries an explicit `transmission_status`. The builder NEVER
//   marks a handoff as transmitted on its own — only a real, acknowledged POST
//   to a registered Bridge ingress URL may set TRANSMITTED. Until the Bridge
//   endpoint + key registration are provisioned out-of-band, the status is
//   PREPARED_NOT_TRANSMITTED. Sarathi does not claim to have forwarded a chain
//   it has not actually forwarded.
//
// TAG: tantra-convergence-v1

import (
	"fmt"
	"path/filepath"
	"time"
)

// CETBridgeHandoffLog is the append-only JSONL of every prepared handoff.
const CETBridgeHandoffLog = "proof_logs/tantra_convergence/sarathi_bridge_handoffs.jsonl"

// Handoff transmission states.
const (
	// HandoffPreparedNotTransmitted — Sarathi built the handoff and it is ready,
	// but no acknowledged POST to a registered Bridge ingress has occurred.
	HandoffPreparedNotTransmitted = "PREPARED_NOT_TRANSMITTED"
	// HandoffTransmitted — set ONLY after a real Bridge ingress ACK is recorded.
	HandoffTransmitted = "TRANSMITTED"
)

// CETBridgeHandoffHeaders is the X-Sarathi-* header set Sarathi sends on the
// Sarathi -> Bridge hop. Bridge reads these and re-checks them against the
// body.
type CETBridgeHandoffHeaders struct {
	TraceID         string `json:"X-Sarathi-Trace-ID"`
	ExecutionID     string `json:"X-Sarathi-Execution-ID"`
	DecisionID      string `json:"X-Sarathi-Decision-ID"`
	CETHash         string `json:"X-Sarathi-CET-Hash"`
	BucketKey       string `json:"X-Sarathi-Bucket-Key"`
	SealHash        string `json:"X-Sarathi-SumScript-Seal"`
	SchemaVersion   string `json:"X-Sarathi-Schema-Version"`
	ContractVersion string `json:"X-Sarathi-Contract-Version"`
}

// CETBridgeHandoffArtifact is the outbound Sarathi -> Bridge contract.
type CETBridgeHandoffArtifact struct {
	SystemName      string `json:"system_name"`
	ArtifactType    string `json:"artifact_type"`
	Boundary        string `json:"boundary"`
	SchemaVersion   string `json:"schema_version"`
	ContractVersion string `json:"contract_version"`
	ExecutionID     string `json:"execution_id"`
	TraceID         string `json:"trace_id"`
	CETHash         string `json:"cet_hash"`
	BucketKey       string `json:"bucket_key"`
	Decision        string `json:"decision"`

	// EnforcementTokenReference is the capability reference Bridge verifies.
	EnforcementTokenReference string `json:"enforcement_token_reference"`
	// CapabilityTokenJWT is the live capability JWT (compact RFC 7519) when a
	// JWT authority was available at build time; empty otherwise.
	CapabilityTokenJWT string `json:"capability_token_jwt,omitempty"`
	// CapabilityTokenKID is the JWKS key id Bridge resolves to verify the JWT.
	CapabilityTokenKID string `json:"capability_token_kid,omitempty"`

	// HashContinuity is the set of hashes Bridge re-checks: the cet_hash MUST
	// match what InsightFlow/Bucket later observe; the seal proves the
	// SUM-SCRIPT was not mutated at the Sarathi boundary.
	HashContinuity CETBridgeHashContinuity `json:"hash_continuity"`

	// Headers is the X-Sarathi-* set sent on the hop.
	Headers CETBridgeHandoffHeaders `json:"headers"`

	// TransmissionStatus — PREPARED_NOT_TRANSMITTED until a real Bridge ingress
	// ACK is recorded.
	TransmissionStatus string `json:"transmission_status"`
	// BridgeIngressURL is the configured Bridge ingress (empty when unprovisioned).
	BridgeIngressURL string `json:"bridge_ingress_url"`
	// TransmissionNote explains the status in plain language.
	TransmissionNote string `json:"transmission_note"`

	Provenance   string `json:"provenance"`
	TimestampUTC string `json:"timestamp_utc"`
}

// CETBridgeHashContinuity is the continuity-hash block Bridge re-checks.
type CETBridgeHashContinuity struct {
	CETHashPreserved     bool   `json:"cet_hash_preserved"`
	TraceIDPreserved     bool   `json:"trace_id_preserved"`
	ExecutionIDPreserved bool   `json:"execution_id_preserved"`
	SarathiSealHash      string `json:"sarathi_seal_hash"`
}

// BuildBridgeHandoffArtifact assembles the Sarathi -> Bridge handoff from a
// successful boundary verification, the enforcement token reference, and an
// optional minted capability JWT.
//
// bridgeIngressURL is the configured Bridge ingress; pass "" when no Bridge
// endpoint has been provisioned. The builder ALWAYS sets
// PREPARED_NOT_TRANSMITTED — transmission status is only ever advanced to
// TRANSMITTED by a real, acknowledged POST to a registered Bridge ingress.
// Sarathi never self-certifies a forward it did not actually perform.
func BuildBridgeHandoffArtifact(
	res *CETVerifierResult,
	enforcementTokenReference string,
	capabilityJWT string,
	capabilityKID string,
	bridgeIngressURL string,
	now time.Time,
) *CETBridgeHandoffArtifact {
	s := res.SumScript
	decisionID := ""
	if res.InnerResult != nil && res.InnerResult.Decision != nil {
		decisionID = res.InnerResult.Decision.DecisionID
	}

	note := "Handoff artifact built and ready. Not transmitted: no acknowledged POST to a registered Bridge ingress has occurred. " +
		"Provide the Bridge ingress URL + Ed25519/JWKS key registration out-of-band to enable live transmission."
	if bridgeIngressURL != "" {
		note = "Handoff artifact built and ready. Bridge ingress URL is configured but no acknowledged POST has been recorded for this chain yet."
	}

	return &CETBridgeHandoffArtifact{
		SystemName:                "Sarathi",
		ArtifactType:              "bridge_handoff",
		Boundary:                  "Sarathi->Bridge",
		SchemaVersion:             s.SchemaVersion,
		ContractVersion:           s.ContractVersion,
		ExecutionID:               s.ExecutionID,
		TraceID:                   s.TraceID,
		CETHash:                   s.CETHash,
		BucketKey:                 s.BucketKey,
		Decision:                  string(res.Decision),
		EnforcementTokenReference: enforcementTokenReference,
		CapabilityTokenJWT:        capabilityJWT,
		CapabilityTokenKID:        capabilityKID,
		HashContinuity: CETBridgeHashContinuity{
			CETHashPreserved:     true,
			TraceIDPreserved:     true,
			ExecutionIDPreserved: true,
			SarathiSealHash:      res.SealHash,
		},
		Headers: CETBridgeHandoffHeaders{
			TraceID:         s.TraceID,
			ExecutionID:     s.ExecutionID,
			DecisionID:      decisionID,
			CETHash:         s.CETHash,
			BucketKey:       s.BucketKey,
			SealHash:        res.SealHash,
			SchemaVersion:   s.SchemaVersion,
			ContractVersion: s.ContractVersion,
		},
		TransmissionStatus: HandoffPreparedNotTransmitted,
		BridgeIngressURL:   bridgeIngressURL,
		TransmissionNote:   note,
		Provenance:         CETArtifactProvenance,
		TimestampUTC:       now.UTC().Format(time.RFC3339Nano),
	}
}

// PersistBridgeHandoffArtifact appends + writes a standalone handoff file.
func PersistBridgeHandoffArtifact(a *CETBridgeHandoffArtifact) (string, error) {
	if err := cetAppendJSONLine(CETBridgeHandoffLog, a); err != nil {
		return "", err
	}
	standalone := filepath.Join(CETArtifactDir, fmt.Sprintf("bridge_handoff_%s.json", safeFileToken(a.ExecutionID)))
	if err := writeIndentedJSON(standalone, a); err != nil {
		return "", err
	}
	return standalone, nil
}
