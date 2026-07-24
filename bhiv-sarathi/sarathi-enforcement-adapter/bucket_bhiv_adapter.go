package main

// bucket_bhiv_adapter.go — Sarathi → BHIV Bucket outbound adapter.
//
// The real BHIV Bucket (Siddhesh) is the SHARED append-only chain for the BHIV
// ecosystem (SVACS, NICAI, Core, InsightFlow). It cannot be modified for any
// one product, so Sarathi adapts to Bucket's fixed contract and keeps its
// strong cryptographic guarantees on the SARATHI SIDE. This adapter is
// ADDITIVE — it does not touch the existing BucketClient / peer_bucket.go
// paths. It implements the conflict-free split per Bucket's canonical
// integration doc (BUCKET-SARATHI-001, 2026-06-19):
//
//   - Standard BHIV envelope, schema_version = "1.0.0", same shape SVACS uses.
//     All Sarathi semantics live INSIDE `payload` (Bucket treats payload as
//     opaque JSON). Identity is carried by `source_module_id`, NOT by extra
//     top-level fields — Bucket validates structure and may reject unknown
//     top-level keys.
//   - artifact_id = deterministic UUIDv5 from decision_id (Bucket dedups on
//     artifact_id, NOT decision_id; same decision retried => same artifact_id).
//   - parent_hash fetched live from GET /bucket/latest-hash (omitted on genesis
//     when artifact_count == 0).
//
// RESPONSIBILITY SPLIT (no conflict — each system does what it was built for):
//   - Bucket   = chain custody (server `hash`, `parent_hash`, append-only log).
//   - Sarathi  = the seal + the witness:
//       * mints minted_body_hash (transport) + minted_response_hash (decision)
//         LOCALLY before send and stores them keyed by decision_id;
//       * after the write, READS THE ARTIFACT BACK and re-verifies trace_id /
//         decision_id / canonical_response_b64 / response-hash byte-identity —
//         this is the independent verification that recovers what Sarathi
//         previously expected Bucket to do on receipt;
//       * issues its OWN Ed25519-signed custody receipt
//         (sarathi.custody.receipt/v1.0) under Sarathi's enforcement key.
//
// Bucket does NOT: store wire bytes verbatim, verify X-Sarathi-* hashes,
// return an Ed25519 receipt, or POST to /v1/downstream-ack. None of those will
// come — they are outside Bucket's role, and Sarathi no longer depends on them.
//
// TAG: bucket-bhiv-align-v2

import (
	"bytes"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"path/filepath"
	"strings"
	"time"

	"github.com/google/uuid"
)

// Bucket envelope constants (aligned to Bucket's canonical shared shape).
const (
	BucketBHIVSchemaVersion  = "1.0.0"
	BucketBHIVSourceModuleID = "sarathi.enforcement_adapter"
	BucketBHIVArtifactType   = "enforcement_decision"
	// BucketCustodyReceiptSchema is the Sarathi-OWNED, Sarathi-SIGNED custody
	// receipt (Bucket never signs or posts a receipt — Sarathi witnesses its
	// own write per BUCKET-SARATHI-001 Step 5).
	BucketCustodyReceiptSchema = "sarathi.custody.receipt/v1.0"
)

// Bucket proof-artifact locations (Sarathi-side, local).
const (
	BucketProofDir          = "proof_logs/bucket"
	BucketTransmitLog       = "proof_logs/bucket/bucket_transmissions.jsonl"
	BucketReceiptLog        = "proof_logs/bucket/sarathi_bucket_receipts.jsonl"
)

// BucketBHIVPayload is the inner enforcement record Bucket stores opaque.
// trace_id lives HERE (not top-level): the deployed Bucket rejects trace_id as
// an unknown top-level envelope field (see BucketBHIVEnvelope note).
type BucketBHIVPayload struct {
	DecisionID           string   `json:"decision_id"`
	TraceID              string   `json:"trace_id"`
	Verdict              string   `json:"verdict"`
	EvaluatorID          string   `json:"evaluator_id"`
	DecisionHash         string   `json:"decision_hash"`
	DecisionCoreHash     string   `json:"decision_core_hash"`
	EnforcementHash      string   `json:"enforcement_hash"`
	ResponseHash         string   `json:"response_hash"`
	ChainBindingHash     string   `json:"chain_binding_hash"`
	PolicyReference      string   `json:"policy_reference"`
	InputHash            string   `json:"input_hash"`
	AgentID              string   `json:"agent_id"`
	ResourceID           string   `json:"resource_id"`
	Action               string   `json:"action"`
	Obligations          []string `json:"obligations"`
	EnforcedAt           string   `json:"enforced_at"`
	SealedAt             string   `json:"sealed_at"`
	CanonicalResponseB64 string   `json:"canonical_response_b64"`
}

// BucketBHIVEnvelope is the exact wire shape Bucket requires — the SHARED BHIV
// envelope (identical to SVACS/NICAI). NO product-specific top-level fields:
// Sarathi identity is carried by source_module_id, and all Sarathi semantics
// (INCLUDING trace_id) live inside Payload (opaque to Bucket).
//
// trace_id is INSIDE payload, NOT top-level. The deployed Bucket's GET
// /bucket/schema-info advertises allowed_envelope_fields = {artifact_id,
// timestamp_utc, schema_version, source_module_id, artifact_type, parent_hash,
// payload, hash} and rejects every other top-level key as "Schema drift".
// (BUCKET-SARATHI-001 lists trace_id top-level, but the live deployment does
// NOT accept it — payload is the contract-safe home, and Bucket stores payload
// opaque so nothing is lost.)
type BucketBHIVEnvelope struct {
	ArtifactID     string            `json:"artifact_id"`
	TimestampUTC   string            `json:"timestamp_utc"`
	SchemaVersion  string            `json:"schema_version"`
	SourceModuleID string            `json:"source_module_id"`
	ArtifactType   string            `json:"artifact_type"`
	ParentHash     string            `json:"parent_hash,omitempty"`
	Payload        BucketBHIVPayload `json:"payload"`
}

// BucketLatestHash is the parsed GET /bucket/latest-hash response. Fields are
// parsed liberally; Bucket may add others.
type BucketLatestHash struct {
	LastHash      string `json:"last_hash"`
	ArtifactCount int    `json:"artifact_count"`
}

// BucketSyncResponse is the synchronous 200 body Bucket returns on a write.
type BucketSyncResponse struct {
	Success     bool   `json:"success"`
	ArtifactID  string `json:"artifact_id"`
	Hash        string `json:"hash"`
	ParentHash  string `json:"parent_hash"`
	Timestamp   string `json:"timestamp"`
	StorageType string `json:"storage_type"`
	Message     string `json:"message"`
}

// SarathiBucketReceipt is the Sarathi-OWNED, Sarathi-SIGNED custody receipt
// (BUCKET-SARATHI-001 Step 5). Sarathi builds, signs, and persists this after a
// successful Bucket write + read-back verification — Bucket does NOT post a
// receipt back to /v1/downstream-ack and Sarathi does not wait for one.
//
// The Ed25519 signature is computed over the canonical bytes of every field
// EXCEPT receipt_signature (which is "" at signing time), under Sarathi's
// enforcement key. peer_public_key_hex + key_id let any verifier check it
// without prior key exchange beyond Sarathi's published enforcement key.
type SarathiBucketReceipt struct {
	SchemaVersion      string `json:"schema_version"`
	Peer               string `json:"peer"`
	ExecutionID        string `json:"execution_id"`
	DecisionID         string `json:"decision_id"`
	TraceID            string `json:"trace_id"`
	BucketArtifactID   string `json:"bucket_artifact_id"`
	BucketHash         string `json:"bucket_hash"`
	MintedBodyHash     string `json:"minted_body_hash"`
	MintedResponseHash string `json:"minted_response_hash"`
	ReadBackVerified   bool   `json:"read_back_verified"`
	PersistedAt        string `json:"persisted_at"`
	PeerPublicKeyHex   string `json:"peer_public_key_hex"`
	KeyID              string `json:"key_id"`
	ReceiptSignature   string `json:"receipt_signature"`
}

// BucketReadbackVerification is the Sarathi-owned post-write proof
// (BUCKET-SARATHI-001 Step 4). Sarathi GETs the stored artifact and confirms,
// byte-for-byte, that Bucket holds exactly what Sarathi sealed. This recovers
// the independent verification Sarathi previously expected Bucket to perform.
type BucketReadbackVerification struct {
	Fetched           bool   `json:"fetched"`
	TraceIDMatch      bool   `json:"trace_id_match"`
	DecisionIDMatch   bool   `json:"decision_id_match"`
	CanonicalB64Match bool   `json:"canonical_b64_match"`
	ResponseHashMatch bool   `json:"response_hash_match"`
	ComputeHashChecked bool  `json:"compute_hash_checked"`
	ComputeHashMatch  bool   `json:"compute_hash_match"`
	ChainVerified     bool   `json:"chain_verified"`
	AllVerified       bool   `json:"all_verified"`
	Note              string `json:"note,omitempty"`
}

// BucketTransmitResult is the full outcome of one Sarathi → Bucket exchange.
type BucketTransmitResult struct {
	ArtifactID         string                `json:"artifact_id"`
	DecisionID         string                `json:"decision_id"`
	TraceID            string                `json:"trace_id"`
	ParentHashUsed     string                `json:"parent_hash_used"`
	MintedBodyHash     string                `json:"minted_body_hash"`
	MintedResponseHash string                `json:"minted_response_hash"`
	HTTPStatus         int                         `json:"http_status"`
	BucketResponse     *BucketSyncResponse         `json:"bucket_response,omitempty"`
	BucketHashMatch    bool                        `json:"bucket_hash_matches_minted_body"`
	ChainVerified      bool                        `json:"chain_verified"`
	ReadBack           *BucketReadbackVerification `json:"read_back,omitempty"`
	Receipt            *SarathiBucketReceipt       `json:"receipt,omitempty"`
	Envelope           *BucketBHIVEnvelope   `json:"envelope"`
	SentBody           string                `json:"-"`
	Note               string                `json:"note"`
	TransmittedAt      string                `json:"transmitted_at"`
}

// BucketArtifactIDFor derives the deterministic UUIDv5 artifact_id from a
// decision_id. Same decision_id → same artifact_id (retry safety); Bucket
// dedups on this value.
func BucketArtifactIDFor(decisionID string) string {
	return uuid.NewSHA1(uuid.NameSpaceOID, []byte("sarathi.bucket.artifact:"+decisionID)).String()
}

// bucketJoin joins a base URL with a path, trimming any trailing slash.
func bucketJoin(base, path string) string {
	return strings.TrimRight(strings.TrimSpace(base), "/") + path
}

// BucketBHIVHeaders returns the optional X-Sarathi-* metadata headers. Bucket
// does not read them today (they are advisory), but they aid cross-system
// tracing and any future verification.
func BucketBHIVHeaders(env *BucketBHIVEnvelope, executionID, bodyHash, responseHash string) map[string]string {
	return map[string]string{
		"X-Sarathi-Decision-ID":        env.Payload.DecisionID,
		"X-Sarathi-Execution-ID":       executionID,
		"X-Sarathi-Trace-ID":           env.Payload.TraceID,
		"X-Sarathi-Body-Hash":          bodyHash,
		"X-Sarathi-Response-Hash":      responseHash,
		"X-Sarathi-Chain-Binding-Hash": env.Payload.ChainBindingHash,
		"X-Sarathi-Enforcement-Hash":   env.Payload.EnforcementHash,
		"X-Sarathi-Schema-Version":     env.SchemaVersion,
		"X-Sarathi-Sealed-At":          env.Payload.SealedAt,
	}
}

// MintBucketHashes returns the canonical wire bytes Sarathi will send, the
// SHA-256 over those bytes (body_hash), and the SHA-256 over the decoded
// canonical_response_b64 (response_hash). The body sent on the wire is exactly
// the canonical bytes returned here, so what Sarathi hashes equals what it
// sends.
func MintBucketHashes(env *BucketBHIVEnvelope) (canonicalBody []byte, bodyHash, responseHash string, err error) {
	canonicalBody, err = CanonicalMarshal(env)
	if err != nil {
		return nil, "", "", fmt.Errorf("bucket: canonical marshal: %w", err)
	}
	bodyHash = Sha256Hex(canonicalBody)
	decoded, derr := base64.StdEncoding.DecodeString(env.Payload.CanonicalResponseB64)
	if derr != nil {
		return nil, "", "", fmt.Errorf("bucket: decode canonical_response_b64: %w", derr)
	}
	responseHash = Sha256Hex(decoded)
	return canonicalBody, bodyHash, responseHash, nil
}

// FetchBucketLatestHash GETs {base}/bucket/latest-hash and returns the parsed
// chain head. On any error it returns a zero-value head with artifact_count=0
// (genesis) plus the error, so callers can decide to proceed on genesis.
func FetchBucketLatestHash(httpc *http.Client, base string) (*BucketLatestHash, error) {
	url := bucketJoin(base, "/bucket/latest-hash")
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return &BucketLatestHash{}, fmt.Errorf("bucket latest-hash: build request: %w", err)
	}
	req.Header.Set("ngrok-skip-browser-warning", "true")
	resp, err := httpc.Do(req)
	if err != nil {
		return &BucketLatestHash{}, fmt.Errorf("bucket latest-hash: GET %s: %w", url, err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return &BucketLatestHash{}, fmt.Errorf("bucket latest-hash: status=%d body=%s",
			resp.StatusCode, truncateForLog(string(body), 256))
	}
	var lh BucketLatestHash
	if err := json.Unmarshal(body, &lh); err != nil {
		return &BucketLatestHash{}, fmt.Errorf("bucket latest-hash: decode: %w (body=%s)",
			err, truncateForLog(string(body), 256))
	}
	return &lh, nil
}

// ConfirmBucketArtifact GETs {base}/bucket/artifact/{artifactID} and reports
// whether Bucket marks the stored artifact chain_verified:true. Parsed
// liberally — a missing field is treated as not-verified rather than an error.
func ConfirmBucketArtifact(httpc *http.Client, base, artifactID string) (bool, []byte, error) {
	url := bucketJoin(base, "/bucket/artifact/"+artifactID)
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return false, nil, fmt.Errorf("bucket confirm: build request: %w", err)
	}
	req.Header.Set("ngrok-skip-browser-warning", "true")
	resp, err := httpc.Do(req)
	if err != nil {
		return false, nil, fmt.Errorf("bucket confirm: GET %s: %w", url, err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return false, body, fmt.Errorf("bucket confirm: status=%d body=%s",
			resp.StatusCode, truncateForLog(string(body), 256))
	}
	var parsed map[string]interface{}
	if err := json.Unmarshal(body, &parsed); err != nil {
		return false, body, nil
	}
	if v, ok := parsed["chain_verified"].(bool); ok {
		return v, body, nil
	}
	// Some Bucket builds nest under "artifact" — look one level down.
	if inner, ok := parsed["artifact"].(map[string]interface{}); ok {
		if v, ok := inner["chain_verified"].(bool); ok {
			return v, body, nil
		}
	}
	return false, body, nil
}

// ComputeBucketHash POSTs an envelope body to {base}/bucket/compute-hash and
// returns Bucket's authority hash for it. This is the OPTIONAL preview /
// read-back authority-hash check (BUCKET-SARATHI-001 Step 3/4). Best-effort:
// returns ok=false (not an error) when the endpoint is absent (404) so callers
// can proceed without it.
func ComputeBucketHash(httpc *http.Client, base string, body []byte) (hash string, ok bool, err error) {
	url := bucketJoin(base, "/bucket/compute-hash")
	req, rerr := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	if rerr != nil {
		return "", false, fmt.Errorf("bucket compute-hash: build request: %w", rerr)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("ngrok-skip-browser-warning", "true")
	resp, derr := httpc.Do(req)
	if derr != nil {
		return "", false, fmt.Errorf("bucket compute-hash: POST %s: %w", url, derr)
	}
	defer resp.Body.Close()
	rb, _ := io.ReadAll(resp.Body)
	if resp.StatusCode == http.StatusNotFound {
		return "", false, nil // endpoint not offered — optional, skip
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return "", false, fmt.Errorf("bucket compute-hash: status=%d body=%s",
			resp.StatusCode, truncateForLog(string(rb), 256))
	}
	var parsed map[string]interface{}
	if err := json.Unmarshal(rb, &parsed); err != nil {
		return "", false, fmt.Errorf("bucket compute-hash: decode: %w", err)
	}
	if h, ok := parsed["hash"].(string); ok && h != "" {
		return h, true, nil
	}
	return "", false, nil
}

// bucketExtractEnvelopeFields pulls trace_id and payload.{decision_id,
// canonical_response_b64} out of a Bucket read-back body. Bucket may return the
// envelope directly, or nested under "artifact"/"data"/"payload" — this probes
// the common shapes liberally so the verification is robust to wrapper drift.
func bucketExtractEnvelopeFields(body []byte) (traceID, decisionID, canonicalB64 string, chainVerified bool) {
	var top map[string]interface{}
	if err := json.Unmarshal(body, &top); err != nil {
		return "", "", "", false
	}
	// chain_verified may live at the top level or one level down.
	if v, ok := top["chain_verified"].(bool); ok {
		chainVerified = v
	}
	// Find the object that actually holds trace_id / payload.
	candidates := []map[string]interface{}{top}
	for _, key := range []string{"artifact", "data", "record", "envelope"} {
		if inner, ok := top[key].(map[string]interface{}); ok {
			candidates = append([]map[string]interface{}{inner}, candidates...)
			if v, ok := inner["chain_verified"].(bool); ok {
				chainVerified = v
			}
		}
	}
	for _, c := range candidates {
		if traceID == "" {
			if t, ok := c["trace_id"].(string); ok {
				traceID = t
			}
		}
		if pl, ok := c["payload"].(map[string]interface{}); ok {
			// trace_id now lives inside payload (Bucket rejects it top-level).
			if t, ok := pl["trace_id"].(string); ok && traceID == "" {
				traceID = t
			}
			if d, ok := pl["decision_id"].(string); ok && decisionID == "" {
				decisionID = d
			}
			if cb, ok := pl["canonical_response_b64"].(string); ok && canonicalB64 == "" {
				canonicalB64 = cb
			}
		}
	}
	return traceID, decisionID, canonicalB64, chainVerified
}

// VerifyBucketReadback GETs the stored artifact and re-verifies byte-identity
// (BUCKET-SARATHI-001 Step 4): trace_id, payload.decision_id, and
// canonical_response_b64 are unchanged, and SHA-256 over the decoded
// canonical_response_b64 equals the locally-minted response hash. When the
// optional /bucket/compute-hash endpoint exists, it also confirms Bucket's
// authority hash on the read-back equals the hash returned at write time.
//
// AllVerified is the Sarathi-owned security gate: it is true ONLY when every
// content check passes. The compute-hash check is advisory (does not gate
// AllVerified) because the endpoint is optional.
func VerifyBucketBHIVReadback(
	httpc *http.Client,
	base, artifactID, wantTraceID, wantDecisionID, wantCanonicalB64, mintedResponseHash, bucketHash string,
) *BucketReadbackVerification {
	rb := &BucketReadbackVerification{}
	verified, body, err := ConfirmBucketArtifact(httpc, base, artifactID)
	if err != nil {
		rb.Note = "read-back GET failed: " + err.Error()
		return rb
	}
	rb.Fetched = true
	rb.ChainVerified = verified

	gotTrace, gotDecision, gotB64, chainV := bucketExtractEnvelopeFields(body)
	if chainV {
		rb.ChainVerified = true
	}
	rb.TraceIDMatch = gotTrace == wantTraceID
	rb.DecisionIDMatch = gotDecision == wantDecisionID
	rb.CanonicalB64Match = gotB64 == wantCanonicalB64

	if gotB64 != "" {
		if decoded, derr := base64.StdEncoding.DecodeString(gotB64); derr == nil {
			rb.ResponseHashMatch = Sha256Hex(decoded) == mintedResponseHash
		}
	}

	// Optional authority-hash cross-check on the read-back body.
	if ah, ok, cerr := ComputeBucketHash(httpc, base, body); cerr == nil && ok {
		rb.ComputeHashChecked = true
		rb.ComputeHashMatch = strings.EqualFold(strings.TrimSpace(ah), strings.TrimSpace(bucketHash))
	}

	rb.AllVerified = rb.Fetched && rb.TraceIDMatch && rb.DecisionIDMatch &&
		rb.CanonicalB64Match && rb.ResponseHashMatch
	if !rb.AllVerified && rb.Note == "" {
		rb.Note = fmt.Sprintf("read-back mismatch: trace=%v decision=%v b64=%v resp_hash=%v",
			rb.TraceIDMatch, rb.DecisionIDMatch, rb.CanonicalB64Match, rb.ResponseHashMatch)
	}
	return rb
}

// signSarathiBucketReceipt fills peer_public_key_hex + key_id, canonicalizes the
// receipt with receipt_signature="" (RFC 8785 via CanonicalMarshal), signs the
// canonical bytes under Sarathi's enforcement key via the active provider, and
// sets receipt_signature to the hex-encoded signature. Returns an error if the
// enforcement signer is unavailable (the receipt is still usable unsigned, but
// callers should surface the failure).
func signSarathiBucketReceipt(r *SarathiBucketReceipt) error {
	if activeProvider == nil {
		return fmt.Errorf("bucket receipt: active crypto provider not initialised")
	}
	priv, keyID, err := loadSarathiEnforcementSigner()
	if err != nil {
		return fmt.Errorf("bucket receipt: load signer: %w", err)
	}
	r.KeyID = keyID
	r.PeerPublicKeyHex = priv.Public().Encoded()
	r.ReceiptSignature = ""
	signable, err := CanonicalMarshal(r)
	if err != nil {
		return fmt.Errorf("bucket receipt: canonical marshal: %w", err)
	}
	sig, err := activeProvider.Sign(signable, priv)
	if err != nil {
		return fmt.Errorf("bucket receipt: sign: %w", err)
	}
	r.ReceiptSignature = hex.EncodeToString(sig)
	return nil
}

// TransmitToBucket runs the full aligned exchange against a live Bucket base
// URL: fetch chain head → build + mint → POST → parse sync 200 → read-back
// verify (Step 4) → build, sign, and persist the Sarathi-owned custody receipt
// (Step 5). It never marks success on anything other than a real 2xx with
// success:true.
func TransmitToBucket(httpc *http.Client, base string, env *BucketBHIVEnvelope, executionID string, now time.Time) (*BucketTransmitResult, error) {
	if httpc == nil {
		httpc = &http.Client{Timeout: EcosystemClientDefaultTimeout}
	}
	res := &BucketTransmitResult{
		ArtifactID:    env.ArtifactID,
		DecisionID:    env.Payload.DecisionID,
		TraceID:       env.Payload.TraceID,
		Envelope:      env,
		TransmittedAt: now.UTC().Format(time.RFC3339Nano),
	}

	// 1. Chain head — set parent_hash unless genesis.
	lh, lerr := FetchBucketLatestHash(httpc, base)
	if lerr != nil {
		res.Note = "latest-hash fetch failed: " + lerr.Error()
		return res, lerr
	}
	if lh.ArtifactCount > 0 && strings.TrimSpace(lh.LastHash) != "" {
		env.ParentHash = lh.LastHash
	} else {
		env.ParentHash = "" // genesis — omitted on the wire (omitempty)
	}
	res.ParentHashUsed = env.ParentHash

	// 2. Mint hashes over the exact canonical bytes we will send.
	canonicalBody, bodyHash, responseHash, merr := MintBucketHashes(env)
	if merr != nil {
		res.Note = merr.Error()
		return res, merr
	}
	res.MintedBodyHash = bodyHash
	res.MintedResponseHash = responseHash
	res.SentBody = string(canonicalBody)

	// 3. POST /bucket/artifact.
	url := bucketJoin(base, "/bucket/artifact")
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(canonicalBody))
	if err != nil {
		res.Note = "build request: " + err.Error()
		return res, err
	}
	req.ContentLength = int64(len(canonicalBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("ngrok-skip-browser-warning", "true")
	for k, v := range BucketBHIVHeaders(env, executionID, bodyHash, responseHash) {
		req.Header.Set(k, v)
	}
	resp, err := httpc.Do(req)
	if err != nil {
		res.Note = "POST failed: " + err.Error()
		return res, err
	}
	respBody, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	res.HTTPStatus = resp.StatusCode
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		res.Note = fmt.Sprintf("Bucket returned HTTP %d (not 2xx): %s",
			resp.StatusCode, truncateForLog(string(respBody), 256))
		return res, fmt.Errorf("bucket: %s", res.Note)
	}
	var sync BucketSyncResponse
	if err := json.Unmarshal(respBody, &sync); err != nil {
		res.Note = "200 OK but undecodable sync body: " + truncateForLog(string(respBody), 256)
		return res, fmt.Errorf("bucket: %s", res.Note)
	}
	res.BucketResponse = &sync
	res.BucketHashMatch = strings.EqualFold(strings.TrimSpace(sync.Hash), bodyHash)

	// 4. Read-back verification (Step 4) — Sarathi independently proves Bucket
	// holds exactly the sealed bytes. This is the security gate.
	rb := VerifyBucketBHIVReadback(httpc, base, sync.ArtifactID,
		env.Payload.TraceID, env.Payload.DecisionID, env.Payload.CanonicalResponseB64,
		responseHash, sync.Hash)
	res.ReadBack = rb
	res.ChainVerified = rb.ChainVerified

	// 5. Sarathi-owned, Sarathi-SIGNED custody receipt (Step 5) — built and
	// persisted locally; Bucket never signs or posts this.
	receipt := &SarathiBucketReceipt{
		SchemaVersion:      BucketCustodyReceiptSchema,
		Peer:               "sarathi",
		ExecutionID:        executionID,
		DecisionID:         env.Payload.DecisionID,
		TraceID:            env.Payload.TraceID,
		BucketArtifactID:   sync.ArtifactID,
		BucketHash:         sync.Hash,
		MintedBodyHash:     bodyHash,
		MintedResponseHash: responseHash,
		ReadBackVerified:   rb.AllVerified,
		PersistedAt:        time.Now().UTC().Format(time.RFC3339Nano),
	}
	if serr := signSarathiBucketReceipt(receipt); serr != nil {
		// Receipt is still recorded unsigned; surface the signing gap in the note.
		res.Note = "WARN custody receipt unsigned: " + serr.Error() + "; "
	}
	res.Receipt = receipt
	res.Note += fmt.Sprintf("HTTP %d success=%v bucket_hash=%s read_back_verified=%v chain_verified=%v",
		resp.StatusCode, sync.Success, sync.Hash, rb.AllVerified, res.ChainVerified)
	return res, nil
}

// PersistBucketTransmit appends the transmission + receipt to the append-only
// logs and writes a standalone per-artifact file. Best-effort: errors are
// returned but the result is already complete.
func PersistBucketTransmit(res *BucketTransmitResult) (string, error) {
	if err := cetAppendJSONLine(BucketTransmitLog, res); err != nil {
		return "", err
	}
	if res.Receipt != nil {
		_ = cetAppendJSONLine(BucketReceiptLog, res.Receipt)
	}
	standalone := filepath.Join(BucketProofDir, fmt.Sprintf("bucket_transmit_%s.json", safeFileToken(res.DecisionID)))
	if err := writeIndentedJSON(standalone, res); err != nil {
		return "", err
	}
	return standalone, nil
}
