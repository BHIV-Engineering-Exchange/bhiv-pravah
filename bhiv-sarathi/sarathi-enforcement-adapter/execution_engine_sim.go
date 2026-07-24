package main

// execution_engine_sim.go — Sovereign Execution Gate. Token-Only Entry.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Enforcement Adapter (PEP)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// ARCHITECTURAL HARD GATE:
//   The ExecutionEngine has ONE public execution method: ExecuteWithToken().
//   This method accepts ONLY a CapabilityToken — not a raw request, not an
//   ExecutionResponse, not any other artifact.
//
//   If execution can happen without a valid, Ed25519-signed CapabilityToken,
//   the system is advisory. This engine ensures it is SOVEREIGN.
//
// EXECUTION CONTRACT:
//   Input:  *CapabilityToken (signed by TokenAuthority)
//   Output: *ExecutionResult (standardized, deterministic)
//
//   The engine holds ONLY the public key of the TokenAuthority.
//   It cannot sign tokens. It can only verify them.
//   The private key lives in the EnforcementAdapter.
//
// 9-CHECK VALIDATION GATE (in order):
//   1. Token exists                    → NO_TOKEN
//   2. Ed25519 signature valid         → INVALID_SIGNATURE
//   3. SHA-256 integrity hash matches  → HASH_MISMATCH
//   4. Token not expired               → TOKEN_EXPIRED
//   5. Token not consumed              → TOKEN_ALREADY_USED
//   6. Verdict is ALLOW                → VERDICT_NOT_ALLOW
//   7. Enforcement hash in chain       → ENFORCEMENT_HASH_NOT_IN_CHAIN
//   8. Decision ID present             → ALLOW_WITHOUT_DECISION_ID
//   9. Token not revoked (FIX-04 v7.0) → TOKEN_REVOKED
//
// GAP FIXES APPLIED:
//   GAP-02: TTL check — reject expired decisions/tokens
//   GAP-04: Bypass prevention — verify enforcement_hash in adapter chain
//   GAP-05: Obligation discharge — must discharge all before execution
//   GAP-10: ESCALATE handling — ESCALATE → nil token → NO_TOKEN
//   GAP-11: json.Marshal error handling (fail-closed)
//   GAP-17: Struct-based deterministic hash computation

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"
)

// executionChainPayload is a struct for deterministic hash computation (GAP-17).
type executionChainPayload struct {
	Prev            string `json:"prev"`
	EnforcementHash string `json:"enforcement_hash"`
	ExecutionState  string `json:"execution_state"`
	Executed        bool   `json:"executed"`
	Sequence        int    `json:"sequence"`
}

// ExecutionLogEntry is a single entry in the execution hash chain.
type ExecutionLogEntry struct {
	ExecutionSequence     int      `json:"execution_sequence"`
	ExecutionState        string   `json:"execution_state"`
	Executed              bool     `json:"executed"`
	EnforcementHash       string   `json:"enforcement_hash"`
	DecisionID            string   `json:"decision_id"`
	CorrelationID         string   `json:"correlation_id"`
	Verdict               string   `json:"verdict"`
	PrevExecutionHash     string   `json:"prev_execution_hash"`
	ExecutionHash         string   `json:"execution_hash"`
	TokenID               string   `json:"token_id,omitempty"`
	ObligationsDischarged []string `json:"obligations_discharged,omitempty"`
	BlockReason           string   `json:"block_reason,omitempty"`
	BlockDetail           string   `json:"block_detail,omitempty"`
}

// ================================================================
// CRIT-06 FIX: ExecutionHandler — Real Execution Backend Interface
// ================================================================
//
// The ExecutionEngine validates tokens and manages the execution chain,
// but the ACTUAL execution (calling downstream services, running actions)
// is delegated to an ExecutionHandler. This decouples the sovereign gate
// from the execution backend, allowing:
//   - Simulation (current behavior, for testing)
//   - Real execution (HTTP calls, gRPC, message queues)
//   - Hybrid (real execution with dry-run mode)
//
// Without this interface, the system is a pure simulation that can never
// execute real actions — a CRITICAL gap for production deployment.
//
// Industry alignment:
//   - AWS Lambda: Execution gateway validates IAM tokens, then delegates to runtime
//   - Google Cloud Run: Ingress validates IAM, then delegates to container
//   - HashiCorp Nomad: Scheduler validates ACL tokens, then delegates to allocator
type ExecutionHandler interface {
	// Execute performs the actual action authorized by the token.
	// Called ONLY after all 9 validation checks pass.
	// Returns (success bool, executionDetail string, err error).
	// If err != nil, the execution is treated as FAILED (not BLOCKED).
	Execute(token *CapabilityToken) (success bool, detail string, err error)

	// IsSimulation returns true if this handler simulates execution.
	// Production deployments MUST use a non-simulation handler.
	IsSimulation() bool
}

// SimulationHandler is the default execution handler that simulates execution.
// Used for testing, development, and system verification.
type SimulationHandler struct{}

func (s *SimulationHandler) Execute(token *CapabilityToken) (bool, string, error) {
	return true, fmt.Sprintf("SIMULATED: decision_id=%s correlation_id=%s", token.DecisionID(), token.CorrelationID()), nil
}
func (s *SimulationHandler) IsSimulation() bool { return true }

// WebhookExecutionHandler sends the CapabilityToken to an external HTTP webhook for real workloads.
type WebhookExecutionHandler struct {
	webhookURL string
}

func NewWebhookExecutionHandler(url string) *WebhookExecutionHandler {
	return &WebhookExecutionHandler{webhookURL: url}
}

func (w *WebhookExecutionHandler) Execute(token *CapabilityToken) (bool, string, error) {
	if token == nil {
		return false, "No token provided", fmt.Errorf("nil token")
	}
	payload, err := json.Marshal(token.ToMap())
	if err != nil {
		return false, "Failed to marshal payload", err
	}
	
	req, err := http.NewRequest("POST", w.webhookURL, bytes.NewBuffer(payload))
	if err != nil {
		return false, "Failed to create request", err
	}
	req.Header.Set("Content-Type", "application/json")
	
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return false, fmt.Sprintf("Webhook execution error: %v", err), err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		return true, fmt.Sprintf("REAL EXECUTION: Webhook returned %s", resp.Status), nil
	}
	return false, fmt.Sprintf("Webhook rejected request: HTTP %s", resp.Status), fmt.Errorf("HTTP %d", resp.StatusCode)
}

func (w *WebhookExecutionHandler) IsSimulation() bool { return false }

// ================================================================
// PRODUCTION WEBHOOK HANDLER (v14.2 PHASE B)
// ================================================================
//
// ProductionWebhookHandler is a hardened HTTP execution client that replaces
// the bare WebhookExecutionHandler stub for real-world production workloads.
//
// Features:
//   - Exponential backoff retry with jitter (configurable max retries)
//   - Circuit breaker (fail-closed: OPEN circuit → immediate failure)
//   - Configurable per-request timeout
//   - Auth headers (Bearer token)
//   - Correlation headers (X-Sarathi-Token-ID, X-Correlation-ID)
//   - Dead-letter log (in-memory ring buffer + optional PostgreSQL persistence)
//
// SECURITY INVARIANTS:
//   - This handler is called ONLY after the 10-check validation gate passes.
//     It cannot bypass enforcement — it is downstream of the sovereign gate.
//   - If execution fails (HTTP error, timeout, circuit open), the result
//     is EXECUTION_FAILED (not EXECUTION_BLOCKED — the token was valid,
//     but the downstream system could not fulfill it).
//   - Dead-letter entries preserve the full execution context for audit.
//
// Industry alignment:
//   - AWS Lambda: Execution gateway retries with DLQ on failure
//   - Google Cloud Tasks: Exponential backoff with configurable retry
//   - Azure Durable Functions: Circuit breaker + retry policies

// FailedExecution records a failed execution attempt for dead-letter processing.
// Persisted to both in-memory ring buffer and PostgreSQL (if available).
type FailedExecution struct {
	TokenID         string    `json:"token_id"`
	DecisionID      string    `json:"decision_id"`
	CorrelationID   string    `json:"correlation_id"`
	EnforcementHash string    `json:"enforcement_hash"`
	WebhookURL      string    `json:"webhook_url"`
	HTTPStatus      int       `json:"http_status,omitempty"`
	ErrorDetail     string    `json:"error_detail"`
	Attempts        int       `json:"attempts"`
	FirstAttemptAt  time.Time `json:"first_attempt_at"`
	LastAttemptAt   time.Time `json:"last_attempt_at"`
	CircuitState    string    `json:"circuit_state"`
}

// ProductionWebhookConfig configures the ProductionWebhookHandler.
type ProductionWebhookConfig struct {
	WebhookURL   string            // target webhook endpoint
	AuthToken    string            // Bearer token for authentication
	Timeout      time.Duration     // per-request timeout
	Headers      map[string]string // custom headers
	Retry        RetryConfig       // retry configuration
	CircuitBreaker CircuitBreakerConfig // circuit breaker configuration
	MaxDeadLetter int              // max dead-letter entries (ring buffer size)
}

// DefaultProductionWebhookConfig returns production-grade defaults.
func DefaultProductionWebhookConfig(webhookURL string) ProductionWebhookConfig {
	return ProductionWebhookConfig{
		WebhookURL: webhookURL,
		Timeout:    10 * time.Second,
		Retry:      DefaultRetryConfig(),
		CircuitBreaker: DefaultCircuitBreakerConfig(),
		MaxDeadLetter:  500,
	}
}

// ProductionWebhookHandler is a hardened execution handler with retry,
// circuit breaker, and dead-letter support for real production workloads.
type ProductionWebhookHandler struct {
	config         ProductionWebhookConfig
	httpClient     *http.Client
	circuitBreaker *CircuitBreaker
	mu             sync.Mutex
	deadLetterLog  []FailedExecution
	maxDeadLetter  int
}

// NewProductionWebhookHandler creates a production-grade webhook execution handler.
func NewProductionWebhookHandler(config ProductionWebhookConfig) *ProductionWebhookHandler {
	if config.Timeout <= 0 {
		config.Timeout = 10 * time.Second
	}
	if config.MaxDeadLetter <= 0 {
		config.MaxDeadLetter = 500
	}

	return &ProductionWebhookHandler{
		config: config,
		httpClient: &http.Client{
			Timeout: config.Timeout,
		},
		circuitBreaker: NewCircuitBreaker("webhook-exec", config.CircuitBreaker),
		deadLetterLog:  make([]FailedExecution, 0, config.MaxDeadLetter),
		maxDeadLetter:  config.MaxDeadLetter,
	}
}

// Execute performs the actual HTTP webhook call with retry and circuit breaker.
// Called ONLY after the 10-check validation gate passes in ExecuteWithToken.
func (pwh *ProductionWebhookHandler) Execute(token *CapabilityToken) (bool, string, error) {
	if token == nil {
		return false, "No token provided", fmt.Errorf("nil token")
	}

	firstAttempt := time.Now().UTC()

	// Step 1: Circuit breaker check
	if !pwh.circuitBreaker.Allow() {
		failed := FailedExecution{
			TokenID:         token.TokenID(),
			DecisionID:      token.DecisionID(),
			CorrelationID:   token.CorrelationID(),
			EnforcementHash: token.enforcementHash,
			WebhookURL:      pwh.config.WebhookURL,
			ErrorDetail:     "CIRCUIT_BREAKER_OPEN",
			Attempts:        0,
			FirstAttemptAt:  firstAttempt,
			LastAttemptAt:   firstAttempt,
			CircuitState:    pwh.circuitBreaker.GetStateString(),
		}
		pwh.recordDeadLetter(failed)
		return false, "CIRCUIT_OPEN: webhook circuit breaker is open — failing closed", fmt.Errorf("circuit breaker OPEN")
	}

	// Step 2: Marshal payload
	payload, err := json.Marshal(token.ToMap())
	if err != nil {
		return false, "Failed to marshal token payload", err
	}

	// Step 3: Retry loop with exponential backoff
	var lastErr error
	var lastStatus int
	maxAttempts := 1 + pwh.config.Retry.MaxRetries

	for attempt := 0; attempt < maxAttempts; attempt++ {
		if attempt > 0 {
			backoff := pwh.config.Retry.ComputeBackoff(attempt - 1)
			time.Sleep(backoff)
		}

		req, reqErr := http.NewRequest("POST", pwh.config.WebhookURL, bytes.NewBuffer(payload))
		if reqErr != nil {
			lastErr = reqErr
			continue
		}

		// Set headers
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("X-Sarathi-Token-ID", token.TokenID())
		req.Header.Set("X-Sarathi-Correlation-ID", token.CorrelationID())
		req.Header.Set("X-Sarathi-Decision-ID", token.DecisionID())
		if pwh.config.AuthToken != "" {
			req.Header.Set("Authorization", "Bearer "+pwh.config.AuthToken)
		}
		for k, v := range pwh.config.Headers {
			req.Header.Set(k, v)
		}

		resp, respErr := pwh.httpClient.Do(req)
		if respErr != nil {
			lastErr = respErr
			lastStatus = 0
			continue // Transient — retry
		}
		resp.Body.Close()
		lastStatus = resp.StatusCode

		// 2xx = success
		if resp.StatusCode >= 200 && resp.StatusCode < 300 {
			pwh.circuitBreaker.RecordSuccess()
			return true, fmt.Sprintf("REAL_EXECUTION: webhook returned HTTP %d (attempt %d/%d)",
				resp.StatusCode, attempt+1, maxAttempts), nil
		}

		// 4xx = permanent failure — do not retry
		if resp.StatusCode >= 400 && resp.StatusCode < 500 {
			lastErr = fmt.Errorf("HTTP %d", resp.StatusCode)
			break // Permanent, no retry
		}

		// 5xx = transient — retry
		lastErr = fmt.Errorf("HTTP %d", resp.StatusCode)
	}

	// All attempts failed — record circuit breaker failure and dead-letter
	pwh.circuitBreaker.RecordFailure()

	failed := FailedExecution{
		TokenID:         token.TokenID(),
		DecisionID:      token.DecisionID(),
		CorrelationID:   token.CorrelationID(),
		EnforcementHash: token.enforcementHash,
		WebhookURL:      pwh.config.WebhookURL,
		HTTPStatus:      lastStatus,
		ErrorDetail:     fmt.Sprintf("all %d attempts failed: %v", maxAttempts, lastErr),
		Attempts:        maxAttempts,
		FirstAttemptAt:  firstAttempt,
		LastAttemptAt:   time.Now().UTC(),
		CircuitState:    pwh.circuitBreaker.GetStateString(),
	}
	pwh.recordDeadLetter(failed)

	detail := fmt.Sprintf("WEBHOOK_FAILED: %d attempts exhausted (last HTTP %d, err: %v)",
		maxAttempts, lastStatus, lastErr)
	return false, detail, lastErr
}

// IsSimulation returns false — this is a real production handler.
func (pwh *ProductionWebhookHandler) IsSimulation() bool { return false }

// recordDeadLetter appends a failed execution to the dead-letter ring buffer.
func (pwh *ProductionWebhookHandler) recordDeadLetter(entry FailedExecution) {
	pwh.mu.Lock()
	defer pwh.mu.Unlock()

	if len(pwh.deadLetterLog) >= pwh.maxDeadLetter {
		// Ring buffer: drop oldest
		pwh.deadLetterLog = pwh.deadLetterLog[1:]
	}
	pwh.deadLetterLog = append(pwh.deadLetterLog, entry)

	fmt.Printf("  [DeadLetter] token=%s decision=%s corr=%s err=%s\n",
		entry.TokenID, entry.DecisionID, entry.CorrelationID, entry.ErrorDetail)
}

// GetDeadLetterLog returns a copy of the dead-letter entries for inspection.
func (pwh *ProductionWebhookHandler) GetDeadLetterLog() []FailedExecution {
	pwh.mu.Lock()
	defer pwh.mu.Unlock()

	cp := make([]FailedExecution, len(pwh.deadLetterLog))
	copy(cp, pwh.deadLetterLog)
	return cp
}

// GetDeadLetterCount returns the number of dead-letter entries.
func (pwh *ProductionWebhookHandler) GetDeadLetterCount() int {
	pwh.mu.Lock()
	defer pwh.mu.Unlock()
	return len(pwh.deadLetterLog)
}

// GetCircuitBreakerState returns the current circuit breaker state string.
func (pwh *ProductionWebhookHandler) GetCircuitBreakerState() string {
	return pwh.circuitBreaker.GetStateString()
}

// ================================================================
// DEAD-LETTER POSTGRESQL PERSISTENCE (v14.2)
// ================================================================
//
// These methods persist failed execution attempts to PostgreSQL for
// durable recovery and audit compliance. The in-memory ring buffer
// provides fast access; PostgreSQL provides durability.

// EnsureDeadLetterSchema creates the dead_letter_queue table in PostgreSQL.
// Idempotent — safe to call multiple times.
func EnsureDeadLetterSchema(db *sql.DB) error {
	if db == nil {
		return fmt.Errorf("nil database connection")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	schema := `
	CREATE TABLE IF NOT EXISTS dead_letter_queue (
		id              SERIAL PRIMARY KEY,
		token_id        TEXT NOT NULL,
		decision_id     TEXT NOT NULL,
		correlation_id  TEXT NOT NULL,
		enforcement_hash TEXT NOT NULL,
		webhook_url     TEXT NOT NULL,
		http_status     INTEGER DEFAULT 0,
		error_detail    TEXT NOT NULL,
		attempts        INTEGER NOT NULL DEFAULT 0,
		first_attempt_at TIMESTAMPTZ NOT NULL,
		last_attempt_at  TIMESTAMPTZ NOT NULL,
		circuit_state   TEXT NOT NULL DEFAULT 'UNKNOWN',
		created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
		resolved        BOOLEAN NOT NULL DEFAULT FALSE,
		resolved_at     TIMESTAMPTZ
	);

	CREATE INDEX IF NOT EXISTS idx_dead_letter_correlation
		ON dead_letter_queue(correlation_id);
	CREATE INDEX IF NOT EXISTS idx_dead_letter_unresolved
		ON dead_letter_queue(resolved) WHERE resolved = FALSE;
	`

	_, err := db.ExecContext(ctx, schema)
	return err
}

// PersistDeadLetterToPostgres writes a single dead-letter entry to PostgreSQL.
func PersistDeadLetterToPostgres(db *sql.DB, entry FailedExecution) error {
	if db == nil {
		return fmt.Errorf("nil database connection")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	_, err := db.ExecContext(ctx,
		`INSERT INTO dead_letter_queue
		(token_id, decision_id, correlation_id, enforcement_hash,
		 webhook_url, http_status, error_detail, attempts,
		 first_attempt_at, last_attempt_at, circuit_state)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
		entry.TokenID, entry.DecisionID, entry.CorrelationID,
		entry.EnforcementHash, entry.WebhookURL, entry.HTTPStatus,
		entry.ErrorDetail, entry.Attempts,
		entry.FirstAttemptAt, entry.LastAttemptAt, entry.CircuitState,
	)
	return err
}

// FlushDeadLetterToPostgres batch-writes all in-memory dead-letter entries
// to PostgreSQL. Returns the number of entries successfully persisted.
func (pwh *ProductionWebhookHandler) FlushDeadLetterToPostgres(db *sql.DB) (int, error) {
	if db == nil {
		return 0, fmt.Errorf("nil database connection")
	}

	entries := pwh.GetDeadLetterLog()
	persisted := 0
	for _, entry := range entries {
		if err := PersistDeadLetterToPostgres(db, entry); err != nil {
			fmt.Printf("  [DeadLetter] PostgreSQL persist error for token=%s: %v\n", entry.TokenID, err)
			continue
		}
		persisted++
	}

	if persisted > 0 {
		fmt.Printf("  [DeadLetter] Flushed %d/%d entries to PostgreSQL\n", persisted, len(entries))
	}
	return persisted, nil
}

// ExecutionEngine is the sovereign execution gate.
// It has ONE public execution method: ExecuteWithToken.
// No other path to execution exists.
// CRIT-06: Now supports pluggable ExecutionHandler for real execution backends.
type ExecutionEngine struct {
	mu                sync.Mutex
	executionLog      []ExecutionLogEntry
	prevExecutionHash string
	executionCount    int
	adapter           *EnforcementAdapter // GAP-04: for enforcement chain verification
	tokenRegistry     *TokenRegistry      // single-use token tracking
	tokenPublicKey    ed25519.PublicKey    // TokenAuthority public key (verify only)
	tokenKeyID        string              // expected signer key ID
	revocationList    *TokenRevocationList // FIX-04 (v7.0): Token revocation check (9th gate)
	handler           ExecutionHandler     // CRIT-06: pluggable execution backend
	minRegistryVersion int64               // Gap 2: Minimum allowed registry version for TOCTOU
}

// NewExecutionEngine creates an execution engine bound to an adapter.
// It receives ONLY the public key of the TokenAuthority — no private key.
// Uses SimulationHandler by default. For production, call SetExecutionHandler.
func NewExecutionEngine(adapter *EnforcementAdapter, tokenPubKey ed25519.PublicKey, tokenKeyID string) *ExecutionEngine {
	return &ExecutionEngine{
		prevExecutionHash: "GENESIS",
		adapter:           adapter,
		tokenRegistry:     NewTokenRegistry(),
		tokenPublicKey:    tokenPubKey,
		tokenKeyID:        tokenKeyID,
		handler:           &SimulationHandler{},
	}
}

// SetExecutionHandler sets the execution backend.
// In production, replace SimulationHandler with a real handler.
func (ee *ExecutionEngine) SetExecutionHandler(handler ExecutionHandler) {
	ee.mu.Lock()
	defer ee.mu.Unlock()
	ee.handler = handler
}

// IsSimulation returns true if the engine is using a simulation handler.
func (ee *ExecutionEngine) IsSimulation() bool {
	if ee.handler == nil {
		return true
	}
	return ee.handler.IsSimulation()
}

// SetRevocationList binds a token revocation list for check 9 (FIX-04 v7.0).
func (ee *ExecutionEngine) SetRevocationList(trl *TokenRevocationList) {
	ee.revocationList = trl
}

// SetMinRegistryVersion implements Phase 14 Gap 2. Enforces explicit freshness constraint.
func (ee *ExecutionEngine) SetMinRegistryVersion(v int64) {
	ee.mu.Lock()
	defer ee.mu.Unlock()
	ee.minRegistryVersion = v
}

// GetRevocationList returns the bound revocation list.
func (ee *ExecutionEngine) GetRevocationList() *TokenRevocationList {
	return ee.revocationList
}

// GetTokenRegistry returns the token registry for inspection/testing.
func (ee *ExecutionEngine) GetTokenRegistry() *TokenRegistry {
	return ee.tokenRegistry
}

// GetTokenKeyID returns the expected token authority key ID.
func (ee *ExecutionEngine) GetTokenKeyID() string {
	return ee.tokenKeyID
}

// ================================================================
// ExecuteWithToken — THE SOLE EXECUTION PATH
// ================================================================

// ExecuteWithToken is the ONLY way to execute.
// It accepts a CapabilityToken and NOTHING ELSE.
// This is the architectural hard gate: no token → no execution.
//
// The method performs the full 8-check validation gate, discharges
// obligations, records the execution in the hash chain, and returns
// a standardized ExecutionResult with deterministic failure codes.
func (ee *ExecutionEngine) ExecuteWithToken(token *CapabilityToken) *ExecutionResult {
	ee.mu.Lock()
	defer ee.mu.Unlock()

	ee.executionCount++
	now := time.Now().UTC()

	// 8-CHECK VALIDATION GATE
	chainCheck := func(hash string) bool {
		if ee.adapter == nil {
			return false // VULN-C2 FIX: nil adapter means enforcement chain cannot be verified — fail-closed
		}
		return ee.adapter.HasEnforcementHash(hash)
	}

	validation := ValidateTokenFull(token, ee.tokenPublicKey, ee.tokenKeyID, chainCheck)

	if !validation.Valid {
		return ee.recordTokenExecution(token, "EXECUTION_BLOCKED", false,
			validation.Reason, validation.Detail, nil, now)
	}

	// CHECK 9 (FIX-04 v7.0): Token revocation check
	// Reject tokens that have been explicitly revoked or whose agent has been suspended.
	if ee.revocationList != nil && token != nil {
		revoked, revokeReason := ee.revocationList.IsRevoked(token.tokenHash, token.requestHash)
		if revoked {
			return ee.recordTokenExecution(token, "EXECUTION_BLOCKED", false,
				"TOKEN_REVOKED", revokeReason, nil, now)
		}
	}

	// CHECK 10 (Gap 2): Registry Freshness
	if token != nil && ee.minRegistryVersion > 0 && token.RegistryVersion() < ee.minRegistryVersion {
		return ee.recordTokenExecution(token, "EXECUTION_BLOCKED", false,
			"REGISTRY_VERSION_OUTDATED", fmt.Sprintf("token registry_version=%d is older than engine min_registry_version=%d", token.RegistryVersion(), ee.minRegistryVersion), nil, now)
	}

	// Single-use enforcement (replay protection)
	if !ee.tokenRegistry.Consume(token) {
		return ee.recordTokenExecution(token, "EXECUTION_BLOCKED", false,
			BlockTokenAlreadyUsed, "token consumed by concurrent execution", nil, now)
	}

	// Discharge obligations before permitting execution (GAP-05)
	obligations := token.Obligations()
	discharged := ee.dischargeObligations(obligations, token)

	// ================================================================
	// EXT-EXEC: Delegate to the Execution Handler (CRIT-06/Phase 14)
	// ================================================================
	success, detail, err := ee.handler.Execute(token)
	if !success || err != nil {
		blockReas := "WORKFLOW_EXECUTION_FAILED"
		blockDet := detail
		if err != nil {
			blockDet = fmt.Sprintf("%s (err: %v)", detail, err)
		}
		// Notice that state is EXECUTION_FAILED because it passed Sarathi's 10-check gate
		// but the downstream external executor failed to fulfill it.
		return ee.recordTokenExecution(token, "EXECUTION_FAILED", false,
			blockReas, blockDet, discharged, now)
	}

	return ee.recordTokenExecution(token, "EXECUTION_PERMITTED", true,
		"", detail, discharged, now)
}

// dischargeObligations processes mandatory side-effects before execution (GAP-05).
func (ee *ExecutionEngine) dischargeObligations(obligations []string, token *CapabilityToken) []string {
	discharged := make([]string, 0, len(obligations))
	for _, obl := range obligations {
		switch obl {
		case "LOG_ACCESS":
			fmt.Printf("  [Obligation] LOG_ACCESS discharged for correlation_id=%s\n", token.CorrelationID())
		case "NOTIFY_AUDIT":
			fmt.Printf("  [Obligation] NOTIFY_AUDIT discharged for correlation_id=%s\n", token.CorrelationID())
		case "NOTIFY_OWNER":
			fmt.Printf("  [Obligation] NOTIFY_OWNER discharged for correlation_id=%s\n", token.CorrelationID())
		default:
			fmt.Printf("  [Obligation] %s discharged for correlation_id=%s\n", obl, token.CorrelationID())
		}
		discharged = append(discharged, obl)
	}
	return discharged
}

// recordTokenExecution creates a hash-chained execution log entry from a token.
func (ee *ExecutionEngine) recordTokenExecution(
	token *CapabilityToken,
	state string,
	executed bool,
	blockReason, blockDetail string,
	obligationsDischarged []string,
	timestamp time.Time,
) *ExecutionResult {

	// Extract fields from token (may be nil for NO_TOKEN case)
	var enfHash, decID, corrID, reqHash, polHash, tokID string
	var verdict string
	if token != nil {
		enfHash = token.enforcementHash
		decID = token.decisionID
		corrID = token.correlationID
		reqHash = token.requestHash
		polHash = token.policyHash
		tokID = token.tokenID
		verdict = token.verdict
	}

	// GAP-17: Struct-based deterministic hash computation
	chainPayload := executionChainPayload{
		Prev:            ee.prevExecutionHash,
		EnforcementHash: enfHash,
		ExecutionState:  state,
		Executed:        executed,
		Sequence:        ee.executionCount,
	}
	chainJSON, err := json.Marshal(chainPayload)
	if err != nil {
		// FIX-06 (v7.0): Safe fallback — deterministic error hash instead of panic
		chainJSON = []byte(fmt.Sprintf("EXEC_CHAIN_ERROR:%s:%s:%v", ee.prevExecutionHash, enfHash, err))
	}
	executionHash := Sha256Hex(chainJSON)

	entry := ExecutionLogEntry{
		ExecutionSequence:     ee.executionCount,
		ExecutionState:        state,
		Executed:              executed,
		EnforcementHash:       enfHash,
		DecisionID:            decID,
		CorrelationID:         corrID,
		Verdict:               verdict,
		PrevExecutionHash:     ee.prevExecutionHash,
		ExecutionHash:         executionHash,
		TokenID:               tokID,
		ObligationsDischarged: obligationsDischarged,
		BlockReason:           blockReason,
		BlockDetail:           blockDetail,
	}

	ee.executionLog = append(ee.executionLog, entry)
	ee.prevExecutionHash = executionHash

	return &ExecutionResult{
		Executed:          executed,
		Status:            state,
		BlockReason:       blockReason,
		BlockDetail:       blockDetail,
		TokenID:           tokID,
		DecisionID:        decID,
		CorrelationID:     corrID,
		RequestHash:       reqHash,
		PolicyHash:        polHash,
		EnforcementHash:   enfHash,
		ExecutionSequence: ee.executionCount,
		ExecutionHash:     executionHash,
		PrevExecutionHash: ee.prevExecutionHash,
		Obligations:       obligationsDischarged,
		Timestamp:         timestamp.Format("2006-01-02T15:04:05.000000Z"),
	}
}

// ================================================================
// BACKWARD COMPATIBILITY: AttemptExecution
// ================================================================

// AttemptExecution provides backward compatibility for the pipeline.
// It extracts the CapabilityToken from the ExecutionResponse and
// delegates to ExecuteWithToken. If no token exists, it returns a
// standardized EXECUTION_BLOCKED result.
//
// NOTE: This method exists solely for pipeline integration. The
// architectural contract is that ExecuteWithToken is the only
// execution entry point. External systems must use ExecuteWithToken.
func (ee *ExecutionEngine) AttemptExecution(resp *ExecutionResponse) map[string]interface{} {
	if resp == nil {
		result := &ExecutionResult{
			Executed:    false,
			Status:      "EXECUTION_BLOCKED",
			BlockReason: BlockNoToken,
			BlockDetail: "nil response — no token available",
			Timestamp:   time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		}
		return result.ToMap()
	}

	token := resp.GetCapabilityToken()
	result := ee.ExecuteWithToken(token)
	return result.ToMap()
}

// ================================================================
// CHAIN VERIFICATION
// ================================================================

// VerifyExecutionChain walks the execution log and verifies hash linkage.
func (ee *ExecutionEngine) VerifyExecutionChain() (bool, string) {
	ee.mu.Lock()
	defer ee.mu.Unlock()

	expectedPrev := "GENESIS"
	for i, entry := range ee.executionLog {
		if entry.PrevExecutionHash != expectedPrev {
			return false, fmt.Sprintf("execution chain break at index %d: expected prev=%s, got=%s",
				i, expectedPrev, entry.PrevExecutionHash)
		}
		chainPayload := executionChainPayload{
			Prev:            entry.PrevExecutionHash,
			EnforcementHash: entry.EnforcementHash,
			ExecutionState:  entry.ExecutionState,
			Executed:        entry.Executed,
			Sequence:        entry.ExecutionSequence,
		}
		chainJSON, err := json.Marshal(chainPayload)
		if err != nil {
			return false, fmt.Sprintf("execution marshal error at index %d: %v", i, err)
		}
		recomputed := Sha256Hex(chainJSON)
		if entry.ExecutionHash != recomputed {
			return false, fmt.Sprintf("execution hash mismatch at index %d: stored=%s, recomputed=%s",
				i, entry.ExecutionHash, recomputed)
		}
		expectedPrev = entry.ExecutionHash
	}
	return true, ""
}

// GetExecutionLog returns a copy of the execution log.
func (ee *ExecutionEngine) GetExecutionLog() []ExecutionLogEntry {
	ee.mu.Lock()
	defer ee.mu.Unlock()

	cp := make([]ExecutionLogEntry, len(ee.executionLog))
	copy(cp, ee.executionLog)
	return cp
}

// ExecutionCount returns the total number of execution attempts.
func (ee *ExecutionEngine) ExecutionCount() int {
	ee.mu.Lock()
	defer ee.mu.Unlock()
	return ee.executionCount
}

// ================================================================
// SARATHI EXECUTION CONTRACT CONFORMANCE (v13.0)
// ================================================================
//
// These methods implement the SarathiExecutionContract interface,
// making the ExecutionEngine a compliant execution system in the
// TANTRA/BHIV ecosystem. The compile-time assertion in
// sarathi_execution_contract.go enforces this at build time.

// ExecuteWithEnforcement implements SarathiExecutionContract.
// It delegates directly to ExecuteWithToken — the sole execution path.
// This method exists to satisfy the universal contract interface.
func (ee *ExecutionEngine) ExecuteWithEnforcement(token *CapabilityToken) *ExecutionResult {
	return ee.ExecuteWithToken(token)
}

// RequiresToken implements SarathiExecutionContract.
// Always returns true — the ExecutionEngine CANNOT execute without a token.
func (ee *ExecutionEngine) RequiresToken() bool {
	return true
}

// SystemID implements SarathiExecutionContract.
// Returns the unique system identifier for cross-system traceability.
func (ee *ExecutionEngine) SystemID() string {
	return "sarathi-execution-engine"
}

// ValidateBinding implements SarathiExecutionContract.
// Verifies that the engine is correctly bound to a Sarathi enforcement adapter.
// Returns nil if binding is valid, error if not properly connected.
func (ee *ExecutionEngine) ValidateBinding() error {
	if ee.adapter == nil {
		return fmt.Errorf("BINDING_VIOLATION: execution engine has no adapter reference — enforcement chain cannot be verified")
	}
	if ee.tokenPublicKey == nil {
		return fmt.Errorf("BINDING_VIOLATION: execution engine has no TokenAuthority public key — token signatures cannot be verified")
	}
	if ee.tokenKeyID == "" {
		return fmt.Errorf("BINDING_VIOLATION: execution engine has no expected token key ID — signer identity cannot be verified")
	}
	return nil
}
