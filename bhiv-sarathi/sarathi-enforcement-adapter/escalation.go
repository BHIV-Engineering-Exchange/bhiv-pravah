package main

// escalation.go — Escalation queue for ESCALATE verdicts (GAP-10).
//
// When the PDP returns ESCALATE, the request requires human review.
// The EscalationQueue holds pending escalations with automatic timeout.
// After timeout, the escalation auto-denies (fail-closed).
//
// Production integration: This queue would be backed by a durable store
// (database, message queue) and connected to a human review UI.
// The current implementation is in-memory for local testing.

import (
	"fmt"
	"sync"
	"time"
)

// DefaultEscalationTimeout is how long an ESCALATE verdict waits for
// human review before auto-denying. Fail-closed by design.
const DefaultEscalationTimeout = 5 * time.Minute

// EscalationEntry represents a pending escalation requiring human review.
type EscalationEntry struct {
	EnforcementHash string
	CorrelationID   string
	Verdict         string
	Reason          string
	AgentRole       string
	ResourceType    string
	EnqueuedAt      time.Time
	ExpiresAt       time.Time
	Status          string // PENDING, APPROVED, DENIED, EXPIRED
	ReviewedBy      string // who reviewed (empty if not yet reviewed)
	ReviewedAt      time.Time
}

// EscalationQueue manages ESCALATE verdicts awaiting human review.
type EscalationQueue struct {
	mu      sync.Mutex
	entries []EscalationEntry
	timeout time.Duration
}

// NewEscalationQueue creates an escalation queue with default timeout.
func NewEscalationQueue() *EscalationQueue {
	eq := &EscalationQueue{
		timeout: DefaultEscalationTimeout,
	}
	// VULN-H3 FIX: Start background auto-expire goroutine
	go eq.autoExpireLoop()
	return eq
}

// autoExpireLoop periodically expires stale PENDING escalations.
// Runs every 30 seconds. Fail-closed: stale escalations auto-deny.
func (eq *EscalationQueue) autoExpireLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		expired := eq.ExpireStale()
		if expired > 0 {
			fmt.Printf("[Escalation] Auto-expired %d stale escalations (fail-closed)\n", expired)
		}
	}
}

// Enqueue adds an ESCALATE enforcement response to the review queue.
func (eq *EscalationQueue) Enqueue(resp *ExecutionResponse) {
	eq.mu.Lock()
	defer eq.mu.Unlock()

	now := time.Now().UTC()
	entry := EscalationEntry{
		EnforcementHash: resp.EnforcementHash(),
		CorrelationID:   resp.CorrelationID(),
		Verdict:         resp.Verdict(),
		Reason:          resp.PDPReason(),
		AgentRole:       resp.AgentRoleField(),
		ResourceType:    resp.ResourceTypeField(),
		EnqueuedAt:      now,
		ExpiresAt:       now.Add(eq.timeout),
		Status:          "PENDING",
	}
	eq.entries = append(eq.entries, entry)
	fmt.Printf("[Escalation] Queued: correlation_id=%s, expires_at=%s\n",
		entry.CorrelationID, entry.ExpiresAt.Format("2006-01-02T15:04:05Z"))
}

// Review processes a human review decision on a pending escalation.
// Returns true if the escalation was found and updated, false otherwise.
func (eq *EscalationQueue) Review(correlationID, decision, reviewer string) bool {
	eq.mu.Lock()
	defer eq.mu.Unlock()

	for i := range eq.entries {
		if eq.entries[i].CorrelationID == correlationID && eq.entries[i].Status == "PENDING" {
			if decision == "APPROVE" {
				eq.entries[i].Status = "APPROVED"
			} else {
				eq.entries[i].Status = "DENIED"
			}
			eq.entries[i].ReviewedBy = reviewer
			eq.entries[i].ReviewedAt = time.Now().UTC()
			return true
		}
	}
	return false
}

// ExpireStale marks all timed-out PENDING escalations as EXPIRED (auto-deny).
// This should be called periodically in production.
func (eq *EscalationQueue) ExpireStale() int {
	eq.mu.Lock()
	defer eq.mu.Unlock()

	now := time.Now().UTC()
	expired := 0
	for i := range eq.entries {
		if eq.entries[i].Status == "PENDING" && now.After(eq.entries[i].ExpiresAt) {
			eq.entries[i].Status = "EXPIRED"
			expired++
		}
	}
	return expired
}

// PendingCount returns the number of PENDING escalations.
func (eq *EscalationQueue) PendingCount() int {
	eq.mu.Lock()
	defer eq.mu.Unlock()

	count := 0
	for _, e := range eq.entries {
		if e.Status == "PENDING" {
			count++
		}
	}
	return count
}

// TotalCount returns the total number of escalation entries.
func (eq *EscalationQueue) TotalCount() int {
	eq.mu.Lock()
	defer eq.mu.Unlock()
	return len(eq.entries)
}

// GetEntries returns a copy of all escalation entries.
func (eq *EscalationQueue) GetEntries() []EscalationEntry {
	eq.mu.Lock()
	defer eq.mu.Unlock()

	cp := make([]EscalationEntry, len(eq.entries))
	copy(cp, eq.entries)
	return cp
}
