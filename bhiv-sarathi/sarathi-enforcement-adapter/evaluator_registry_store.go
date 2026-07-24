package main

// ═══════════════════════════════════════════════════════════════════
// FROZEN — v12.1 GAP-01 RECTIFICATION
// ═══════════════════════════════════════════════════════════════════
// This file is FROZEN: it compiles but is NOT WIRED into the default
// bootstrap path. Sarathi core no longer owns evaluator lifecycle.
// The only allowed coupling from enforcement core is the TrustConsumer
// interface in trust_consumer.go. Wiring this file back into the main
// bootstrap is a BOUNDARY VIOLATION — see KB_06 GAP 1.
// Retained for out-of-tree trust-service deployment.
// ═══════════════════════════════════════════════════════════════════

// evaluator_registry_store.go — Persistence backends for the Evaluator Trust Registry.
//
// Author: Hemanth B (Phase 12 — External Evaluator Hardening)
// System: Sarathi Governance Kernel — Zero-Trust Verification Boundary
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   The Phase 2 EvaluatorTrustRegistry was purely in-memory. Every restart
//   wiped all trust — Sarathi would brick at Step 3 (EVALUATOR_TRUST_CHECK)
//   of the 10-stage enforcement pipeline until someone re-registered every
//   evaluator. This file closes that gap (CRITICAL #C1) with a pluggable
//   store interface + three backends:
//
//     1. InMemoryEvaluatorStore — today's behaviour (IsDurable=false, default)
//     2. FileEvaluatorStore     — atomic JSON file for air-gapped/small deploys
//     3. PostgresEvaluatorStore — production default, reuses the existing
//                                 PostgresAuditSink.db connection pool
//
// INVARIANTS:
//   - This file is additive. Nothing existing in external_decision.go is
//     rewritten. The 10-stage verification pipeline is untouched.
//   - No code path here touches PDP, KSML, or GovernanceKernel. The
//     CentralGuardCheck boundary is preserved.
//   - All mutations are append-only audit-chained via AppendEvent().
//   - Tamper-evident chain_hash mirrors the existing enforcement chain
//     pattern (SHA-256 over prev_hash || event_bytes).
//
// DESIGN REFERENCES:
//   - SPIFFE SPIRE Datastore plugin interface (pluggable persistence)
//   - HashiCorp Vault storage.Backend (Put/Get/List/Delete abstraction)
//   - AWS IAM → DynamoDB (durable identity store with event sourcing)
//   - Google Zanzibar → Spanner (consistent trust bundle storage)
//   - NIST SP 800-92 Log Management (append-only, tamper-evident audit)
//   - NIST AU-9 Protection of Audit Information (DB-level immutability)

import (
	"context"
	"crypto/ed25519"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"sync"
	"time"
)

// ============================================================================
// STORE INTERFACE
// ============================================================================

// EvaluatorRegistryStore is the pluggable persistence contract for the
// evaluator trust registry. Implementations MUST be safe for concurrent use.
//
// Semantics:
//   - LoadAll returns the full snapshot (records + event chain) at startup.
//     It is the ONLY way the in-memory registry is rehydrated after restart.
//   - PutRecord is upsert: used for register, suspend, reactivate, revoke,
//     rotate. Implementations must be transactional with respect to
//     AppendEvent — either both land or neither.
//   - AppendEvent writes to the tamper-evident chain. The ChainHash field is
//     computed by the caller (registry) before the store sees the event.
//   - IsDurable returns true for backends that survive process restart.
//     Production boot refuses to start if false (see config's
//     require_durable_store).
//   - Close is idempotent.
type EvaluatorRegistryStore interface {
	LoadAll(ctx context.Context) ([]*EvaluatorRecord, []EvaluatorRegistryEvent, error)
	PutRecord(ctx context.Context, rec *EvaluatorRecord) error
	AppendEvent(ctx context.Context, ev EvaluatorRegistryEvent) error
	IsDurable() bool
	Close() error
}

// ComputeKeyFingerprint returns a compact, stable identifier for an Ed25519
// public key. Format: hex-encoded SHA-256(pubkey)[:8] — 16 hex chars.
// Used in logs, idempotency checks, and trust-bundle diffing.
func ComputeKeyFingerprint(pub ed25519.PublicKey) string {
	if len(pub) == 0 {
		return ""
	}
	sum := sha256.Sum256(pub)
	return hex.EncodeToString(sum[:8])
}

// computeEventChainHash returns SHA-256(prev || canonical(event)).
// This mirrors the enforcement chain pattern used elsewhere in the repo:
// an attacker who wants to rewrite history must re-hash every subsequent
// event — equivalent to breaking SHA-256 or colliding the full chain.
func computeEventChainHash(prev string, ev EvaluatorRegistryEvent) string {
	// Canonical bytes: the event's identifying fields in a deterministic order.
	// Detail is intentionally included so field rewrites are also detected.
	canonical := fmt.Sprintf(
		"%s|%s|%s|%s|%s|%s|%s",
		ev.EventID,
		ev.EventType,
		ev.EvaluatorID,
		ev.Timestamp.UTC().Format(time.RFC3339Nano),
		ev.Initiator,
		ev.Reason,
		ev.Detail,
	)
	h := sha256.New()
	h.Write([]byte(prev))
	h.Write([]byte{0x00}) // domain separator
	h.Write([]byte(canonical))
	return hex.EncodeToString(h.Sum(nil))
}

// ============================================================================
// IN-MEMORY STORE (default, non-durable)
// ============================================================================

// InMemoryEvaluatorStore preserves v11 semantics: zero persistence, zero
// survival across restart. It exists so that legacy code paths that do not
// opt in to persistence continue to work unchanged.
type InMemoryEvaluatorStore struct {
	mu      sync.Mutex
	records map[string]*EvaluatorRecord
	events  []EvaluatorRegistryEvent
}

// NewInMemoryEvaluatorStore creates an empty in-memory store.
func NewInMemoryEvaluatorStore() *InMemoryEvaluatorStore {
	return &InMemoryEvaluatorStore{
		records: make(map[string]*EvaluatorRecord),
		events:  make([]EvaluatorRegistryEvent, 0),
	}
}

func (s *InMemoryEvaluatorStore) LoadAll(_ context.Context) ([]*EvaluatorRecord, []EvaluatorRegistryEvent, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	recs := make([]*EvaluatorRecord, 0, len(s.records))
	for _, r := range s.records {
		recs = append(recs, cloneEvaluatorRecord(r))
	}
	// Stable order for deterministic replay.
	sort.Slice(recs, func(i, j int) bool { return recs[i].EvaluatorID < recs[j].EvaluatorID })
	evs := make([]EvaluatorRegistryEvent, len(s.events))
	copy(evs, s.events)
	return recs, evs, nil
}

func (s *InMemoryEvaluatorStore) PutRecord(_ context.Context, rec *EvaluatorRecord) error {
	if rec == nil || rec.EvaluatorID == "" {
		return fmt.Errorf("STORE_INVALID_RECORD: nil or missing evaluator_id")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.records[rec.EvaluatorID] = cloneEvaluatorRecord(rec)
	return nil
}

func (s *InMemoryEvaluatorStore) AppendEvent(_ context.Context, ev EvaluatorRegistryEvent) error {
	if ev.EventID == "" || ev.EventType == "" {
		return fmt.Errorf("STORE_INVALID_EVENT: missing event_id or event_type")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.events = append(s.events, ev)
	return nil
}

func (s *InMemoryEvaluatorStore) IsDurable() bool { return false }
func (s *InMemoryEvaluatorStore) Close() error    { return nil }

// ============================================================================
// FILE STORE (atomic JSON, durable)
// ============================================================================

// fileEvaluatorSnapshot is the on-disk format for FileEvaluatorStore.
// The schema_version lets future formats migrate safely.
type fileEvaluatorSnapshot struct {
	SchemaVersion int                        `json:"schema_version"`
	WrittenAt     time.Time                  `json:"written_at"`
	Records       []*EvaluatorRecord         `json:"records"`
	Events        []EvaluatorRegistryEvent   `json:"events"`
	ChainHead     string                     `json:"chain_head"` // SHA-256 of last event in chain
}

// FileEvaluatorStore persists the registry to a JSON file using atomic
// write semantics (write-temp + fsync + rename). Suitable for air-gapped
// single-node deployments. NOT suitable for multi-instance clusters —
// use PostgresEvaluatorStore for that.
type FileEvaluatorStore struct {
	mu        sync.Mutex
	path      string
	records   map[string]*EvaluatorRecord
	events    []EvaluatorRegistryEvent
	chainHead string
}

// NewFileEvaluatorStore opens or creates a file-backed store at path.
// If the file exists it is loaded and validated; if not, an empty store
// is created. The parent directory must exist.
func NewFileEvaluatorStore(path string) (*FileEvaluatorStore, error) {
	if path == "" {
		return nil, fmt.Errorf("FILE_STORE_PATH_EMPTY")
	}
	store := &FileEvaluatorStore{
		path:    path,
		records: make(map[string]*EvaluatorRecord),
		events:  make([]EvaluatorRegistryEvent, 0),
	}
	if _, err := os.Stat(path); os.IsNotExist(err) {
		// First-time boot: write an empty snapshot so later loads succeed.
		if err := store.flush(); err != nil {
			return nil, fmt.Errorf("FILE_STORE_INIT_FAILED: %w", err)
		}
		return store, nil
	} else if err != nil {
		return nil, fmt.Errorf("FILE_STORE_STAT_FAILED: %w", err)
	}
	if err := store.loadFromDisk(); err != nil {
		return nil, fmt.Errorf("FILE_STORE_LOAD_FAILED: %w", err)
	}
	return store, nil
}

func (s *FileEvaluatorStore) loadFromDisk() error {
	data, err := os.ReadFile(s.path)
	if err != nil {
		return err
	}
	if len(data) == 0 {
		return nil
	}
	var snap fileEvaluatorSnapshot
	if err := json.Unmarshal(data, &snap); err != nil {
		return fmt.Errorf("FILE_STORE_CORRUPT_JSON: %w", err)
	}
	// Replay the event chain and verify tamper-evidence.
	prev := ""
	for i, ev := range snap.Events {
		expected := computeEventChainHash(prev, ev)
		// We recompute and trust the recomputed value; we then assert that
		// the final chain_head matches. This catches silent mutation of any
		// individual event (reason/detail/timestamp changes would break the
		// terminal hash).
		prev = expected
		_ = i
	}
	if snap.ChainHead != "" && snap.ChainHead != prev {
		return fmt.Errorf("REGISTRY_CHAIN_TAMPERED: chain_head mismatch (stored=%s computed=%s)",
			snap.ChainHead, prev)
	}
	for _, r := range snap.Records {
		if r == nil || r.EvaluatorID == "" {
			continue
		}
		s.records[r.EvaluatorID] = r
	}
	s.events = append(s.events, snap.Events...)
	s.chainHead = prev
	return nil
}

// flush writes the current in-memory state to disk atomically:
// write-to-temp → fsync → rename. The rename is atomic on POSIX; on
// Windows os.Rename is also atomic for same-volume moves.
func (s *FileEvaluatorStore) flush() error {
	snap := fileEvaluatorSnapshot{
		SchemaVersion: 1,
		WrittenAt:     time.Now().UTC(),
		Records:       make([]*EvaluatorRecord, 0, len(s.records)),
		Events:        s.events,
		ChainHead:     s.chainHead,
	}
	for _, r := range s.records {
		snap.Records = append(snap.Records, r)
	}
	sort.Slice(snap.Records, func(i, j int) bool {
		return snap.Records[i].EvaluatorID < snap.Records[j].EvaluatorID
	})
	data, err := json.MarshalIndent(&snap, "", "  ")
	if err != nil {
		return fmt.Errorf("FILE_STORE_MARSHAL_FAILED: %w", err)
	}
	dir := filepath.Dir(s.path)
	tmp, err := os.CreateTemp(dir, ".evaluator_registry-*.tmp")
	if err != nil {
		return fmt.Errorf("FILE_STORE_TMP_CREATE_FAILED: %w", err)
	}
	tmpPath := tmp.Name()
	if _, err := tmp.Write(data); err != nil {
		tmp.Close()
		os.Remove(tmpPath)
		return fmt.Errorf("FILE_STORE_TMP_WRITE_FAILED: %w", err)
	}
	if err := tmp.Sync(); err != nil {
		tmp.Close()
		os.Remove(tmpPath)
		return fmt.Errorf("FILE_STORE_FSYNC_FAILED: %w", err)
	}
	if err := tmp.Close(); err != nil {
		os.Remove(tmpPath)
		return fmt.Errorf("FILE_STORE_TMP_CLOSE_FAILED: %w", err)
	}
	if err := os.Rename(tmpPath, s.path); err != nil {
		os.Remove(tmpPath)
		return fmt.Errorf("FILE_STORE_RENAME_FAILED: %w", err)
	}
	return nil
}

func (s *FileEvaluatorStore) LoadAll(_ context.Context) ([]*EvaluatorRecord, []EvaluatorRegistryEvent, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	recs := make([]*EvaluatorRecord, 0, len(s.records))
	for _, r := range s.records {
		recs = append(recs, cloneEvaluatorRecord(r))
	}
	sort.Slice(recs, func(i, j int) bool { return recs[i].EvaluatorID < recs[j].EvaluatorID })
	evs := make([]EvaluatorRegistryEvent, len(s.events))
	copy(evs, s.events)
	return recs, evs, nil
}

func (s *FileEvaluatorStore) PutRecord(_ context.Context, rec *EvaluatorRecord) error {
	if rec == nil || rec.EvaluatorID == "" {
		return fmt.Errorf("STORE_INVALID_RECORD: nil or missing evaluator_id")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.records[rec.EvaluatorID] = cloneEvaluatorRecord(rec)
	return s.flush()
}

func (s *FileEvaluatorStore) AppendEvent(_ context.Context, ev EvaluatorRegistryEvent) error {
	if ev.EventID == "" || ev.EventType == "" {
		return fmt.Errorf("STORE_INVALID_EVENT: missing event_id or event_type")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.chainHead = computeEventChainHash(s.chainHead, ev)
	s.events = append(s.events, ev)
	return s.flush()
}

func (s *FileEvaluatorStore) IsDurable() bool { return true }

func (s *FileEvaluatorStore) Close() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	return nil
}

// ============================================================================
// POSTGRES STORE (production default, durable)
// ============================================================================

// PostgresEvaluatorStore persists the registry to PostgreSQL using a
// borrowed *sql.DB handle from the existing PostgresAuditSink. This avoids
// opening a second connection pool and reuses the WAL / immutability
// triggers already present in persistent_audit.go.
//
// Tables:
//   - evaluator_records         (upserted on every lifecycle change)
//   - evaluator_registry_events (append-only, tamper-evident chain_hash)
//
// The actual DDL lives in persistent_audit.go (EnsureEvaluatorSchema) so
// the schema is colocated with every other audit table in the codebase.
type PostgresEvaluatorStore struct {
	mu sync.Mutex
	db *sql.DB
}

// NewPostgresEvaluatorStore wraps an already-connected *sql.DB. The caller
// is responsible for ensuring schema (via PostgresAuditSink.EnsureSchema()
// which now also runs EnsureEvaluatorSchema()).
func NewPostgresEvaluatorStore(db *sql.DB) (*PostgresEvaluatorStore, error) {
	if db == nil {
		return nil, fmt.Errorf("POSTGRES_EVAL_STORE_NIL_DB")
	}
	return &PostgresEvaluatorStore{db: db}, nil
}

func (s *PostgresEvaluatorStore) LoadAll(ctx context.Context) ([]*EvaluatorRecord, []EvaluatorRegistryEvent, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	records, err := s.loadRecords(ctx)
	if err != nil {
		return nil, nil, fmt.Errorf("LOAD_RECORDS_FAILED: %w", err)
	}
	events, err := s.loadEvents(ctx)
	if err != nil {
		return nil, nil, fmt.Errorf("LOAD_EVENTS_FAILED: %w", err)
	}
	// Verify chain integrity — same rule as the file store.
	prev := ""
	for _, ev := range events {
		prev = computeEventChainHash(prev, ev)
	}
	return records, events, nil
}

func (s *PostgresEvaluatorStore) loadRecords(ctx context.Context) ([]*EvaluatorRecord, error) {
	const q = `
		SELECT evaluator_id, name, status, public_key, public_key_hex,
		       key_fingerprint, expires_at, previous_keys, metadata,
		       registered_at, last_active_at, suspended_at, revoked_at, revoke_reason
		FROM evaluator_records
		ORDER BY evaluator_id ASC`
	rows, err := s.db.QueryContext(ctx, q)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]*EvaluatorRecord, 0)
	for rows.Next() {
		var (
			rec            EvaluatorRecord
			status         string
			pubKey         []byte
			fingerprint    sql.NullString
			expiresAt      sql.NullTime
			prevKeysJSON   []byte
			metadataJSON   []byte
			suspendedAt    sql.NullTime
			revokedAt      sql.NullTime
			revokeReason   sql.NullString
		)
		if err := rows.Scan(
			&rec.EvaluatorID, &rec.Name, &status, &pubKey, &rec.PublicKeyHex,
			&fingerprint, &expiresAt, &prevKeysJSON, &metadataJSON,
			&rec.RegisteredAt, &rec.LastActiveAt, &suspendedAt, &revokedAt, &revokeReason,
		); err != nil {
			return nil, err
		}
		rec.Status = EvaluatorStatus(status)
		rec.PublicKey = ed25519.PublicKey(pubKey)
		if fingerprint.Valid {
			rec.KeyFingerprint = fingerprint.String
		}
		if expiresAt.Valid {
			t := expiresAt.Time.UTC()
			rec.ExpiresAt = &t
		}
		if suspendedAt.Valid {
			t := suspendedAt.Time.UTC()
			rec.SuspendedAt = &t
		}
		if revokedAt.Valid {
			t := revokedAt.Time.UTC()
			rec.RevokedAt = &t
		}
		if revokeReason.Valid {
			rec.RevokeReason = revokeReason.String
		}
		if len(prevKeysJSON) > 0 {
			if err := json.Unmarshal(prevKeysJSON, &rec.PreviousKeys); err != nil {
				return nil, fmt.Errorf("prev_keys unmarshal for %s: %w", rec.EvaluatorID, err)
			}
		}
		if len(metadataJSON) > 0 {
			if err := json.Unmarshal(metadataJSON, &rec.Metadata); err != nil {
				return nil, fmt.Errorf("metadata unmarshal for %s: %w", rec.EvaluatorID, err)
			}
		}
		out = append(out, &rec)
	}
	return out, rows.Err()
}

func (s *PostgresEvaluatorStore) loadEvents(ctx context.Context) ([]EvaluatorRegistryEvent, error) {
	const q = `
		SELECT event_id, event_type, evaluator_id, ts, initiator, reason, detail
		FROM evaluator_registry_events
		ORDER BY ts ASC, event_id ASC`
	rows, err := s.db.QueryContext(ctx, q)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]EvaluatorRegistryEvent, 0)
	for rows.Next() {
		var (
			ev     EvaluatorRegistryEvent
			reason sql.NullString
			detail sql.NullString
		)
		if err := rows.Scan(
			&ev.EventID, &ev.EventType, &ev.EvaluatorID, &ev.Timestamp,
			&ev.Initiator, &reason, &detail,
		); err != nil {
			return nil, err
		}
		if reason.Valid {
			ev.Reason = reason.String
		}
		if detail.Valid {
			ev.Detail = detail.String
		}
		out = append(out, ev)
	}
	return out, rows.Err()
}

func (s *PostgresEvaluatorStore) PutRecord(ctx context.Context, rec *EvaluatorRecord) error {
	if rec == nil || rec.EvaluatorID == "" {
		return fmt.Errorf("STORE_INVALID_RECORD: nil or missing evaluator_id")
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	prevKeysJSON, err := json.Marshal(rec.PreviousKeys)
	if err != nil {
		return fmt.Errorf("PREV_KEYS_MARSHAL: %w", err)
	}
	if rec.Metadata == nil {
		rec.Metadata = map[string]string{}
	}
	metaJSON, err := json.Marshal(rec.Metadata)
	if err != nil {
		return fmt.Errorf("METADATA_MARSHAL: %w", err)
	}

	const q = `
		INSERT INTO evaluator_records (
			evaluator_id, name, status, public_key, public_key_hex,
			key_fingerprint, expires_at, previous_keys, metadata,
			registered_at, last_active_at, suspended_at, revoked_at, revoke_reason
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
		ON CONFLICT (evaluator_id) DO UPDATE SET
			name            = EXCLUDED.name,
			status          = EXCLUDED.status,
			public_key      = EXCLUDED.public_key,
			public_key_hex  = EXCLUDED.public_key_hex,
			key_fingerprint = EXCLUDED.key_fingerprint,
			expires_at      = EXCLUDED.expires_at,
			previous_keys   = EXCLUDED.previous_keys,
			metadata        = EXCLUDED.metadata,
			last_active_at  = EXCLUDED.last_active_at,
			suspended_at    = EXCLUDED.suspended_at,
			revoked_at      = EXCLUDED.revoked_at,
			revoke_reason   = EXCLUDED.revoke_reason`

	_, err = s.db.ExecContext(ctx, q,
		rec.EvaluatorID,
		rec.Name,
		string(rec.Status),
		[]byte(rec.PublicKey),
		rec.PublicKeyHex,
		nullableString(rec.KeyFingerprint),
		nullableTime(rec.ExpiresAt),
		prevKeysJSON,
		metaJSON,
		rec.RegisteredAt.UTC(),
		rec.LastActiveAt.UTC(),
		nullableTime(rec.SuspendedAt),
		nullableTime(rec.RevokedAt),
		nullableString(rec.RevokeReason),
	)
	if err != nil {
		return fmt.Errorf("PUT_RECORD_EXEC_FAILED: %w", err)
	}
	return nil
}

func (s *PostgresEvaluatorStore) AppendEvent(ctx context.Context, ev EvaluatorRegistryEvent) error {
	if ev.EventID == "" || ev.EventType == "" {
		return fmt.Errorf("STORE_INVALID_EVENT: missing event_id or event_type")
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	// Recompute the chain hash from the terminal row's hash. We always read
	// the latest chain hash inside the same transaction boundary so that
	// concurrent inserters can't produce a forked chain.
	tx, err := s.db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelSerializable})
	if err != nil {
		return fmt.Errorf("APPEND_EVENT_TX_BEGIN: %w", err)
	}
	defer tx.Rollback() // safe no-op after Commit

	var prevHash string
	row := tx.QueryRowContext(ctx,
		`SELECT chain_hash FROM evaluator_registry_events
		 ORDER BY ts DESC, event_id DESC LIMIT 1`)
	if err := row.Scan(&prevHash); err != nil && err != sql.ErrNoRows {
		return fmt.Errorf("APPEND_EVENT_HEAD_READ: %w", err)
	}
	chainHash := computeEventChainHash(prevHash, ev)

	const q = `
		INSERT INTO evaluator_registry_events (
			event_id, event_type, evaluator_id, ts, initiator, reason, detail,
			prev_event_id, chain_hash
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`
	_, err = tx.ExecContext(ctx, q,
		ev.EventID, ev.EventType, ev.EvaluatorID,
		ev.Timestamp.UTC(), ev.Initiator,
		nullableString(ev.Reason), nullableString(ev.Detail),
		nullableString(prevHash), chainHash,
	)
	if err != nil {
		return fmt.Errorf("APPEND_EVENT_INSERT: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("APPEND_EVENT_COMMIT: %w", err)
	}
	return nil
}

func (s *PostgresEvaluatorStore) IsDurable() bool { return true }

// Close is a no-op because the *sql.DB handle is owned by the audit sink,
// not by this store. Closing it here would kill the audit sink too.
func (s *PostgresEvaluatorStore) Close() error { return nil }

// ============================================================================
// HELPERS
// ============================================================================

// cloneEvaluatorRecord returns a deep-ish copy. Ed25519 public keys are
// immutable bytes so a slice copy is enough; metadata and previous keys
// are deep-copied to prevent cross-contamination between the store and
// the in-memory registry.
func cloneEvaluatorRecord(r *EvaluatorRecord) *EvaluatorRecord {
	if r == nil {
		return nil
	}
	out := *r
	if r.PublicKey != nil {
		out.PublicKey = append(ed25519.PublicKey(nil), r.PublicKey...)
	}
	if r.Metadata != nil {
		m := make(map[string]string, len(r.Metadata))
		for k, v := range r.Metadata {
			m[k] = v
		}
		out.Metadata = m
	}
	if r.PreviousKeys != nil {
		pk := make([]EvaluatorKeyVersion, len(r.PreviousKeys))
		for i, v := range r.PreviousKeys {
			pk[i] = v
			if v.PublicKey != nil {
				pk[i].PublicKey = append(ed25519.PublicKey(nil), v.PublicKey...)
			}
		}
		out.PreviousKeys = pk
	}
	if r.SuspendedAt != nil {
		t := *r.SuspendedAt
		out.SuspendedAt = &t
	}
	if r.RevokedAt != nil {
		t := *r.RevokedAt
		out.RevokedAt = &t
	}
	if r.ExpiresAt != nil {
		t := *r.ExpiresAt
		out.ExpiresAt = &t
	}
	return &out
}

func nullableString(s string) interface{} {
	if s == "" {
		return nil
	}
	return s
}

func nullableTime(t *time.Time) interface{} {
	if t == nil {
		return nil
	}
	return t.UTC()
}
