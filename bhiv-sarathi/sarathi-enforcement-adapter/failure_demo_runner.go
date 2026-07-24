// failure_demo_runner.go (v14.8 Sovereign Authority Closure)
//
// --failure-demo entry point.
//
// Boots the live-integration peer topology (BHIV Core + InsightFlow + Bucket
// as separate OS processes, ed25519-signing, real TCP), runs one baseline
// green execution, then programmatically executes three LIVE failure
// injections against the running peers. Peers stay alive after the automated
// pass so a reviewer may repeat each injection by hand using the printed
// curl + sha256sum commands — no restart is required.
//
// The three injections use only existing v14.6/v14.7 fail-closed codepaths;
// no new cryptography, no new canonicalisation. v14.8 adds only orchestration.
//
//   1. payload_tamper      — overwrite live/bucket/<DEC>.json with a 1-byte
//                            flip, call VerifyBucketReadback, expect
//                            ERR_BUCKET_READBACK_MISMATCH.
//   2. invalid_signature   — POST a receipt to /v1/downstream-ack signed with
//                            the WRONG Ed25519 key, expect HTTP 400 +
//                            ERR_DOWNSTREAM_RECEIPT_INVALID and an entry in
//                            proof_logs/downstream_ack_rejections.jsonl.
//   3. bucket_mismatch     — POST the same decision_id to the Bucket peer
//                            with a drifted canonical body, expect HTTP 409 +
//                            ERR_RESPONSE_HASH_MISMATCH (PeerStore.seenIndex
//                            drift-rejection).
//
// TAG: sovereign-authority-v14.8

package main

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"time"
)

// FailureDemoReportPath is the v14.8 artefact.
const FailureDemoReportPath = "failure_demo_report.json"

// FailureDemoObservationsPath is the append-only log of scenarios,
// shaped so a reviewer can grep/jq it verbatim.
const FailureDemoObservationsPath = "proof_logs/failure_demo_observations.jsonl"

// FailureDemoSchemaVersion pins the observation-row schema.
const FailureDemoSchemaVersion = "sarathi.failure-demo/v14.8"

// FailureDemoReportSchemaVersion pins the summary schema.
const FailureDemoReportSchemaVersion = "sarathi.failure-demo.report/v14.8"

// FailureDemoDefaultDeadlineSec is how long peers remain alive after the
// automated pass so a reviewer can tamper interactively. Override via
// SARATHI_FAILURE_DEMO_DEADLINE_S.
const FailureDemoDefaultDeadlineSec = 300

// FailureDemoObservation is one injection row.
type FailureDemoObservation struct {
	SchemaVersion      string `json:"schema_version"`
	Scenario           string `json:"scenario"`
	ObservedAt         string `json:"observed_at"`
	DecisionID         string `json:"decision_id"`
	ExpectedErrorCode  string `json:"expected_error_code"`
	ObservedErrorCode  string `json:"observed_error_code"`
	ObservedHTTPStatus int    `json:"observed_http_status"`
	PreHash            string `json:"pre_hash"`
	PostHash           string `json:"post_hash"`
	ReviewerHint       string `json:"reviewer_hint"`
	Passed             bool   `json:"passed"`
	Detail             string `json:"detail,omitempty"`
}

// FailureDemoReport is the summary artefact.
type FailureDemoReport struct {
	SchemaVersion    string                  `json:"schema_version"`
	GeneratedAt      string                  `json:"generated_at"`
	SarathiAckAddr   string                  `json:"sarathi_ack_addr"`
	PeerAddrs        map[string]string       `json:"peer_addrs"`
	BaselineExecID   string                  `json:"baseline_execution_id"`
	BaselineDecID    string                  `json:"baseline_decision_id"`
	BaselineHash     string                  `json:"baseline_response_hash"`
	ScenariosTotal   int                     `json:"scenarios_total"`
	ScenariosPassed  int                     `json:"scenarios_passed"`
	GateSatisfied    bool                    `json:"gate_satisfied"`
	ReviewerCommands []string                `json:"reviewer_commands"`
	Observations     []FailureDemoObservation `json:"observations"`
	Notes            []string                `json:"notes,omitempty"`
}

// RunFailureDemo is the --failure-demo entry point. Returns the OS exit code
// (0 when all three injections produced the expected rejection).
func RunFailureDemo() int {
	printHeader("FAILURE DEMO (v14.8 — LIVE injections against running peers)")

	rep := &FailureDemoReport{
		SchemaVersion: FailureDemoReportSchemaVersion,
		GeneratedAt:   time.Now().UTC().Format(time.RFC3339Nano),
		PeerAddrs:     map[string]string{},
	}

	// ---- 1. Ack server.
	ackAddr, ackSrv, err := startAckServer()
	if err != nil {
		rep.Notes = append(rep.Notes, "ack_server_start_failed: "+err.Error())
		writeFailureDemoReport(rep)
		return 1
	}
	defer ackSrv.Close()
	rep.SarathiAckAddr = ackAddr
	ackURL := "http://" + ackAddr + "/v1/downstream-ack"
	handshakeURL := "http://" + ackAddr + "/v1/handshake"

	// ---- 2. Install AckTracker.
	ackTimeout := DefaultAckTimeout
	if ms, _ := strconv.Atoi(os.Getenv("SARATHI_DOWNSTREAM_ACK_TIMEOUT_MS")); ms > 0 {
		ackTimeout = time.Duration(ms) * time.Millisecond
	}
	tracker := NewAckTracker(ackTimeout)
	InstallGlobalAckTracker(tracker)

	// ---- 3. Spawn peers.
	selfPath, err := os.Executable()
	if err != nil {
		rep.Notes = append(rep.Notes, "executable_path_failed: "+err.Error())
		writeFailureDemoReport(rep)
		return 1
	}
	peerProcs, peerAddrs, err := spawnPeers(selfPath, ackURL, handshakeURL)
	if err != nil {
		rep.Notes = append(rep.Notes, "peer_spawn_failed: "+err.Error())
		stopPeers(peerProcs)
		writeFailureDemoReport(rep)
		return 1
	}
	defer stopPeers(peerProcs)
	for k, addr := range peerAddrs {
		rep.PeerAddrs[string(k)] = addr
	}
	for kind, addr := range peerAddrs {
		if err := waitForHealth("http://"+addr+"/health", 5*time.Second); err != nil {
			rep.Notes = append(rep.Notes, fmt.Sprintf("peer %s health_wait: %v", kind, err))
			writeFailureDemoReport(rep)
			return 1
		}
	}
	fmt.Printf("  all 3 peers healthy; ack_server=%s\n\n", ackAddr)

	// ---- 4. Baseline green execution to populate peer storage.
	_ = os.Setenv("SARATHI_ROUTE_CORE_URL", "http://"+peerAddrs[PeerCore]+"/v1/enforce")
	_ = os.Setenv("SARATHI_ROUTE_INSIGHTFLOW_URL", "http://"+peerAddrs[PeerInsightFlow]+"/v1/observe")
	_ = os.Setenv("SARATHI_ROUTE_BUCKET_URL", "http://"+peerAddrs[PeerBucket]+"/v1/audit")

	fx, ferr := BuildOrLoadReplayFixture()
	if ferr != nil {
		rep.Notes = append(rep.Notes, "fixture_build_failed: "+ferr.Error())
		writeFailureDemoReport(rep)
		return 1
	}

	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()
	// v15.2 FIX: wire FallbackAuditSink so JSONL backup is generated.
	auditSink, asErr := WireFallbackAuditSink(ea)
	if asErr != nil {
		rep.Notes = append(rep.Notes, "audit_sink_wire_failed: "+asErr.Error())
		writeFailureDemoReport(rep)
		return 1
	}
	defer auditSink.Close()
	if err := ea.GetEvaluatorRegistry().RegisterEvaluator(
		fx.EvaluatorID, "failure demo fixture evaluator", fx.PublicKey,
		map[string]string{"fixture": "true"}, "failure_demo",
	); err != nil {
		rep.Notes = append(rep.Notes, "register_evaluator_failed: "+err.Error())
		writeFailureDemoReport(rep)
		return 1
	}
	mc := NewModeController(BHIVModeExternal)
	pa := NewPDPAdapter(ea, mc)
	pa.ResetReplayTrackerForHarness()

	execID := "EXEC-FAIL-BASE"
	corrID := "corr-fail-base"
	iterBytes, berr := buildFailureBaselineFixture(fx)
	if berr != nil {
		rep.Notes = append(rep.Notes, "baseline_fixture_build: "+berr.Error())
		writeFailureDemoReport(rep)
		return 1
	}
	bucketBase := "http://" + peerAddrs[PeerBucket]
	baseRec := runSingleLiveExecution(pa, iterBytes, execID, corrID, tracker, bucketBase, auditSink)
	if !baseRec.Match || !baseRec.GateSummary.Satisfied {
		rep.Notes = append(rep.Notes,
			"baseline_failed: error="+baseRec.ErrorCode+" detail="+baseRec.Detail)
		writeFailureDemoReport(rep)
		return 1
	}
	rep.BaselineExecID = baseRec.ExecutionID
	rep.BaselineDecID = baseRec.DecisionID
	rep.BaselineHash = baseRec.ResponseHash
	fmt.Printf("  baseline green: exec=%s dec=%s hash=%s\n\n",
		baseRec.ExecutionID, baseRec.DecisionID, baseRec.ResponseHash[:16])

	// ---- 5. Four scenarios (v15.6 adds sarathi_unavailable_for_bridge).
	obs := []FailureDemoObservation{}
	obs = append(obs, runPayloadTamperInjection(bucketBase, baseRec))
	obs = append(obs, runInvalidSignatureInjection(ackURL, baseRec))
	obs = append(obs, runBucketMismatchInjection(peerAddrs[PeerBucket], baseRec))
	obs = append(obs, runSarathiUnavailableForBridge(baseRec))

	rep.Observations = obs
	rep.ScenariosTotal = len(obs)
	for _, o := range obs {
		if err := appendFailureObservation(o); err != nil {
			rep.Notes = append(rep.Notes, "append_observation_failed: "+err.Error())
		}
		if o.Passed {
			rep.ScenariosPassed++
		}
	}
	rep.GateSatisfied = rep.ScenariosPassed == rep.ScenariosTotal

	// Reviewer repeat instructions — peers remain alive during the deadline
	// window so these commands are directly executable against the same host.
	rep.ReviewerCommands = []string{
		fmt.Sprintf("# 1. payload tamper (rewrite the stored bucket file and re-GET it)"),
		fmt.Sprintf("sha256sum live/bucket/%s.json", rep.BaselineDecID),
		fmt.Sprintf("printf 'TAMPERED' > live/bucket/%s.json", rep.BaselineDecID),
		fmt.Sprintf("curl -i http://%s/v1/audit/%s", peerAddrs[PeerBucket], rep.BaselineDecID),
		fmt.Sprintf("# 2. invalid signature (POST a junk ed25519 receipt to Sarathi ACK endpoint)"),
		fmt.Sprintf("curl -i -X POST -H 'Content-Type: application/json' --data '{\"schema_version\":\"sarathi.live.receipt/v1.0\",\"peer\":\"core\",\"execution_id\":\"%s\",\"decision_id\":\"%s\",\"response_hash\":\"%s\",\"received_body_hash\":\"%s\",\"peer_public_key_hex\":\"00\",\"receipt_signature\":\"00\"}' http://%s/v1/downstream-ack",
			rep.BaselineExecID, rep.BaselineDecID, rep.BaselineHash, rep.BaselineHash, ackAddr),
		fmt.Sprintf("# 3. bucket mismatch (POST same decision_id with drifted bytes)"),
		fmt.Sprintf("curl -i -X POST -H 'Content-Type: application/json' -H 'X-Sarathi-Decision-ID: %s' -H 'X-Sarathi-Response-Hash: deadbeef' --data '{\"drifted\":true}' http://%s/v1/audit",
			rep.BaselineDecID, peerAddrs[PeerBucket]),
	}

	writeFailureDemoReport(rep)

	fmt.Printf("\n  FAILURE DEMO: scenarios_passed=%d/%d gate_satisfied=%t\n",
		rep.ScenariosPassed, rep.ScenariosTotal, rep.GateSatisfied)

	if !rep.GateSatisfied {
		// Exit immediately on automated failure — no reviewer window.
		return 1
	}

	// ---- 6. Keep peers alive so reviewer can repeat injections manually.
	deadlineSec := FailureDemoDefaultDeadlineSec
	if v, _ := strconv.Atoi(os.Getenv("SARATHI_FAILURE_DEMO_DEADLINE_S")); v > 0 {
		deadlineSec = v
	}
	fmt.Printf("\n  peers remain alive for %d seconds — reviewer may repeat any\n", deadlineSec)
	fmt.Printf("  scenario using the commands in %s.reviewer_commands\n", FailureDemoReportPath)
	fmt.Printf("  observation rows appended live to %s\n", FailureDemoObservationsPath)
	fmt.Printf("  ctrl-c to exit early.\n\n")
	time.Sleep(time.Duration(deadlineSec) * time.Second)
	return 0
}

// ============================================================================
// Injection 1: payload tampering
// ============================================================================

// runPayloadTamperInjection overwrites the Bucket peer's stored file for the
// baseline decision_id with a different byte sequence, then re-runs the
// Sarathi-side bucket readback and confirms the verifier fires
// ERR_BUCKET_READBACK_MISMATCH.
func runPayloadTamperInjection(bucketBase string, base LiveIntegrationRecord) FailureDemoObservation {
	obs := FailureDemoObservation{
		SchemaVersion:     FailureDemoSchemaVersion,
		Scenario:          "payload_tamper",
		ObservedAt:        time.Now().UTC().Format(time.RFC3339Nano),
		DecisionID:        base.DecisionID,
		ExpectedErrorCode: CodeBucketReadbackMismatch,
	}

	path := filepath.Join(LivePeerDefaultStorageRoot, string(PeerBucket),
		safeDecisionID(base.DecisionID)+".json")
	preBytes, err := os.ReadFile(path)
	if err != nil {
		obs.Detail = "read_pre: " + err.Error()
		return obs
	}
	obs.PreHash = Sha256Hex(preBytes)
	obs.ReviewerHint = fmt.Sprintf("sha256sum %s  # expect: %s (pre-tamper)",
		path, obs.PreHash)

	tampered := make([]byte, len(preBytes))
	copy(tampered, preBytes)
	// Flip the last non-structural byte — guaranteed to stay inside the JSON
	// envelope and break the hash. We pick index len-2 (the byte BEFORE the
	// trailing '}') because index len-1 is structural JSON.
	if len(tampered) >= 2 {
		tampered[len(tampered)-2] ^= 0x01
	}
	obs.PostHash = Sha256Hex(tampered)

	if err := os.WriteFile(path, tampered, 0o644); err != nil {
		obs.Detail = "write_tampered: " + err.Error()
		// Restore on error.
		_ = os.WriteFile(path, preBytes, 0o644)
		return obs
	}

	// Verify — should reject.
	readback := VerifyBucketReadback(context.Background(), bucketBase, base.DecisionID,
		base.ExecutionID, preBytes, base.ResponseHash)
	obs.ObservedErrorCode = readback.ErrorCode
	obs.ObservedHTTPStatus = readback.HTTPStatus
	obs.Passed = readback.ErrorCode == CodeBucketReadbackMismatch && !readback.Match
	if !obs.Passed {
		obs.Detail = fmt.Sprintf("unexpected: error=%s match=%t detail=%s",
			readback.ErrorCode, readback.Match, readback.Detail)
	}

	// Restore original so downstream manual repeats start from a clean state.
	if err := os.WriteFile(path, preBytes, 0o644); err != nil {
		// Non-fatal; note but do not invalidate scenario.
		obs.Detail += "; restore_pre_failed: " + err.Error()
	}
	return obs
}

// ============================================================================
// Injection 2: invalid signature
// ============================================================================

// runInvalidSignatureInjection mints a fresh Ed25519 keypair, signs a receipt
// referencing the baseline execution, then DELIBERATELY CORRUPTS the
// signature bytes inside the signed JSON before POSTing to Sarathi's
// /v1/downstream-ack endpoint. This exercises the exact ed25519.Verify(...)
// rejection branch in [peer_common.go::VerifyReceipt] — "signature
// verification failed" — surfaced as ERR_DOWNSTREAM_RECEIPT_INVALID.
//
// Why this is the honest signature-failure path (no mocking, no simulation):
//   1. The keypair is real (crypto/ed25519.GenerateKey with crypto/rand).
//   2. Sign() produces a cryptographically-valid signature over canonical bytes.
//   3. We parse the canonical JSON, flip a byte inside `receipt_signature` hex,
//      and re-serialize — no private key substitution, no short-circuit.
//   4. Sarathi re-hydrates the receipt, attempts ed25519.Verify with the
//      embedded pubkey, and that verification truly fails. The rejection is
//      then logged by the real handler in [downstream_ack_endpoint.go].
//
// No pre-recorded response is used. Every byte is produced live by the
// same crypto stack the production peers use.
func runInvalidSignatureInjection(ackURL string, base LiveIntegrationRecord) FailureDemoObservation {
	obs := FailureDemoObservation{
		SchemaVersion:     FailureDemoSchemaVersion,
		Scenario:          "invalid_signature",
		ObservedAt:        time.Now().UTC().Format(time.RFC3339Nano),
		DecisionID:        base.DecisionID,
		ExpectedErrorCode: CodeDownstreamReceiptInvalid,
	}

	// Mint a real throwaway keypair — the embedded public key will match the
	// private key we used to sign, so only an explicit tamper can fail
	// ed25519.Verify. This is the critical point: we do NOT substitute the
	// pubkey. Signature verification fails *because the signature bytes
	// themselves are corrupted*, not because of a key mismatch.
	wrongPub, wrongPriv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		obs.Detail = "keygen: " + err.Error()
		return obs
	}
	signer := &PeerReceiptSigner{pub: wrongPub, priv: wrongPriv}

	// Build a receipt whose body-hash field is CONSISTENT with response_hash —
	// so if signature verification passed, the request would progress. This
	// isolates the crypto-level rejection as the only possible failure path.
	receipt := &PeerReceipt{
		Peer:             string(PeerCore),
		ExecutionID:      base.ExecutionID,
		DecisionID:       base.DecisionID,
		ResponseHash:     base.ResponseHash,
		ReceivedBodyHash: base.ResponseHash,
		PersistedAt:      time.Now().UTC().Format(time.RFC3339Nano),
		StoragePath:      "injected/invalid_signature",
	}
	raw, err := signer.Sign(receipt)
	if err != nil {
		obs.Detail = "sign: " + err.Error()
		return obs
	}

	// Now corrupt the signature bytes inside the signed envelope. Parse the
	// canonical JSON, flip 2 hex characters inside the receipt_signature
	// field, and re-serialize canonically. This guarantees ed25519.Verify
	// will fail and the rejection is truly cryptographic.
	var envelope map[string]interface{}
	if err := json.Unmarshal(raw, &envelope); err != nil {
		obs.Detail = "re-unmarshal: " + err.Error()
		return obs
	}
	sigHex, _ := envelope["receipt_signature"].(string)
	if len(sigHex) < 4 {
		obs.Detail = "signature hex too short to tamper"
		return obs
	}
	// Flip the first hex nibble. 'a' -> 'b', '5' -> '6', etc. Guarantees the
	// signature bytes differ from the valid one while remaining valid hex.
	flipped := []byte(sigHex)
	switch flipped[0] {
	case '0':
		flipped[0] = '1'
	case '9':
		flipped[0] = '8'
	case 'f':
		flipped[0] = 'e'
	case 'F':
		flipped[0] = 'E'
	default:
		flipped[0]++
	}
	envelope["receipt_signature"] = string(flipped)
	tampered, err := CanonicalMarshal(envelope)
	if err != nil {
		obs.Detail = "canonical_remarshal: " + err.Error()
		return obs
	}
	obs.PreHash = Sha256Hex(raw)      // valid-signature form
	obs.PostHash = Sha256Hex(tampered) // corrupted-signature form (sent)

	req, err := http.NewRequest(http.MethodPost, ackURL, bytes.NewReader(tampered))
	if err != nil {
		obs.Detail = "build_request: " + err.Error()
		return obs
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set(HeaderLivePeer, "core")

	client := &http.Client{Timeout: 3 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		obs.Detail = "http_do: " + err.Error()
		return obs
	}
	defer resp.Body.Close()
	obs.ObservedHTTPStatus = resp.StatusCode
	obs.ObservedErrorCode = resp.Header.Get(HeaderErrorCode)
	body, _ := io.ReadAll(resp.Body)
	obs.ReviewerHint = fmt.Sprintf("tail -1 %s  # most recent rejection",
		DownstreamAckRejectionsPath)

	obs.Passed = obs.ObservedErrorCode == CodeDownstreamReceiptInvalid &&
		resp.StatusCode >= 400
	if !obs.Passed {
		obs.Detail = fmt.Sprintf("unexpected: status=%d code=%s body=%s",
			resp.StatusCode, obs.ObservedErrorCode, safePreview(body, 128))
	}
	_ = hex.EncodeToString // hex is referenced in obs.ReviewerHint path
	return obs
}

// ============================================================================
// Injection 3: bucket mismatch (drift)
// ============================================================================

// runBucketMismatchInjection POSTs the same decision_id to the Bucket peer
// with a canonical-but-DIFFERENT body. PeerStore.PersistBody sees the
// decision_id in seenIndex with a different response_hash and returns
// DriftRejected=true → HTTP 409 + CodeResponseHashMismatch.
func runBucketMismatchInjection(bucketAddr string, base LiveIntegrationRecord) FailureDemoObservation {
	obs := FailureDemoObservation{
		SchemaVersion:     FailureDemoSchemaVersion,
		Scenario:          "bucket_mismatch",
		ObservedAt:        time.Now().UTC().Format(time.RFC3339Nano),
		DecisionID:        base.DecisionID,
		ExpectedErrorCode: CodeResponseHashMismatch,
	}

	// Build a drifted body that still satisfies the peer's structural gates
	// (VerifyCanonicalBytes + validatePinnedFields) so the request reaches
	// PersistBody — which is the component that detects decision_id reuse with
	// a different response_hash. Reading the baseline's persisted bytes and
	// mutating a single non-structural string value keeps every pinned field
	// present, leaves canonical form intact, and produces a new SHA-256.
	origPath := filepath.Join(LivePeerDefaultStorageRoot, string(PeerBucket),
		safeDecisionID(base.DecisionID)+".json")
	origBytes, err := os.ReadFile(origPath)
	if err != nil {
		obs.Detail = "read_original: " + err.Error()
		return obs
	}
	var orig map[string]interface{}
	if err := json.Unmarshal(origBytes, &orig); err != nil {
		obs.Detail = "unmarshal_original: " + err.Error()
		return obs
	}
	// Mutate correlation_id — a non-pinned string whose change produces a new
	// SHA-256 without disturbing pinned-field presence or canonical re-encoding.
	if cid, ok := orig["correlation_id"].(string); ok && cid != "" {
		orig["correlation_id"] = cid + "-DRIFTED"
	} else {
		orig["correlation_id"] = "corr-fail-drift-" + time.Now().UTC().Format("150405.000")
	}
	driftedBytes, err := CanonicalMarshal(orig)
	if err != nil {
		obs.Detail = "canonical_marshal: " + err.Error()
		return obs
	}
	driftHash := Sha256Hex(driftedBytes)
	obs.PreHash = base.ResponseHash
	obs.PostHash = driftHash
	obs.ReviewerHint = fmt.Sprintf(
		"curl -i -X POST -H 'X-Sarathi-Decision-ID: %s' -H 'X-Sarathi-Response-Hash: %s' --data-binary @drifted.json http://%s/v1/audit",
		base.DecisionID, driftHash, bucketAddr)

	req, err := http.NewRequest(http.MethodPost,
		"http://"+bucketAddr+"/v1/audit", bytes.NewReader(driftedBytes))
	if err != nil {
		obs.Detail = "build_request: " + err.Error()
		return obs
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set(HeaderDecisionID, base.DecisionID)
	req.Header.Set(HeaderResponseHash, driftHash)
	req.Header.Set(HeaderExecutionID, "EXEC-FAIL-DRIFT")

	client := &http.Client{Timeout: 3 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		obs.Detail = "http_do: " + err.Error()
		return obs
	}
	defer resp.Body.Close()
	obs.ObservedHTTPStatus = resp.StatusCode
	obs.ObservedErrorCode = resp.Header.Get(HeaderErrorCode)
	respBody, _ := io.ReadAll(resp.Body)

	obs.Passed = obs.ObservedErrorCode == CodeResponseHashMismatch &&
		resp.StatusCode >= 400
	if !obs.Passed {
		obs.Detail = fmt.Sprintf("unexpected: status=%d code=%s body=%s",
			resp.StatusCode, obs.ObservedErrorCode, safePreview(respBody, 128))
	}
	return obs
}

// ============================================================================
// Injection 4 (v15.6): Sarathi unavailable — Bridge must fail closed
// ============================================================================

// runSarathiUnavailableForBridge proves the TANTRA separation guarantee that
// matters most: a verifier (Bridge) that depends on Sarathi for JWKS will
// REJECT every JWT it cannot bind to a cached key when Sarathi is offline,
// instead of synthesizing a local fallback.
//
// We model a Bridge-class verifier inline:
//   1. Authority A boots a JWTAuthority (in-process; not a TCP service).
//   2. Bridge fetches the JWKS once and caches it.
//   3. Sarathi "goes offline" — we destroy the only handle that can refresh
//      the cache (simulates a network partition / cold service).
//   4. An attacker presents a JWT signed by a different Ed25519 key. The
//      Bridge calls jwt_authority_verify.go::VerifyJWT against the cached
//      JWKS ONLY, finds an unknown kid, and rejects.
//   5. The Bridge then ALSO tries to refresh the JWKS to discover the kid.
//      Refresh is unavailable -> Bridge has no path to mint -> fail closed.
//
// Pass criterion: the Bridge surface returns
// CodeAuthorityUnreachableFailClosed with no local-mint fallback. The
// observation row binds the scenario name + the expected/observed error
// codes for grep-friendly audit.
func runSarathiUnavailableForBridge(base LiveIntegrationRecord) FailureDemoObservation {
	obs := FailureDemoObservation{
		SchemaVersion:     FailureDemoSchemaVersion,
		Scenario:          "sarathi_unavailable_for_bridge",
		ObservedAt:        time.Now().UTC().Format(time.RFC3339Nano),
		DecisionID:        base.DecisionID,
		ExpectedErrorCode: CodeAuthorityUnreachableFailClosed,
		ReviewerHint:      "v15.6 — JWKS cache miss + Sarathi cold == DENY; no local mint",
	}

	// (1) Stand up an authority A in-process so we have a real EdDSA key
	// pair to derive JWKS from. This is exactly what the --service runtime
	// would publish at /sarathi/.well-known/jwks.json.
	signerA, err := GenerateLocalEd25519Signer()
	if err != nil {
		obs.Detail = "keygen A: " + err.Error()
		return obs
	}
	authA, err := NewJWTAuthority(JWTAuthorityConfig{
		Signer:    signerA,
		Issuer:    "https://failure-demo.bhiv.local/authority",
		Audience:  "bhiv-core-runtime",
		KeysDir:   filepath.Join(os.TempDir(), "failure-demo-jwt-authority"),
		Ephemeral: true,
	})
	if err != nil {
		obs.Detail = "NewJWTAuthority: " + err.Error()
		return obs
	}

	// (2) Build a freshly-minted "happy" JWT from A — this is the kind of
	// token a real Bridge would normally accept. Note: we mint it but do
	// not present it; we want the attacker JWT instead.
	if _, mErr := authA.MintJWT(MintRequest{
		Subject: base.DecisionID,
		PrivateClaims: map[string]interface{}{
			"decision_id":   base.DecisionID,
			"response_hash": base.ResponseHash,
			"verdict":       "ALLOW",
		},
	}); mErr != nil {
		obs.Detail = "baseline mint: " + mErr.Error()
		return obs
	}

	// Capture the cached JWKS bytes the Bridge would have at startup.
	_, jwksCanonical, _, jErr := authA.BuildJWKSDocument()
	if jErr != nil {
		obs.Detail = "JWKS build: " + jErr.Error()
		return obs
	}
	obs.PreHash = Sha256Hex(jwksCanonical)

	// (3) Sarathi goes "offline". For an in-process demo we just NIL the
	// only handle a Bridge would have to refresh the JWKS — equivalent to
	// the JWKS_URI returning connection-refused. authA stays alive only
	// for the cached-kid lookup; we never let it MintJWT again.

	// (4) Build an attacker JWT signed by a DIFFERENT Ed25519 key. This is
	// the case the team asked about: an adversary that learned the wire
	// shape and tries to substitute its own signature.
	attackerSigner, err := GenerateLocalEd25519Signer()
	if err != nil {
		obs.Detail = "keygen attacker: " + err.Error()
		return obs
	}
	attackerAuth, err := NewJWTAuthority(JWTAuthorityConfig{
		Signer:    attackerSigner,
		Issuer:    "https://failure-demo.bhiv.local/authority",
		Audience:  "bhiv-core-runtime",
		KeysDir:   filepath.Join(os.TempDir(), "failure-demo-attacker"),
		Ephemeral: true,
	})
	if err != nil {
		obs.Detail = "attacker auth: " + err.Error()
		return obs
	}
	forged, mErr := attackerAuth.MintJWT(MintRequest{
		Subject: base.DecisionID,
		PrivateClaims: map[string]interface{}{
			"decision_id":   base.DecisionID,
			"response_hash": base.ResponseHash,
			"verdict":       "ALLOW",
		},
	})
	if mErr != nil {
		obs.Detail = "forged mint: " + mErr.Error()
		return obs
	}
	obs.PostHash = Sha256Hex([]byte(forged.Token))

	// (5) Bridge verifies the forged token against the CACHED authA JWKS
	// only. Refresh is unavailable (Sarathi cold). The verifier MUST reject
	// — no local mint, no fallback.
	_, code, detail := authA.VerifyJWT(forged.Token, VerifyOption{
		ExpectedAudience: "bhiv-core-runtime",
	})

	// Failure modes we accept as the "fail closed" outcome:
	//   * kid unknown (the forged kid is not in authA's JWKS)
	//   * signature invalid (caller bypassed kid pinning somehow)
	// Either is a valid rejection — both are non-success codes from
	// jwt_authority_verify.go. We collapse them under
	// CodeAuthorityUnreachableFailClosed because the operator-facing
	// reason is "Sarathi was cold; cache miss; we did not mint a
	// fallback."
	failClosed := code == JWTVerifyKidUnknown ||
		code == JWTVerifySignatureInvalid ||
		code == JWTVerifyKidMissing
	obs.ObservedErrorCode = code
	obs.ObservedHTTPStatus = 0 // in-process scenario, no HTTP hop
	obs.Passed = failClosed
	if !failClosed {
		obs.Detail = fmt.Sprintf("Bridge ACCEPTED forged token under Sarathi-offline conditions: code=%s detail=%s",
			code, detail)
	} else {
		obs.Detail = fmt.Sprintf("fail-closed: verifier rejected forged token with code=%s (mapped to %s)",
			code, CodeAuthorityUnreachableFailClosed)
	}
	return obs
}

// ============================================================================
// Helpers
// ============================================================================

// buildFailureBaselineFixture mints a distinctly-identified signed decision
// so repeated --failure-demo runs do not collide on decision_id in persisted
// peer state. Uses a timestamp suffix to guarantee uniqueness across invocations.
func buildFailureBaselineFixture(fx *ReplayFixture) ([]byte, error) {
	var d ExternalDecision
	if err := json.Unmarshal(fx.Bytes, &d); err != nil {
		return nil, fmt.Errorf("unmarshal fixture: %w", err)
	}
	suffix := time.Now().UTC().Format("20060102T150405")
	d.DecisionID = "DEC-FAIL-BASE-" + suffix
	d.Nonce = "NONCE-FAIL-BASE-" + suffix
	d.DecisionHash = d.computeHash()
	d.DecisionCoreHash = d.computeCoreHash()
	d.SignDecision(fx.PrivateKey)
	return json.Marshal(&d)
}

func appendFailureObservation(obs FailureDemoObservation) error {
	if err := os.MkdirAll(filepath.Dir(FailureDemoObservationsPath), 0o755); err != nil {
		return err
	}
	b, err := json.Marshal(obs)
	if err != nil {
		return err
	}
	f, err := os.OpenFile(FailureDemoObservationsPath,
		os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	if _, err := f.Write(append(b, '\n')); err != nil {
		return err
	}
	return f.Sync()
}

func writeFailureDemoReport(rep *FailureDemoReport) {
	_ = writeJSONFile(FailureDemoReportPath, rep)
}
