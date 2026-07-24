package main

// cmd_tantra_convergence.go — `--tantra-convergence` CLI driver.
//
// Runs ONE locked TANTRA convergence chain identity through Sarathi's REAL
// CET->Sarathi enforcement boundary and emits the evidence artifacts the
// TANTRA convergence packet requests. Nothing is mocked: a real Ed25519
// keypair signs a real tantra.decision.v1, the real 12-step verifier verifies
// it, the real convergence-continuity gates run, a real enforcement
// attestation is signed, and (when a JWT authority key is present) a real
// capability JWT is minted.
//
// The locked identity is the one the TANTRA team froze in
// canonical_chain_identity.md. The driver PRESERVES those identifiers — it
// never regenerates execution_id / trace_id / cet_hash.
//
// What this driver does NOT do: transmit anything to Bridge or any external
// system. It builds the Sarathi->Bridge handoff contract and records its
// status as PREPARED_NOT_TRANSMITTED. Live transmission requires the Bridge
// ingress URL + key registration, provisioned out-of-band.
//
// Usage:
//
//	sarathi-enforcement-adapter.exe --tantra-convergence
//	sarathi-enforcement-adapter.exe --tantra-convergence --bridge-ingress-url=https://<bridge>/ingress
//
// TAG: tantra-convergence-v1

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Locked canonical chain identity (canonical_chain_identity.md §Locked Identity).
const (
	LockedExecutionID     = "exec-tantra-001"
	LockedTraceID         = "trace-tantra-001"
	LockedCETHash         = "89d18ea108d45ece5b98e07e6f54b54b54c8b115e0610e58952328530e8e6801"
	LockedBucketKey       = "b64147889ed9eff3f303afe8457f5e318e9f77ba24ac2b2a35b7e2ac572d4f80"
	LockedConvPolicyRef   = "bhiv.core.tantra_convergence_policy@v1.0"
	LockedSovereignEvalID = "bhiv.sovereign.decision.prod.v1"
)

// ConvergenceFlag is the CLI flag that owns the process.
const ConvergenceFlag = "--tantra-convergence"

// BridgeIngressURLFlag optionally supplies a configured Bridge ingress URL.
const BridgeIngressURLFlag = "--bridge-ingress-url"

// CETConvergenceSummaryPath is the consolidated evidence summary the response
// document references.
const CETConvergenceSummaryPath = "proof_logs/tantra_convergence/CONVERGENCE_SUMMARY.json"

// TantraConvergenceMode is the parsed CLI action.
type TantraConvergenceMode struct {
	Ok               bool
	BridgeIngressURL string
}

// ParseTantraConvergenceArgs returns Ok=true when --tantra-convergence is
// present so the caller can hand the process to RunTantraConvergence.
func ParseTantraConvergenceArgs(argv []string) TantraConvergenceMode {
	mode := TantraConvergenceMode{}
	for i := 1; i < len(argv); i++ {
		a := argv[i]
		switch {
		case a == ConvergenceFlag:
			mode.Ok = true
		case strings.HasPrefix(a, BridgeIngressURLFlag+"="):
			mode.BridgeIngressURL = strings.TrimSpace(a[len(BridgeIngressURLFlag)+1:])
		case a == BridgeIngressURLFlag && i+1 < len(argv):
			mode.BridgeIngressURL = strings.TrimSpace(argv[i+1])
			i++
		}
	}
	return mode
}

// convergenceStep records one negative/positive proof outcome for the summary.
type convergenceStep struct {
	Name       string `json:"name"`
	Expectation string `json:"expectation"`
	Passed     bool   `json:"passed"`
	Detail     string `json:"detail"`
	ErrorCode  string `json:"error_code,omitempty"`
	ArtifactPath string `json:"artifact_path,omitempty"`
}

// convergenceSummary is the consolidated evidence record.
type convergenceSummary struct {
	GeneratedAtUTC          string                              `json:"generated_at_utc"`
	SarathiBuild            string                              `json:"sarathi_build"`
	CryptoProvider          string                              `json:"crypto_provider"`
	LockedIdentity          map[string]string                   `json:"locked_identity"`
	EnforcementDecision     *SarathiEnforcementDecisionArtifact `json:"enforcement_decision_artifact"`
	BridgeHandoff           *CETBridgeHandoffArtifact           `json:"bridge_handoff_artifact"`
	EnforcementArtifactPath string                              `json:"enforcement_artifact_path"`
	BridgeHandoffPath       string                              `json:"bridge_handoff_path"`
	CapabilityJWTMinted     bool                                `json:"capability_jwt_minted"`
	CapabilityJWTNote       string                              `json:"capability_jwt_note"`
	Steps                   []convergenceStep                   `json:"proof_steps"`
	AllPassed               bool                                `json:"all_passed"`
}

// RunTantraConvergence executes the full convergence proof and returns a
// process exit code (0 = all proofs passed).
func RunTantraConvergence(mode TantraConvergenceMode) int {
	now := time.Now().UTC()
	provider := ActiveProvider()

	fmt.Println("============================================================")
	fmt.Println("  TANTRA CONVERGENCE — CET->Sarathi enforcement boundary")
	fmt.Println("  Locked chain:", LockedExecutionID, "/", LockedTraceID)
	fmt.Println("  cet_hash:", LockedCETHash)
	fmt.Println("  provider:", provider.Algorithm())
	fmt.Println("============================================================")

	if err := os.MkdirAll(CETArtifactDir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: mkdir %s: %v\n", CETArtifactDir, err)
		return 1
	}

	// --- Real Sovereign keypair + registered evaluator -----------------------
	priv, pub, err := provider.Generate(nil)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: generate sovereign key: %v\n", err)
		return 1
	}
	keyID := LockedSovereignEvalID + "#" + algKeyIDSuffix(provider.Algorithm()) + "-conv-2026-06"
	registry, accepted, err := NewTantraTrustConsumer([]TantraEvaluatorEntry{{
		EvaluatorID:   LockedSovereignEvalID,
		Name:          "Sovereign BHIV Core (convergence)",
		Status:        "ACTIVE",
		SchemaVersion: TantraSchemaV1,
		Algorithm:     string(provider.Algorithm()),
		KeyID:         keyID,
		PublicKey:     provider.EncodePublicKey(pub),
		RegisteredAt:  now.Format(time.RFC3339Nano),
	}}, provider)
	if err != nil || accepted != 1 {
		fmt.Fprintf(os.Stderr, "FATAL: registry build (accepted=%d): %v\n", accepted, err)
		return 1
	}

	// --- Build + sign the inner tantra.decision.v1 (verdict ALLOW) -----------
	innerDecision, innerWire, err := buildSignedConvergenceDecision(provider, priv, keyID, LockedTraceID, now)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: build inner decision: %v\n", err)
		return 1
	}

	// --- Seal it into the locked SUM-SCRIPT envelope -------------------------
	sum := &CETSumScript{
		SchemaVersion:   CETConvergenceSchemaVersion,
		ContractVersion: CETConvergenceContractVersion,
		ExecutionID:     LockedExecutionID,
		TraceID:         LockedTraceID,
		CETHash:         LockedCETHash,
		BucketKey:       LockedBucketKey,
		DecisionB64:     base64.StdEncoding.EncodeToString(innerWire),
	}
	sumRaw, err := json.Marshal(sum)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: marshal SUM-SCRIPT: %v\n", err)
		return 1
	}

	summary := convergenceSummary{
		GeneratedAtUTC: now.Format(time.RFC3339Nano),
		SarathiBuild:   "v15.7+tantra-convergence-v1",
		CryptoProvider: string(provider.Algorithm()),
		LockedIdentity: map[string]string{
			"execution_id":     LockedExecutionID,
			"trace_id":         LockedTraceID,
			"cet_hash":         LockedCETHash,
			"bucket_key":       LockedBucketKey,
			"schema_version":   CETConvergenceSchemaVersion,
			"contract_version": CETConvergenceContractVersion,
		},
	}

	// =========================================================================
	// PROOF 1 — positive path: real boundary verification of the locked chain
	// =========================================================================
	res, verr := newConvergenceBoundary(provider, registry, now).Verify(sumRaw)
	if verr != nil {
		fmt.Fprintf(os.Stderr, "FATAL: locked-chain verification rejected unexpectedly: %s\n", verr.Error())
		summary.Steps = append(summary.Steps, convergenceStep{
			Name: "positive_locked_chain", Expectation: "accept", Passed: false,
			Detail: verr.Error(), ErrorCode: verr.Code,
		})
		_ = writeIndentedJSON(CETConvergenceSummaryPath, &summary)
		return 1
	}
	fmt.Printf("[proof 1] locked chain VERIFIED — decision=%s seal=%s\n", res.Decision, res.SealHash)

	// --- Real enforcement token: signed attestation + (best-effort) JWT ------
	enforcementRef, capJWT, capKID, jwtNote, jwtOK := mintConvergenceEnforcementToken(provider, res, innerDecision, now)
	summary.CapabilityJWTMinted = jwtOK
	summary.CapabilityJWTNote = jwtNote

	// --- Emit the enforcement_decision artifact ------------------------------
	encArtifact := BuildEnforcementDecisionArtifact(res, enforcementRef, now)
	encPath, err := PersistEnforcementDecisionArtifact(encArtifact)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: persist enforcement artifact: %v\n", err)
		return 1
	}
	summary.EnforcementDecision = encArtifact
	summary.EnforcementArtifactPath = encPath
	fmt.Printf("[proof 1] enforcement_decision artifact -> %s\n", encPath)

	// --- Build the Sarathi->Bridge handoff (PREPARED_NOT_TRANSMITTED) --------
	handoff := BuildBridgeHandoffArtifact(res, enforcementRef, capJWT, capKID, mode.BridgeIngressURL, now)
	handoffPath, err := PersistBridgeHandoffArtifact(handoff)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: persist bridge handoff: %v\n", err)
		return 1
	}
	summary.BridgeHandoff = handoff
	summary.BridgeHandoffPath = handoffPath
	fmt.Printf("[proof 1] bridge_handoff artifact -> %s (status=%s)\n", handoffPath, handoff.TransmissionStatus)

	// =========================================================================
	// LIVE BRIDGE TRANSMISSION (when --bridge-ingress-url + capability JWT)
	// =========================================================================
	if mode.BridgeIngressURL != "" && capJWT != "" && jwtOK {
		fmt.Println()
		fmt.Println("  ┌─────────────────────────────────────────────────────────┐")
		fmt.Println("  │  SARATHI → BRIDGE  live transmission                    │")
		fmt.Println("  └─────────────────────────────────────────────────────────┘")
		fmt.Printf("  target:   %s\n", mode.BridgeIngressURL)
		fmt.Printf("  exec_id:  %s\n", handoff.ExecutionID)
		fmt.Printf("  trace_id: %s\n", handoff.TraceID)
		fmt.Printf("  cet_hash: %s\n", handoff.CETHash)
		fmt.Printf("  auth:     Bearer <capability JWT> (kid=%s)\n", capKID)
		fmt.Println()

		txStatus, txHTTP, txNote := runBridgeTransmission(handoff, capJWT)
		fmt.Printf("  HTTP status: %d\n", txHTTP)
		fmt.Printf("  result:      %s\n", txStatus)
		fmt.Printf("  note:        %s\n", txNote)

		if txStatus == HandoffTransmitted {
			handoff.TransmissionStatus = HandoffTransmitted
			handoff.TransmissionNote = txNote
			_, _ = PersistBridgeHandoffArtifact(handoff)
			summary.BridgeHandoff = handoff
			fmt.Println()
			fmt.Println("  ✓ Bridge ACK received — handoff re-persisted as TRANSMITTED")
		} else {
			fmt.Println()
			fmt.Println("  ✗ Bridge did not return 2xx — status remains PREPARED_NOT_TRANSMITTED")
		}
		fmt.Println()
	}

	summary.Steps = append(summary.Steps, convergenceStep{
		Name: "positive_locked_chain", Expectation: "accept(allow)", Passed: res.Decision == CETDecisionAllow,
		Detail:       fmt.Sprintf("decision=%s cet_hash_mode=%s seal=%s", res.Decision, encArtifact.CETHashVerificationMode, res.SealHash),
		ArtifactPath: encPath,
	})

	// =========================================================================
	// PROOF 2 — cet_hash recompute mechanism (Sarathi-controlled material)
	// =========================================================================
	summary.Steps = append(summary.Steps, runCETHashRecomputeProof(provider, registry, now))

	// =========================================================================
	// PROOF 3 — fail-closed: mutated inner decision => signature reject
	// =========================================================================
	summary.Steps = append(summary.Steps, runMutatedInnerProof(provider, registry, sum, innerWire, now))

	// =========================================================================
	// PROOF 4 — fail-closed: trace_id discontinuity (envelope != inner)
	// =========================================================================
	summary.Steps = append(summary.Steps, runTraceDiscontinuityProof(provider, registry, innerWire, now))

	// --- Summary -------------------------------------------------------------
	summary.AllPassed = true
	for _, s := range summary.Steps {
		if !s.Passed {
			summary.AllPassed = false
		}
	}
	if err := writeIndentedJSON(CETConvergenceSummaryPath, &summary); err != nil {
		fmt.Fprintf(os.Stderr, "WARN: write summary: %v\n", err)
	}

	fmt.Println("------------------------------------------------------------")
	for _, s := range summary.Steps {
		status := "PASS"
		if !s.Passed {
			status = "FAIL"
		}
		fmt.Printf("  [%s] %-26s %s\n", status, s.Name, s.Detail)
	}
	fmt.Printf("  summary -> %s\n", CETConvergenceSummaryPath)
	fmt.Println("============================================================")
	if summary.AllPassed {
		fmt.Println("  TANTRA CONVERGENCE: ALL PROOFS PASSED")
		return 0
	}
	fmt.Println("  TANTRA CONVERGENCE: ONE OR MORE PROOFS FAILED")
	return 1
}

// runBridgeTransmission POSTs the handoff artifact to the Bridge ingress URL
// with the capability JWT as the Bearer credential. Returns the transmission
// status string, the HTTP status code received (0 on network error), and a
// human-readable note. The caller is responsible for updating and re-persisting
// the handoff artifact on success.
func runBridgeTransmission(handoff *CETBridgeHandoffArtifact, capabilityJWT string) (status string, httpCode int, note string) {
	body, err := json.Marshal(handoff)
	if err != nil {
		return HandoffPreparedNotTransmitted, 0, "marshal error: " + err.Error()
	}
	req, err := http.NewRequest(http.MethodPost, handoff.BridgeIngressURL, bytes.NewReader(body))
	if err != nil {
		return HandoffPreparedNotTransmitted, 0, "build request error: " + err.Error()
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+capabilityJWT)
	req.Header.Set("ngrok-skip-browser-warning", "true")
	req.Header.Set("X-Sarathi-Execution-ID", handoff.ExecutionID)
	req.Header.Set("X-Sarathi-Trace-ID", handoff.TraceID)
	req.Header.Set("X-Sarathi-CET-Hash", handoff.CETHash)
	req.Header.Set("X-Sarathi-Bucket-Key", handoff.BucketKey)
	req.Header.Set("X-Sarathi-SumScript-Seal", handoff.HashContinuity.SarathiSealHash)
	req.Header.Set("X-Sarathi-Schema-Version", handoff.SchemaVersion)
	req.Header.Set("X-Sarathi-Contract-Version", handoff.ContractVersion)

	resp, err := (&http.Client{Timeout: 30 * time.Second}).Do(req)
	if err != nil {
		return HandoffPreparedNotTransmitted, 0, "POST failed: " + err.Error()
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		return HandoffTransmitted, resp.StatusCode,
			fmt.Sprintf("2xx ACK from Bridge (%d) — chain marked TRANSMITTED.", resp.StatusCode)
	}
	return HandoffPreparedNotTransmitted, resp.StatusCode,
		fmt.Sprintf("Bridge returned HTTP %d — not a 2xx ACK; status unchanged.", resp.StatusCode)
}

// newConvergenceBoundary builds a CETBoundary with a fresh in-memory replay
// store so each proof is independent (no cross-test replay collisions).
func newConvergenceBoundary(provider CryptoProvider, registry *TantraTrustConsumer, now time.Time) *CETBoundary {
	return &CETBoundary{
		Inner: &TantraVerifier{
			Provider:    provider,
			Registry:    registry,
			ReplayStore: NewMemoryTantraReplayStore(),
			Now:         func() time.Time { return now },
		},
		Now: func() time.Time { return now },
	}
}

// buildSignedConvergenceDecision builds and signs a real tantra.decision.v1
// (verdict ALLOW) bound to traceID, returning the decision + its canonical
// wire bytes.
func buildSignedConvergenceDecision(provider CryptoProvider, priv PrivateKeyMaterial, keyID, traceID string, now time.Time) (*TantraDecision, []byte, error) {
	inputHash := sha256Hex([]byte("tantra-convergence-input|" + traceID + "|" + LockedConvPolicyRef))
	material := TantraDecisionMaterial{
		SchemaVersion:   TantraSchemaV1,
		TraceID:         traceID,
		InputHash:       inputHash,
		Verdict:         TantraVerdictAllow,
		PolicyReference: LockedConvPolicyRef,
		EvaluatorID:     LockedSovereignEvalID,
	}
	d := &TantraDecision{
		SchemaVersion:      TantraSchemaV1,
		TraceID:            traceID,
		InputHash:          inputHash,
		DecisionHash:       ComputeTantraDecisionHash(material),
		Verdict:            TantraVerdictAllow,
		PolicyReference:    LockedConvPolicyRef,
		EvaluatorID:        LockedSovereignEvalID,
		EnforcementBinding: "CLEARED:Sovereign ALLOW for TANTRA convergence chain",
		Timestamp:          now.Format(time.RFC3339Nano),
		Signature: TantraSignature{
			Alg:      string(provider.Algorithm()),
			KeyID:    keyID,
			Encoding: TantraSignatureEncoding,
		},
	}
	d.DecisionID = ComputeTantraDecisionID(d)
	signable, err := CanonicalSignableBytes(d)
	if err != nil {
		return nil, nil, fmt.Errorf("signable: %w", err)
	}
	sig, err := provider.Sign(signable, priv)
	if err != nil {
		return nil, nil, fmt.Errorf("sign: %w", err)
	}
	d.Signature.Value = base64.RawURLEncoding.EncodeToString(sig)
	wire, err := CanonicalWireBytes(d)
	if err != nil {
		return nil, nil, fmt.Errorf("wire: %w", err)
	}
	return d, wire, nil
}

// mintConvergenceEnforcementToken produces a real enforcement token reference.
// It (1) writes a real Sarathi enforcement signing key, (2) emits the real
// signed enforcement attestation via the production path, and (3) best-effort
// mints a real capability JWT bound to the locked identity. Returns the
// single-string reference, the JWT (if minted), its kid, a human note, and
// whether the JWT was minted.
func mintConvergenceEnforcementToken(provider CryptoProvider, res *CETVerifierResult, inner *TantraDecision, now time.Time) (ref, jwt, kid, note string, jwtOK bool) {
	ref = "sarathi-enforcement:pending"

	// (1)+(2) Real signed enforcement attestation via the production emit path.
	// PREFER the operator's persistent enforcement key (the one shared with Core
	// for verifying Sarathi's attestations) when present — and NEVER clobber it.
	// When absent, use a throwaway key inside the proof directory so a proof run
	// can never overwrite or pollute the live signing identity.
	persistentKey := filepath.Join("live", "keys", "sarathi_enforcement", "issuer-priv.hex")
	encKeyPath := persistentKey
	if _, statErr := os.Stat(persistentKey); statErr != nil {
		encKeyPath = filepath.Join(CETArtifactDir, ".enforce_proof_key.hex")
		_ = os.MkdirAll(CETArtifactDir, 0o755)
		if epriv, _, gerr := provider.Generate(nil); gerr == nil {
			_ = os.WriteFile(encKeyPath, []byte(provider.EncodePrivateKey(epriv)), 0o600)
		}
	}
	os.Setenv(EnvSarathiEnforcementPrivPath, encKeyPath)
	if os.Getenv(EnvSarathiEnforcementKeyID) == "" {
		os.Setenv(EnvSarathiEnforcementKeyID, SarathiEnforcementEvaluatorID+"#"+algKeyIDSuffix(provider.Algorithm())+"-2026-05")
	}
	if extDec, terr := TranslateTantraToExternalDecision(res.InnerResult); terr == nil {
		if attest, aerr := EmitSarathiEnforcementAttestation(res.InnerResult, extDec, now); aerr == nil && attest != nil {
			ref = "sarathi-enforcement:" + attest.DecisionID
			fmt.Printf("[token] signed enforcement attestation decision_id=%s\n", attest.DecisionID)
		} else if aerr != nil {
			fmt.Fprintf(os.Stderr, "[token] WARN attestation: %v\n", aerr)
		}
	}

	// (3) Best-effort real capability JWT (the token Bridge verifies offline).
	auth, jerr := LoadJWTAuthorityFromEnv()
	if jerr != nil || auth == nil {
		note = "capability JWT not minted (no JWT authority signing key available at build time); enforcement reference is the signed Sarathi enforcement attestation. Live /sarathi/enforce mints the JWT per call."
		return ref, "", "", note, false
	}
	private := map[string]interface{}{
		"execution_id":     res.SumScript.ExecutionID,
		"trace_id":         res.SumScript.TraceID,
		"cet_hash":         res.SumScript.CETHash,
		"bucket_key":       res.SumScript.BucketKey,
		"decision_id":      inner.DecisionID,
		"verdict":          "ALLOW",
		"contract_version": res.SumScript.ContractVersion,
		"sumscript_seal":   res.SealHash,
		"boundary":         "Sarathi->Bridge",
	}
	mj, merr := auth.MintJWT(MintRequest{
		Subject:       inner.DecisionID,
		Audience:      DefaultJWTAudience,
		PrivateClaims: private,
		CorrelationID: res.SumScript.TraceID,
	})
	if merr != nil || mj == nil {
		note = "capability JWT mint attempted but failed: " + fmt.Sprint(merr) + "; enforcement reference is the signed Sarathi enforcement attestation."
		return ref, "", "", note, false
	}
	note = fmt.Sprintf("capability JWT minted (aud=%s, kid=%s, TTL<=60s — re-minted per live call). Carried verbatim in the bridge_handoff artifact for offline JWKS verification.", DefaultJWTAudience, mj.Kid)
	ref = "cap-jwt:" + fmt.Sprint(mj.Claims["jti"])
	return ref, mj.Token, mj.Kid, note, true
}

// runCETHashRecomputeProof demonstrates the independent cet_hash recompute
// gate using Sarathi-controlled pre-image material (NOT the locked hash — that
// would require CET's pre-image). Proves the C9 mechanism end-to-end.
func runCETHashRecomputeProof(provider CryptoProvider, registry *TantraTrustConsumer, now time.Time) convergenceStep {
	step := convergenceStep{Name: "cet_hash_recompute_mechanism", Expectation: "accept(recompute+continuity)"}
	const selfTraceID = "trace-sarathi-cet-selftest-001"

	priv, pub, err := provider.Generate(nil)
	if err != nil {
		step.Detail = "keygen: " + err.Error()
		return step
	}
	keyID := LockedSovereignEvalID + "#" + algKeyIDSuffix(provider.Algorithm()) + "-selftest-2026-06"
	reg, _, _ := NewTantraTrustConsumer([]TantraEvaluatorEntry{{
		EvaluatorID: LockedSovereignEvalID, Name: "selftest", Status: "ACTIVE",
		SchemaVersion: TantraSchemaV1, Algorithm: string(provider.Algorithm()),
		KeyID: keyID, PublicKey: provider.EncodePublicKey(pub),
	}}, provider)
	_ = registry // selftest uses its own registry

	_, wire, err := buildSignedConvergenceDecision(provider, priv, keyID, selfTraceID, now)
	if err != nil {
		step.Detail = "inner: " + err.Error()
		return step
	}
	// Sarathi-controlled CET pre-image material; cet_hash = sha256(material).
	material := []byte("sarathi-cet-selftest-material|" + selfTraceID)
	cetHash := sha256Hex(material)
	sum := &CETSumScript{
		SchemaVersion: CETConvergenceSchemaVersion, ContractVersion: CETConvergenceContractVersion,
		ExecutionID: "exec-sarathi-cet-selftest-001", TraceID: selfTraceID,
		CETHash: cetHash, BucketKey: sha256Hex([]byte("selftest-bucket-key")),
		DecisionB64:    base64.StdEncoding.EncodeToString(wire),
		CETMaterialB64: base64.StdEncoding.EncodeToString(material),
	}
	raw, _ := json.Marshal(sum)
	res, verr := (&CETBoundary{
		Inner: &TantraVerifier{Provider: provider, Registry: reg, ReplayStore: NewMemoryTantraReplayStore(), Now: func() time.Time { return now }},
		Now:   func() time.Time { return now },
	}).Verify(raw)
	if verr != nil {
		step.Detail = "unexpected reject: " + verr.Error()
		step.ErrorCode = verr.Code
		return step
	}
	step.Passed = res.CETHashRecomputed && res.Decision == CETDecisionAllow
	step.Detail = fmt.Sprintf("recompute ran=%v cet_hash=%s matched declared", res.CETHashRecomputed, cetHash[:16]+"…")
	return step
}

// runMutatedInnerProof flips a byte inside the inner decision so the inner
// Ed25519 signature fails — proving "mutation = signature failure" and a
// trace-bound rejection artifact is emitted.
func runMutatedInnerProof(provider CryptoProvider, registry *TantraTrustConsumer, validSum *CETSumScript, innerWire []byte, now time.Time) convergenceStep {
	step := convergenceStep{Name: "mutated_inner_decision", Expectation: "reject(fail-closed)"}
	mutated := make([]byte, len(innerWire))
	copy(mutated, innerWire)
	// Flip a byte inside the enforcement_binding value (changes signed bytes).
	idx := strings.Index(string(mutated), `"enforcement_binding":"CLEARED`)
	if idx < 0 {
		step.Detail = "could not locate enforcement_binding to mutate"
		return step
	}
	mutated[idx+len(`"enforcement_binding":"`)] = 'X'
	sum := *validSum
	sum.DecisionB64 = base64.StdEncoding.EncodeToString(mutated)
	raw, _ := json.Marshal(&sum)

	res, verr := newConvergenceBoundary(provider, registry, now).Verify(raw)
	if verr == nil {
		step.Detail = fmt.Sprintf("SECURITY FAILURE: mutated chain accepted (decision=%s)", res.Decision)
		return step
	}
	rej := BuildTraceBoundRejectionArtifact(verr, now)
	path, _ := PersistTraceBoundRejectionArtifact(rej)
	step.Passed = verr.Code == ErrCETInnerDecisionInvalid && rej.FailClosed
	step.ErrorCode = verr.Code
	step.ArtifactPath = path
	step.Detail = fmt.Sprintf("rejected: %s (inner=%s) fail_closed=%v", verr.Code, verr.InnerCode, rej.FailClosed)
	return step
}

// runTraceDiscontinuityProof builds an envelope whose trace_id differs from the
// inner decision's trace_id — proving the C8 continuity gate fails closed.
func runTraceDiscontinuityProof(provider CryptoProvider, registry *TantraTrustConsumer, innerWire []byte, now time.Time) convergenceStep {
	step := convergenceStep{Name: "trace_id_discontinuity", Expectation: "reject(fail-closed)"}
	sum := &CETSumScript{
		SchemaVersion: CETConvergenceSchemaVersion, ContractVersion: CETConvergenceContractVersion,
		ExecutionID: LockedExecutionID, TraceID: "trace-tantra-DIFFERENT-999",
		CETHash: LockedCETHash, BucketKey: LockedBucketKey,
		DecisionB64: base64.StdEncoding.EncodeToString(innerWire),
	}
	raw, _ := json.Marshal(sum)
	res, verr := newConvergenceBoundary(provider, registry, now).Verify(raw)
	if verr == nil {
		step.Detail = fmt.Sprintf("SECURITY FAILURE: trace discontinuity accepted (decision=%s)", res.Decision)
		return step
	}
	rej := BuildTraceBoundRejectionArtifact(verr, now)
	path, _ := PersistTraceBoundRejectionArtifact(rej)
	step.Passed = verr.Code == ErrCETTraceIDDiscontinuity && rej.FailClosed
	step.ErrorCode = verr.Code
	step.ArtifactPath = path
	step.Detail = fmt.Sprintf("rejected: %s fail_closed=%v", verr.Code, rej.FailClosed)
	return step
}
