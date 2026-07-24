package main

// jsonl_audit_sink.go — JSONL File-Based Fallback Audit Sink.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Fallback Audit (v14.4)
// Host Organization: Blackhole Infiverse (BHIV)
//
// PURPOSE:
//   When PostgreSQL is unavailable, this sink persists ALL enforcement
//   decisions, chain entries, and system events to JSONL files in proof_logs/.
//   This ensures zero audit data loss even without a database.
//
// FORMAT:
//   Each line is a complete JSON object (standard JSONL format).
//   Files are append-only, thread-safe via sync.Mutex per file.
//
// FILES:
//   proof_logs/enforcement_audit_backup.jsonl - enforcement decisions
//   proof_logs/chain_audit_backup.jsonl       - hash chain entries
//   proof_logs/system_events_backup.jsonl     - system events

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"
)

// JSONLAuditSink writes audit records to JSONL files for durable backup.
// Implements the AuditSink interface from saarthi_service.go.
type JSONLAuditSink struct {
	enfMu    sync.Mutex
	chainMu  sync.Mutex
	eventMu  sync.Mutex
	enfFile  *os.File
	chainFile *os.File
	eventFile *os.File
}

// NewJSONLAuditSink creates a new JSONL-backed audit sink.
// Creates the proof_logs/ directory if it doesn't exist.
func NewJSONLAuditSink() (*JSONLAuditSink, error) {
	if err := os.MkdirAll("proof_logs", 0755); err != nil {
		return nil, fmt.Errorf("failed to create proof_logs directory: %w", err)
	}

	enfFile, err := os.OpenFile("proof_logs/enforcement_audit_backup.jsonl",
		os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return nil, fmt.Errorf("failed to open enforcement backup: %w", err)
	}

	chainFile, err := os.OpenFile("proof_logs/chain_audit_backup.jsonl",
		os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		enfFile.Close()
		return nil, fmt.Errorf("failed to open chain backup: %w", err)
	}

	eventFile, err := os.OpenFile("proof_logs/system_events_backup.jsonl",
		os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		enfFile.Close()
		chainFile.Close()
		return nil, fmt.Errorf("failed to open events backup: %w", err)
	}

	return &JSONLAuditSink{
		enfFile:   enfFile,
		chainFile: chainFile,
		eventFile: eventFile,
	}, nil
}

// RecordEnforcement persists an enforcement decision to JSONL.
func (s *JSONLAuditSink) RecordEnforcement(req *SaarthiRequest, resp *SaarthiResponse) error {
	record := map[string]interface{}{
		"timestamp":         time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		"correlation_id":    req.CorrelationID,
		"agent_id":          req.AgentID,
		"resource_id":       req.ResourceID,
		"action":            req.Action,
		"verdict":           resp.Verdict,
		"decision_id":       resp.DecisionID,
		"enforcement_hash":  resp.EnforcementHash,
		"request_hash":      resp.RequestHash,
		"policy_version":    resp.PolicyVersion,
		"policy_hash":       resp.PolicyHash,
		"caller_system":     req.CallerSystem,
		"executed":          resp.Executed,
		"block_reason":      resp.BlockReason,
		"execution_state":   resp.ExecutionState,
		"registry_version":  resp.RegistryVersion,
		"obligations":       resp.Obligations,
		"trace_id":          resp.TraceID,
		"error_code":        resp.ErrorCode,
		"schema_version":    resp.SchemaVersion,
		"enforcement_token": resp.EnforcementToken,
		"execution_id":      resp.ExecutionID,
		// v14.5 Cross-System Propagation Layer fields. Empty strings for
		// legacy (non-envelope) decisions — preserved for schema stability.
		"response_hash":      resp.ResponseHash,
		"chain_binding_hash": resp.ChainBindingHash,
		"pdp_decision_id":    resp.PDPDecisionID,
	}

	data, err := json.Marshal(record)
	if err != nil {
		return fmt.Errorf("failed to marshal enforcement record: %w", err)
	}

	s.enfMu.Lock()
	defer s.enfMu.Unlock()
	_, err = s.enfFile.Write(append(data, '\n'))
	return err
}

// RecordSystemEvent persists a system event to JSONL.
func (s *JSONLAuditSink) RecordSystemEvent(eventType, detail string) error {
	record := map[string]interface{}{
		"timestamp":  time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		"event_type": eventType,
		"detail":     detail,
	}

	data, err := json.Marshal(record)
	if err != nil {
		return fmt.Errorf("failed to marshal system event: %w", err)
	}

	s.eventMu.Lock()
	defer s.eventMu.Unlock()
	_, err = s.eventFile.Write(append(data, '\n'))
	return err
}

// RecordChainEntry persists a chain entry to JSONL.
func (s *JSONLAuditSink) RecordChainEntry(entry EnforcementTraceEntry) error {
	data, err := json.Marshal(entry)
	if err != nil {
		return fmt.Errorf("failed to marshal chain entry: %w", err)
	}

	s.chainMu.Lock()
	defer s.chainMu.Unlock()
	_, err = s.chainFile.Write(append(data, '\n'))
	return err
}

// Close syncs and closes all JSONL files.
func (s *JSONLAuditSink) Close() error {
	s.enfMu.Lock()
	s.enfFile.Sync()
	s.enfFile.Close()
	s.enfMu.Unlock()

	s.chainMu.Lock()
	s.chainFile.Sync()
	s.chainFile.Close()
	s.chainMu.Unlock()

	s.eventMu.Lock()
	s.eventFile.Sync()
	s.eventFile.Close()
	s.eventMu.Unlock()

	return nil
}

// IsDurable returns true — JSONL files persist beyond process lifetime.
func (s *JSONLAuditSink) IsDurable() bool { return true }

// FallbackAuditSink wraps both InMemoryAuditSink (for in-process queries)
// and JSONLAuditSink (for durable file-based backup). Every write goes to both.
type FallbackAuditSink struct {
	memory *InMemoryAuditSink
	jsonl  *JSONLAuditSink
}

// NewFallbackAuditSink creates a composite sink that writes to both memory and JSONL.
func NewFallbackAuditSink() (*FallbackAuditSink, error) {
	jsonlSink, err := NewJSONLAuditSink()
	if err != nil {
		return nil, fmt.Errorf("failed to create JSONL audit sink: %w", err)
	}
	return &FallbackAuditSink{
		memory: NewInMemoryAuditSink(),
		jsonl:  jsonlSink,
	}, nil
}

func (f *FallbackAuditSink) RecordEnforcement(req *SaarthiRequest, resp *SaarthiResponse) error {
	_ = f.memory.RecordEnforcement(req, resp) // memory never fails
	return f.jsonl.RecordEnforcement(req, resp)
}

func (f *FallbackAuditSink) RecordSystemEvent(eventType, detail string) error {
	_ = f.memory.RecordSystemEvent(eventType, detail)
	return f.jsonl.RecordSystemEvent(eventType, detail)
}

func (f *FallbackAuditSink) RecordChainEntry(entry EnforcementTraceEntry) error {
	_ = f.memory.RecordChainEntry(entry)
	return f.jsonl.RecordChainEntry(entry)
}

func (f *FallbackAuditSink) Close() error {
	f.memory.Close()
	return f.jsonl.Close()
}

// IsDurable returns true — the JSONL component persists data.
func (f *FallbackAuditSink) IsDurable() bool { return true }

// GetEnforcements exposes the in-memory enforcements for testing.
func (f *FallbackAuditSink) GetEnforcements() []AuditRecord {
	return f.memory.GetEnforcements()
}

// GetEvents exposes the in-memory events for testing.
func (f *FallbackAuditSink) GetEvents() []SystemEventRecord {
	return f.memory.GetEvents()
}
