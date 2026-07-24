// ecosystem_clients.go (v15.2 Real-BHIV Ecosystem Wiring)
//
// HTTP clients for the three real BHIV peer systems (Core, InsightFlow,
// Bucket) implementing the wire contract against BHIV's URL surface (see
// ecosystem_endpoints.go).
//
// Each client method:
//   - sends the envelope's canonical bytes verbatim (RFC 8785, no re-marshal)
//   - sets the 9 standard X-Sarathi-* propagation headers
//   - re-verifies the X-Sarathi-Ack-Hash echo
//   - returns *PropagationStopError on any byte drift (preserves INV-PROP-04)
//   - returns the parsed peer ack on success
//
// These clients are the production replacement for the Sarathi-internal peer
// simulators (peer_*.go). The simulators remain in the binary as conformance
// reference and as the default --live-integration target; when the operator
// sets the SARATHI_*_URL env vars, --live-integration / --parallel-execute /
// --distributed-integration switch to these clients automatically via
// WireBHIVEcosystemTargets in multi_system_router_propagation.go.
//
// TAG: ecosystem-wiring

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// EnvInsightAPIKey is the outbound API key Sarathi presents to InsightFlow on
// every call (X-API-Key header). InsightFlow issues this key out-of-band; the
// FULL value (including any owner-label prefix such as "vijay_insightflow_")
// is the secret and is sent verbatim. Empty => no header is attached.
const EnvInsightAPIKey = "SARATHI_INSIGHT_API_KEY"

// EcosystemClientDefaultTimeout caps every outbound BHIV call. Override via
// SARATHI_ECOSYSTEM_TIMEOUT_MS at boot.
//
// v15.4: bumped from 5s -> 15s to accommodate ngrok free-tier latency
// (cold-start + public-internet RTT).
const EcosystemClientDefaultTimeout = 15 * time.Second

// EcosystemAck is the parsed response from a BHIV peer's POST handler. The
// shape is intentionally minimal — peers may return additional fields, which
// are preserved in Raw for audit but not interpreted.
type EcosystemAck struct {
	Peer        string          `json:"peer"`
	AckHash     string          `json:"ack_hash"`
	DecisionID  string          `json:"decision_id,omitempty"`
	StoragePath string          `json:"storage_path,omitempty"`
	Status      int             `json:"status"`
	HTTPHeaders http.Header     `json:"-"`
	Raw         json.RawMessage `json:"-"`
}

// ----------------------------------------------------------------------------
// CoreClient — 3 endpoints
// ----------------------------------------------------------------------------

// CoreClient maps the three BHIV Core endpoints onto Sarathi's propagation
// envelope. Methods preserve INV-PROP-04 (byte equality across hops).
type CoreClient struct {
	endpoints CoreEndpoints
	httpc     *http.Client
}

// NewCoreClient returns a Core client using the configured timeout.
func NewCoreClient(eps CoreEndpoints) *CoreClient {
	return &CoreClient{
		endpoints: eps,
		httpc:     &http.Client{Timeout: EcosystemClientDefaultTimeout},
	}
}

// Enforce POSTs the sealed canonical bytes to BHIV Core's /v1/enforce
// endpoint. Verifies the ACK hash echo. Used as the primary in-chain hop.
func (c *CoreClient) Enforce(env *PropagationEnvelope) (*EcosystemAck, error) {
	return postEnvelope(c.httpc, c.endpoints.Enforce, env, "core", false)
}

// Execute POSTs the same envelope to BHIV Core's /v1/execute endpoint. This is
// the action endpoint exercised by --parallel-execute SARATHI_PARALLEL_TARGET=bhiv
// mode and InsightFlow's /core_execute side-channel.
func (c *CoreClient) Execute(env *PropagationEnvelope) (*EcosystemAck, error) {
	return postEnvelope(c.httpc, c.endpoints.Execute, env, "core", false)
}

// Health GETs BHIV Core's /health endpoint. Returns nil on a 200; an error
// otherwise (used by service_runtime_cli.go BHIV pre-flight in production).
func (c *CoreClient) Health() error {
	return probeHealth(c.httpc, c.endpoints.Health)
}

// ExecuteTask POSTs the envelope to Core API's /execute_task (port 8003).
// Single-task execution path. v15.3 BHIV ecosystem support.
func (c *CoreClient) ExecuteTask(env *PropagationEnvelope) (*EcosystemAck, error) {
	return postEnvelope(c.httpc, c.endpoints.ExecuteTask, env, "core_execute_task", false)
}

// ExecuteSequence POSTs the envelope to Core API's /execute_sequence
// (port 8003). Multi-task sequence path.
func (c *CoreClient) ExecuteSequence(env *PropagationEnvelope) (*EcosystemAck, error) {
	return postEnvelope(c.httpc, c.endpoints.ExecuteSequence, env, "core_execute_sequence", false)
}

// HandleTask POSTs the envelope to MCP Bridge's /handle_task (port 8000).
// Main task ingestion path: Core → MCP → Sovereign → Sarathi.
func (c *CoreClient) HandleTask(env *PropagationEnvelope) (*EcosystemAck, error) {
	return postEnvelope(c.httpc, c.endpoints.HandleTask, env, "mcp_handle_task", false)
}

// SovereignDecide POSTs an input to Sovereign Core's /sovereign/decide
// (port 9001) and returns the decision response (with decision_hash,
// trace_id, policy_reference). Used in active-decide mode where Sarathi
// is asking the upstream PDP for a verdict.
//
// Note: in the standard enforcement-validation flow Sarathi RECEIVES
// pre-decided ExternalDecisions at /v1/ingest-decision; this method is
// for the inverse flow where Sarathi solicits a decision.
func (c *CoreClient) SovereignDecide(input []byte) (*EcosystemAck, error) {
	if strings.TrimSpace(c.endpoints.SovereignDecide) == "" {
		return nil, fmt.Errorf("core_client: SovereignDecide URL is empty")
	}
	req, err := http.NewRequest(http.MethodPost, c.endpoints.SovereignDecide, bytes.NewReader(input))
	if err != nil {
		return nil, fmt.Errorf("core_client: new request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := c.httpc.Do(req)
	if err != nil {
		return nil, fmt.Errorf("core_client: SovereignDecide POST: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("core_client: SovereignDecide status=%d body=%s",
			resp.StatusCode, truncateForLog(string(body), 256))
	}
	return &EcosystemAck{
		Peer:        "sovereign",
		Status:      resp.StatusCode,
		HTTPHeaders: resp.Header,
		Raw:         json.RawMessage(body),
	}, nil
}

// SovereignHealth probes Sovereign Core /health (port 9001).
func (c *CoreClient) SovereignHealth() error {
	return probeHealth(c.httpc, c.endpoints.SovereignHealth)
}

// PostTaskInput is the v15.4 input-bootstrap path: Sarathi (or any caller)
// sends a fresh task input to Core API /execute_task and lets Core drive the
// rest of the BHIV chain (Core -> MCP /handle_task -> Sovereign
// /sovereign/decide -> back to Sarathi /sarathi/enforce). Per Raj's contract,
// trace_id is GENERATED BY CORE and returned in the response; callers MUST
// send trace_id="" so Core mints it.
//
// This is distinct from ExecuteTask() above: ExecuteTask sends the post-
// enforcement sealed envelope downstream; PostTaskInput sends a brand-new
// input upstream. Same endpoint, different payload shape, opposite direction.
//
// The returned []byte is Core's verbatim response body (typically
// {"trace_id":"...","decision":"ALLOW","decision_hash":"...",
// "policy_reference":"...","input_hash":"...","timestamp":"..."}) — the
// caller parses fields it needs.
func (c *CoreClient) PostTaskInput(input string, contextMap map[string]interface{}) ([]byte, error) {
	if strings.TrimSpace(c.endpoints.ExecuteTask) == "" {
		return nil, fmt.Errorf("core_client: ExecuteTask URL is empty")
	}
	if contextMap == nil {
		contextMap = map[string]interface{}{}
	}
	payload := map[string]interface{}{
		"trace_id": "",
		"input":    input,
		"context":  contextMap,
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("core_client: PostTaskInput marshal: %w", err)
	}
	req, err := http.NewRequest(http.MethodPost, c.endpoints.ExecuteTask, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("core_client: PostTaskInput new request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Sarathi-Component", "PostTaskInput")
	req.Header.Set("ngrok-skip-browser-warning", "true")
	resp, err := c.httpc.Do(req)
	if err != nil {
		return nil, fmt.Errorf("core_client: PostTaskInput POST %s: %w", c.endpoints.ExecuteTask, err)
	}
	defer resp.Body.Close()
	respBody, rerr := io.ReadAll(resp.Body)
	if rerr != nil {
		return nil, fmt.Errorf("core_client: PostTaskInput read: %w", rerr)
	}
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("core_client: PostTaskInput status=%d body=%s",
			resp.StatusCode, truncateForLog(string(respBody), 256))
	}
	return respBody, nil
}

// ----------------------------------------------------------------------------
// InsightFlowClient — 4 endpoints
// ----------------------------------------------------------------------------

// InsightFlowClient maps BHIV InsightFlow's 4 endpoints. Three are digest-only
// (no full body — digest fingerprint hashes), preserving INV-PROP-06 (Intel
// Layer never receives full enforcement output). The fourth (BucketPersist)
// is also digest-only because it is observability mediated, not source of
// truth.
type InsightFlowClient struct {
	endpoints InsightFlowEndpoints
	httpc     *http.Client
}

// NewInsightFlowClient returns an InsightFlow client.
func NewInsightFlowClient(eps InsightFlowEndpoints) *InsightFlowClient {
	return &InsightFlowClient{
		endpoints: eps,
		httpc:     &http.Client{Timeout: EcosystemClientDefaultTimeout},
	}
}

// SarathiTrigger POSTs the envelope to /sarathi_trigger. Marker call: lets
// InsightFlow record that an enforcement event has begun. Digest-only —
// receives fingerprint hashes, never full body.
func (i *InsightFlowClient) SarathiTrigger(env *PropagationEnvelope) (*EcosystemAck, error) {
	return postEnvelope(i.httpc, i.endpoints.SarathiTrigger, env, "insightflow", true)
}

// CoreExecute POSTs the envelope digest to /core_execute. Mirrors Core's
// Execute hop for parity logging on the InsightFlow side.
func (i *InsightFlowClient) CoreExecute(env *PropagationEnvelope) (*EcosystemAck, error) {
	return postEnvelope(i.httpc, i.endpoints.CoreExecute, env, "insightflow", true)
}

// Process POSTs the envelope digest to /insightflow_process — the primary
// observability ingest. Digest-only by contract (INV-PROP-06).
func (i *InsightFlowClient) Process(env *PropagationEnvelope) (*EcosystemAck, error) {
	return postEnvelope(i.httpc, i.endpoints.InsightFlowProcess, env, "insightflow", true)
}

// BucketPersist POSTs the envelope digest to /bucket_persist — the
// InsightFlow-mediated bucket persistence signal. The actual bucket store is
// reached via BucketClient.StoreArtifact; this endpoint is observability
// only.
func (i *InsightFlowClient) BucketPersist(env *PropagationEnvelope) (*EcosystemAck, error) {
	return postEnvelope(i.httpc, i.endpoints.BucketPersist, env, "insightflow", true)
}

// VerifyBucket GETs InsightFlow's /bucket/verify/{trace_id} endpoint to
// confirm trace continuity from InsightFlow's side. Used by Vijay's
// telemetry-validation gate. Returns the raw response body for the operator
// to inspect. v15.3 BHIV ecosystem support.
func (i *InsightFlowClient) VerifyBucket(traceID string) ([]byte, error) {
	if strings.TrimSpace(i.endpoints.VerifyBucket) == "" {
		return nil, fmt.Errorf("insightflow_client: VerifyBucket URL is empty")
	}
	url := strings.TrimRight(i.endpoints.VerifyBucket, "/") + "/" + traceID
	resp, err := i.httpc.Get(url)
	if err != nil {
		return nil, fmt.Errorf("insightflow_client: VerifyBucket GET %s: %w", url, err)
	}
	defer resp.Body.Close()
	body, rerr := io.ReadAll(resp.Body)
	if rerr != nil {
		return nil, fmt.Errorf("insightflow_client: VerifyBucket read: %w", rerr)
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("insightflow_client: VerifyBucket status=%d body=%s",
			resp.StatusCode, truncateForLog(string(body), 256))
	}
	return body, nil
}

// ----------------------------------------------------------------------------
// BucketClient — 3 endpoints
// ----------------------------------------------------------------------------

// BucketClient maps the 3 BHIV Bucket endpoints. The store endpoint is
// in-chain; the two GET endpoints are out-of-chain verification helpers.
type BucketClient struct {
	endpoints BucketEndpoints
	httpc     *http.Client
}

// NewBucketClient returns a Bucket client.
func NewBucketClient(eps BucketEndpoints) *BucketClient {
	return &BucketClient{
		endpoints: eps,
		httpc:     &http.Client{Timeout: EcosystemClientDefaultTimeout},
	}
}

// StoreArtifact POSTs the sealed bytes to /bucket/artifact — the byte-equality
// source of truth.
func (b *BucketClient) StoreArtifact(env *PropagationEnvelope) (*EcosystemAck, error) {
	return postEnvelope(b.httpc, b.endpoints.ArtifactPost, env, "bucket", false)
}

// GetArtifact GETs /bucket/artifact/{decision_id} and returns the verbatim
// stored bytes. Used by VerifyBucketReadback to prove end-to-end byte equality.
func (b *BucketClient) GetArtifact(decisionID string) ([]byte, error) {
	url := strings.TrimRight(b.endpoints.ArtifactGet, "/") + "/" + safeDecisionID(decisionID)
	resp, err := b.httpc.Get(url)
	if err != nil {
		return nil, fmt.Errorf("bucket_get: GET %s: %w", url, err)
	}
	defer resp.Body.Close()
	body, rerr := io.ReadAll(resp.Body)
	if rerr != nil {
		return nil, fmt.Errorf("bucket_get: read body: %w", rerr)
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("bucket_get: %s status=%d body=%s", url, resp.StatusCode, string(body))
	}
	return body, nil
}

// ArtifactSummary is one row in a /bucket/artifacts?trace_id= response.
type ArtifactSummary struct {
	DecisionID   string `json:"decision_id"`
	ResponseHash string `json:"response_hash"`
	StoredAt     string `json:"stored_at,omitempty"`
	StoragePath  string `json:"storage_path,omitempty"`
}

// GetArtifactsByTrace GETs /bucket/artifacts?trace_id={id} and decodes the
// trace-level summary. NEW: enables trace-level verification across multi-hop
// flows. The response shape is JSON object with key "artifacts" pointing at
// an array of ArtifactSummary.
func (b *BucketClient) GetArtifactsByTrace(traceID string) ([]ArtifactSummary, error) {
	base := b.endpoints.ArtifactsByTrace
	sep := "?"
	if strings.Contains(base, "?") {
		sep = "&"
	}
	url := base + sep + "trace_id=" + traceID
	resp, err := b.httpc.Get(url)
	if err != nil {
		return nil, fmt.Errorf("bucket_artifacts_by_trace: GET %s: %w", url, err)
	}
	defer resp.Body.Close()
	body, rerr := io.ReadAll(resp.Body)
	if rerr != nil {
		return nil, fmt.Errorf("bucket_artifacts_by_trace: read body: %w", rerr)
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("bucket_artifacts_by_trace: %s status=%d body=%s",
			url, resp.StatusCode, string(body))
	}
	// Accept either {"artifacts": [...]} or a bare [...] array — be liberal.
	var asObj struct {
		Artifacts []ArtifactSummary `json:"artifacts"`
	}
	if err := json.Unmarshal(body, &asObj); err == nil && asObj.Artifacts != nil {
		return asObj.Artifacts, nil
	}
	var asArr []ArtifactSummary
	if err := json.Unmarshal(body, &asArr); err == nil {
		return asArr, nil
	}
	return nil, fmt.Errorf("bucket_artifacts_by_trace: unrecognised body shape: %s", string(body))
}

// ----------------------------------------------------------------------------
// Shared transport machinery
// ----------------------------------------------------------------------------

// digestPayload is the contract InsightFlow's digest-only endpoints accept.
// It carries fingerprint hashes ONLY — the verdict body is forbidden.
type digestPayload struct {
	SchemaVersion    string `json:"schema_version"`
	DecisionID       string `json:"decision_id"`
	ExecutionID      string `json:"execution_id"`
	TraceID          string `json:"trace_id"`
	CorrelationID    string `json:"correlation_id,omitempty"`
	ResponseHash     string `json:"response_hash"`
	ChainBindingHash string `json:"chain_binding_hash"`
	EnforcementHash  string `json:"enforcement_hash"`
	DecisionHash     string `json:"decision_hash,omitempty"`
	Verdict          string `json:"verdict,omitempty"`
	ObservedAt       string `json:"observed_at"`
}

// buildDigest extracts the fingerprint hashes from an envelope. No verdict
// body, no canonical response, no token. INV-PROP-06.
func buildDigest(env *PropagationEnvelope) digestPayload {
	return digestPayload{
		SchemaVersion:    "sarathi.digest/v1.0",
		DecisionID:       env.DecisionID(),
		ExecutionID:      env.ExecutionID(),
		TraceID:          env.TraceID(),
		CorrelationID:    env.CorrelationID(),
		ResponseHash:     env.ResponseHash(),
		ChainBindingHash: env.ChainBindingHash(),
		EnforcementHash:  env.EnforcementHash(),
		DecisionHash:     env.DecisionHash(),
		Verdict:          env.Verdict(),
		ObservedAt:       time.Now().UTC().Format(time.RFC3339Nano),
	}
}

// postEnvelope is the shared transport. For non-digest hops it sends the
// canonical response bytes verbatim; for digest hops it sends a JSON digest
// payload. In both cases it sets the 9 standard X-Sarathi-* headers and
// verifies the X-Sarathi-Ack-Hash echo for non-digest hops.
//
// Returns *PropagationStopError when a byte mismatch is detected.
func postEnvelope(
	httpc *http.Client,
	url string,
	env *PropagationEnvelope,
	peer string,
	digestOnly bool,
) (*EcosystemAck, error) {
	if env == nil {
		return nil, fmt.Errorf("ecosystem_clients: nil envelope")
	}
	if strings.TrimSpace(url) == "" {
		return nil, fmt.Errorf("ecosystem_clients: empty url for peer=%s", peer)
	}

	var body []byte
	if digestOnly {
		dig := buildDigest(env)
		canon, cerr := CanonicalMarshal(&dig)
		if cerr != nil {
			return nil, fmt.Errorf("ecosystem_clients: digest canonical marshal: %w", cerr)
		}
		body = canon
	} else {
		body = env.CanonicalResponseBytes()
	}

	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("ecosystem_clients: new request peer=%s: %w", peer, err)
	}
	req.ContentLength = int64(len(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("ngrok-skip-browser-warning", "true")
	if digestOnly {
		req.Header.Set(HeaderDigestOnly, "1")
	}
	for k, v := range env.ToHeaderMap() {
		req.Header.Set(k, v)
	}
	// InsightFlow requires an outbound API key (X-API-Key). Attach it when
	// configured; the full value (label prefix included) is the secret.
	if strings.HasPrefix(peer, "insightflow") {
		if k := strings.TrimSpace(os.Getenv(EnvInsightAPIKey)); k != "" {
			req.Header.Set("X-API-Key", k)
		}
	}

	sentHash := Sha256Hex(body)
	resp, err := httpc.Do(req)
	if err != nil {
		return nil, fmt.Errorf("ecosystem_clients: peer=%s url=%s: %w", peer, url, err)
	}
	defer resp.Body.Close()

	respBody, rerr := io.ReadAll(resp.Body)
	if rerr != nil {
		return nil, fmt.Errorf("ecosystem_clients: read peer=%s: %w", peer, rerr)
	}

	if resp.StatusCode >= 400 {
		// Try to surface the peer's error_code header if present.
		errCode := resp.Header.Get(HeaderErrorCode)
		return nil, fmt.Errorf("ecosystem_clients: peer=%s status=%d error_code=%s body=%s",
			peer, resp.StatusCode, errCode, truncateForLog(string(respBody), 256))
	}

	ackHash := resp.Header.Get(HeaderAckHash)

	// For digest hops we don't enforce ack_hash echo (Intelligence layer is
	// out-of-chain by INV-PROP-06). For full-body hops, ack_hash MUST equal
	// the sent hash — any drift halts propagation.
	if !digestOnly {
		ok, eqRes := ValidateHop(peer, body, sentHash, ackHash, env)
		if !ok {
			_ = RecordViolation(eqRes)
			return nil, NewPropagationStopError(eqRes)
		}
	}

	ack := &EcosystemAck{
		Peer:        peer,
		AckHash:     ackHash,
		Status:      resp.StatusCode,
		HTTPHeaders: resp.Header,
		Raw:         json.RawMessage(respBody),
	}
	// Try to parse the structured fields for telemetry. Body shape varies —
	// liberal parser, ignore failures (Raw is preserved either way).
	var parsed map[string]interface{}
	if err := json.Unmarshal(respBody, &parsed); err == nil {
		if s, ok := parsed["decision_id"].(string); ok {
			ack.DecisionID = s
		}
		if s, ok := parsed["storage_path"].(string); ok {
			ack.StoragePath = s
		}
		if s, ok := parsed["ack_hash"].(string); ok && ack.AckHash == "" {
			ack.AckHash = s
		}
	}
	return ack, nil
}

// probeHealth performs a GET against url and returns nil iff the response is
// 2xx. Used for boot-time pre-flight gates and cross-machine telemetry.
func probeHealth(httpc *http.Client, url string) error {
	if strings.TrimSpace(url) == "" {
		return fmt.Errorf("probe_health: empty url")
	}
	resp, err := httpc.Get(url)
	if err != nil {
		return fmt.Errorf("probe_health: %s: %w", url, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("probe_health: %s status=%d", url, resp.StatusCode)
	}
	return nil
}

// truncateForLog returns at most n bytes of s, useful for error messages.
func truncateForLog(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "...(truncateForLogd)"
}
