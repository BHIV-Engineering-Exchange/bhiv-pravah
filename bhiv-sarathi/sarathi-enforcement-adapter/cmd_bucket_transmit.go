package main

// cmd_bucket_transmit.go — `--bucket-transmit` CLI driver.
//
// Runs ONE aligned Sarathi → Bucket exchange against a live Bucket base URL
// and prints the full evidence to the terminal (for screenshots) plus persists
// the artifacts under proof_logs/bucket/. Nothing is mocked: a representative
// enforcement decision is sealed into the BHIV envelope Bucket requires, the
// live chain head is fetched, the envelope is POSTed, the synchronous 200 is
// parsed, the artifact is confirmed via GET, and the Sarathi-owned receipt is
// built + persisted.
//
// Usage:
//
//	sarathi-enforcement-adapter.exe --bucket-transmit --bucket-url=https://<bucket>.ngrok-free.dev
//
// The base URL is the Bucket host root; the driver appends /bucket/latest-hash,
// /bucket/artifact, and /bucket/artifact/{id} itself.
//
// TAG: bucket-bhiv-align-v1

import (
	"encoding/base64"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// BucketTransmitFlag owns the process when present.
const BucketTransmitFlag = "--bucket-transmit"

// BucketURLFlag supplies the Bucket base URL.
const BucketURLFlag = "--bucket-url"

// Locked test identity for the Bucket transmission proof. Deterministic so the
// artifact_id (UUIDv5 of decision_id) is stable across runs — a re-run posts
// the SAME artifact_id, exercising Bucket's idempotency-on-artifact_id rule.
const (
	BucketTestDecisionID  = "dec-bucket-test-001"
	BucketTestTraceID     = "trace-bucket-test-001"
	BucketTestExecutionID = "exec-bucket-test-001"
	BucketTestEvaluatorID = "bhiv.sovereign.decision.prod.v1"
	BucketTestPolicyRef   = "bhiv.core.default_allow_policy@v1.0"
	BucketTestAgentID     = "gov-agent-001"
	BucketTestResourceID  = "policy-reg-001"
	BucketTestAction      = "execute"
)

// BucketTransmitMode is the parsed CLI action.
type BucketTransmitMode struct {
	Ok        bool
	BucketURL string
}

// ParseBucketTransmitArgs returns Ok=true when --bucket-transmit is present.
func ParseBucketTransmitArgs(argv []string) BucketTransmitMode {
	mode := BucketTransmitMode{}
	for i := 1; i < len(argv); i++ {
		a := argv[i]
		switch {
		case a == BucketTransmitFlag:
			mode.Ok = true
		case strings.HasPrefix(a, BucketURLFlag+"="):
			mode.BucketURL = strings.TrimSpace(a[len(BucketURLFlag)+1:])
		case a == BucketURLFlag && i+1 < len(argv):
			mode.BucketURL = strings.TrimSpace(argv[i+1])
			i++
		}
	}
	return mode
}

// buildBucketTestEnvelope assembles a representative enforcement decision sealed
// into the BHIV envelope shape Bucket requires. The canonical_response_b64 is a
// real canonicalized response object; response_hash is minted over its decoded
// bytes so the envelope is internally consistent.
func buildBucketTestEnvelope(now time.Time) (*BucketBHIVEnvelope, error) {
	inputHash := Sha256Hex([]byte("bucket-test-input|" + BucketTestTraceID + "|" + BucketTestPolicyRef))
	decisionHash := Sha256Hex([]byte("decision_hash|" + BucketTestDecisionID + "|" + inputHash))
	decisionCoreHash := Sha256Hex([]byte("decision_core_hash|" + BucketTestDecisionID))
	enforcementHash := Sha256Hex([]byte("enforcement_hash|" + BucketTestDecisionID + "|ALLOW"))
	chainBindingHash := Sha256Hex([]byte("chain_binding|" + decisionHash + "|" + enforcementHash))
	enforcedAt := now.UTC().Format(time.RFC3339Nano)
	sealedAt := now.UTC().Format(time.RFC3339Nano)

	// The sealed canonical response (representative). Canonicalized via the
	// same RFC 8785 path the production sealer uses.
	sealedResponse := map[string]interface{}{
		"schema_version":     "sarathi.enforcement.response/v1.0",
		"decision_id":        BucketTestDecisionID,
		"execution_id":       BucketTestExecutionID,
		"trace_id":           BucketTestTraceID,
		"verdict":            "ALLOW",
		"execution_state":    "EXECUTION_PERMITTED",
		"evaluator_id":       BucketTestEvaluatorID,
		"policy_reference":   BucketTestPolicyRef,
		"decision_hash":      decisionHash,
		"decision_core_hash": decisionCoreHash,
		"enforcement_hash":   enforcementHash,
		"chain_binding_hash": chainBindingHash,
		"input_hash":         inputHash,
		"agent_id":           BucketTestAgentID,
		"resource_id":        BucketTestResourceID,
		"action":             BucketTestAction,
		"obligations":        []string{},
		"enforced_at":        enforcedAt,
		"sealed_at":          sealedAt,
	}
	canonicalResponse, err := CanonicalMarshal(sealedResponse)
	if err != nil {
		return nil, fmt.Errorf("seal canonical response: %w", err)
	}
	responseHash := Sha256Hex(canonicalResponse)
	canonicalResponseB64 := base64.StdEncoding.EncodeToString(canonicalResponse)

	env := &BucketBHIVEnvelope{
		ArtifactID:     BucketArtifactIDFor(BucketTestDecisionID),
		TimestampUTC:   now.UTC().Format(time.RFC3339Nano),
		SchemaVersion:  BucketBHIVSchemaVersion,
		SourceModuleID: BucketBHIVSourceModuleID,
		ArtifactType:   BucketBHIVArtifactType,
		Payload: BucketBHIVPayload{
			DecisionID:           BucketTestDecisionID,
			TraceID:              BucketTestTraceID,
			Verdict:              "ALLOW",
			EvaluatorID:          BucketTestEvaluatorID,
			DecisionHash:         decisionHash,
			DecisionCoreHash:     decisionCoreHash,
			EnforcementHash:      enforcementHash,
			ResponseHash:         responseHash,
			ChainBindingHash:     chainBindingHash,
			PolicyReference:      BucketTestPolicyRef,
			InputHash:            inputHash,
			AgentID:              BucketTestAgentID,
			ResourceID:           BucketTestResourceID,
			Action:               BucketTestAction,
			Obligations:          []string{},
			EnforcedAt:           enforcedAt,
			SealedAt:             sealedAt,
			CanonicalResponseB64: canonicalResponseB64,
		},
	}
	return env, nil
}

// RunBucketTransmit executes the aligned exchange and returns a process exit
// code (0 = transmitted + persisted).
func RunBucketTransmit(mode BucketTransmitMode) int {
	now := time.Now().UTC()

	fmt.Println("============================================================")
	fmt.Println("  SARATHI → BUCKET  aligned transmission (BHIV envelope v1.0.0)")
	fmt.Println("============================================================")

	base := mode.BucketURL
	if base == "" {
		base = strings.TrimSpace(os.Getenv(EnvBucketArtifactPostURL))
		// Allow either a full /bucket/artifact URL or a base host; normalise to base.
		base = strings.TrimSuffix(strings.TrimRight(base, "/"), "/bucket/artifact")
	}
	if base == "" {
		fmt.Fprintln(os.Stderr, "FATAL: no Bucket URL. Pass --bucket-url=https://<bucket-host> or set SARATHI_BUCKET_ARTIFACT_POST_URL")
		return 1
	}
	fmt.Printf("  bucket base:  %s\n", base)

	// Point the custody-receipt signer at the persistent enforcement key when
	// present, WITHOUT clobbering an operator override. The receipt is signed
	// under Sarathi's enforcement identity (BUCKET-SARATHI-001 Step 5).
	if strings.TrimSpace(os.Getenv(EnvSarathiEnforcementPrivPath)) == "" {
		persistentKey := filepath.Join("live", "keys", "sarathi_enforcement", "issuer-priv.hex")
		if _, statErr := os.Stat(persistentKey); statErr == nil {
			os.Setenv(EnvSarathiEnforcementPrivPath, persistentKey)
		}
	}

	env, err := buildBucketTestEnvelope(now)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: build envelope: %v\n", err)
		return 1
	}
	fmt.Printf("  artifact_id:  %s   (UUIDv5 of decision_id — stable on retry)\n", env.ArtifactID)
	fmt.Printf("  decision_id:  %s\n", env.Payload.DecisionID)
	fmt.Printf("  trace_id:     %s\n", env.Payload.TraceID)
	fmt.Printf("  verdict:      %s\n", env.Payload.Verdict)
	fmt.Println()

	httpc := &http.Client{Timeout: EcosystemClientDefaultTimeout}

	fmt.Println("  [1/4] GET /bucket/latest-hash (chain head) ...")
	res, terr := TransmitToBucket(httpc, base, env, BucketTestExecutionID, now)

	// Print whatever we resolved, even on partial failure.
	fmt.Printf("        parent_hash used: %q\n", res.ParentHashUsed)
	fmt.Printf("  [2/4] minted body_hash:     %s\n", res.MintedBodyHash)
	fmt.Printf("        minted response_hash: %s\n", res.MintedResponseHash)
	fmt.Printf("  [3/4] POST /bucket/artifact -> HTTP %d\n", res.HTTPStatus)
	if res.BucketResponse != nil {
		fmt.Printf("        bucket success:    %v\n", res.BucketResponse.Success)
		fmt.Printf("        bucket artifact_id:%s\n", res.BucketResponse.ArtifactID)
		fmt.Printf("        bucket hash:       %s\n", res.BucketResponse.Hash)
		fmt.Printf("        bucket parent_hash:%s\n", res.BucketResponse.ParentHash)
		fmt.Printf("        storage_type:      %s\n", res.BucketResponse.StorageType)
		fmt.Printf("        bucket_hash==minted_body_hash: %v\n", res.BucketHashMatch)
	}
	fmt.Println("  [4/4] GET /bucket/artifact/{id} read-back verification (Sarathi-owned):")
	if rb := res.ReadBack; rb != nil {
		fmt.Printf("        fetched:              %v\n", rb.Fetched)
		fmt.Printf("        trace_id match:       %v\n", rb.TraceIDMatch)
		fmt.Printf("        decision_id match:    %v\n", rb.DecisionIDMatch)
		fmt.Printf("        canonical_b64 match:  %v\n", rb.CanonicalB64Match)
		fmt.Printf("        response_hash match:  %v\n", rb.ResponseHashMatch)
		if rb.ComputeHashChecked {
			fmt.Printf("        compute-hash match:   %v\n", rb.ComputeHashMatch)
		} else {
			fmt.Printf("        compute-hash:         (endpoint not offered — skipped)\n")
		}
		fmt.Printf("        chain_verified:       %v\n", rb.ChainVerified)
		fmt.Printf("        ALL VERIFIED:         %v\n", rb.AllVerified)
		if rb.Note != "" {
			fmt.Printf("        note: %s\n", rb.Note)
		}
	}
	fmt.Println()

	path, perr := PersistBucketTransmit(res)
	if perr == nil {
		fmt.Printf("  proof artifact -> %s\n", path)
	} else {
		fmt.Fprintf(os.Stderr, "  WARN: persist failed: %v\n", perr)
	}
	if r := res.Receipt; r != nil {
		signed := "yes"
		if r.ReceiptSignature == "" {
			signed = "NO (signer unavailable)"
		}
		fmt.Println("  Sarathi custody receipt (Sarathi-owned, Sarathi-signed):")
		fmt.Printf("        schema:            %s\n", r.SchemaVersion)
		fmt.Printf("        decision_id:       %s\n", r.DecisionID)
		fmt.Printf("        bucket_artifact_id:%s\n", r.BucketArtifactID)
		fmt.Printf("        bucket_hash:       %s\n", r.BucketHash)
		fmt.Printf("        read_back_verified:%v\n", r.ReadBackVerified)
		fmt.Printf("        signed:            %s (key_id=%s)\n", signed, r.KeyID)
	}
	fmt.Println("------------------------------------------------------------")

	if terr != nil {
		fmt.Printf("  RESULT: NOT TRANSMITTED — %s\n", res.Note)
		fmt.Println("============================================================")
		return 1
	}
	fmt.Printf("  RESULT: TRANSMITTED — %s\n", res.Note)
	fmt.Println("  SARATHI → BUCKET: SUCCESS")
	fmt.Println("============================================================")
	return 0
}
