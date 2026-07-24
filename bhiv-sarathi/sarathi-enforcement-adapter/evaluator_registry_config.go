package main

// ═══════════════════════════════════════════════════════════════════
// FROZEN — v12.1 GAP-01 RECTIFICATION
// ═══════════════════════════════════════════════════════════════════
// This file is FROZEN: config loading + bootstrap hydration for the
// lifecycle registry is a trust-service concern. The default Sarathi
// bootstrap uses BootstrapTrustConsumer from trust_consumer.go instead
// of BootstrapEvaluatorRegistry defined here. Compiles but is NOT
// WIRED into the default bootstrap path. See KB_06 GAP 1.
// ═══════════════════════════════════════════════════════════════════

// evaluator_registry_config.go — Config loader + bootstrap hydration for
// the Evaluator Trust Registry.
//
// Author: Hemanth B (Phase 12 — External Evaluator Hardening)
// System: Sarathi Governance Kernel — Zero-Trust Verification Boundary
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   The v11 registry was configurable only via Go code. This file gives
//   operators a JSON config file (matching the policy_registry pattern in
//   registry_config.json) that picks the persistence backend, declares
//   bootstrap evaluators, and stamps registry-wide policies (default key
//   crypto period, grace period, metadata allow-list).
//
// PRODUCTION INVARIANTS:
//   - require_durable_store=true is mandatory in production. The boot
//     helper refuses to start if the chosen store reports IsDurable=false.
//   - Bootstrap entries are idempotent. Re-running boot with the same
//     config yields no duplicate records and no errors.
//   - Bootstrap fingerprints MUST match the persisted record. A mismatch
//     means someone swapped a key in the config file post-write — boot
//     fails with FATAL.
//
// DESIGN REFERENCES:
//   - OPA Bundle Service (config-driven trust set)
//   - SPIRE server.conf entries (declarative workload registration)
//   - HashiCorp Vault storage stanza (declarative backend selection)

import (
	"context"
	"crypto/ed25519"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"
)

// EvaluatorRegistryConfig is the JSON shape loaded from
// evaluator_registry_config.json. The schema mirrors registry_config.json
// in spirit so operators familiar with the policy registry config feel
// at home.
type EvaluatorRegistryConfig struct {
	StoreType            string                       `json:"store_type"`             // "memory" | "file" | "postgres"
	StorePath            string                       `json:"store_path,omitempty"`   // file mode only
	RequireDurableStore  bool                         `json:"require_durable_store"`  // production must be true
	DefaultKeyTTLDays    int                          `json:"default_key_ttl_days"`   // M1 — applied to bootstrap entries lacking ExpiresAt
	GracePeriodHours     int                          `json:"grace_period_hours"`     // default rotation grace
	AdminKeysEnvPrefix   string                       `json:"admin_keys_env_prefix"`  // e.g., SARATHI_EVAL_ADMIN_KEY_
	MetadataAllowList    []string                     `json:"metadata_allow_list,omitempty"`
	BootstrapEvaluators  []BootstrapEvaluatorEntry    `json:"bootstrap_evaluators"`
	Description          string                       `json:"description,omitempty"`
}

// BootstrapEvaluatorEntry is a single declaratively-registered evaluator.
// Bootstrap entries skip the PoP flow because they were chosen by the
// operator at deploy time — the operator is implicitly trusted to vouch
// for the public key. (For runtime registration, PoP is mandatory.)
type BootstrapEvaluatorEntry struct {
	EvaluatorID  string            `json:"evaluator_id"`
	Name         string            `json:"name"`
	PublicKeyHex string            `json:"public_key_hex"`
	Metadata     map[string]string `json:"metadata,omitempty"`
	ExpiresAt    *time.Time        `json:"expires_at,omitempty"`
}

// LoadEvaluatorRegistryConfig reads and validates a JSON config file.
// Mirrors policy_registry.NewPolicyRegistryFromConfig in shape.
func LoadEvaluatorRegistryConfig(path string) (*EvaluatorRegistryConfig, error) {
	if path == "" {
		return nil, fmt.Errorf("EVAL_REGISTRY_CONFIG_PATH_EMPTY")
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("EVAL_REGISTRY_CONFIG_READ: %w", err)
	}
	cfg := &EvaluatorRegistryConfig{}
	if err := json.Unmarshal(data, cfg); err != nil {
		return nil, fmt.Errorf("EVAL_REGISTRY_CONFIG_PARSE: %w", err)
	}
	if err := cfg.Validate(); err != nil {
		return nil, err
	}
	return cfg, nil
}

// Validate checks required fields and reasonable bounds.
func (c *EvaluatorRegistryConfig) Validate() error {
	st := strings.ToLower(strings.TrimSpace(c.StoreType))
	switch st {
	case "memory", "file", "postgres":
		c.StoreType = st
	default:
		return fmt.Errorf("EVAL_REGISTRY_CONFIG_INVALID_STORE_TYPE: %q (allowed: memory|file|postgres)", c.StoreType)
	}
	if c.StoreType == "file" && strings.TrimSpace(c.StorePath) == "" {
		return fmt.Errorf("EVAL_REGISTRY_CONFIG_FILE_PATH_REQUIRED")
	}
	if c.DefaultKeyTTLDays < 0 {
		return fmt.Errorf("EVAL_REGISTRY_CONFIG_NEGATIVE_KEY_TTL")
	}
	if c.GracePeriodHours < 0 {
		return fmt.Errorf("EVAL_REGISTRY_CONFIG_NEGATIVE_GRACE")
	}
	if c.AdminKeysEnvPrefix == "" {
		c.AdminKeysEnvPrefix = "SARATHI_EVAL_ADMIN_KEY_"
	}
	for i, e := range c.BootstrapEvaluators {
		if e.EvaluatorID == "" {
			return fmt.Errorf("EVAL_REGISTRY_CONFIG_BOOTSTRAP[%d]_MISSING_ID", i)
		}
		if e.PublicKeyHex == "" {
			return fmt.Errorf("EVAL_REGISTRY_CONFIG_BOOTSTRAP[%d]_MISSING_KEY: %s", i, e.EvaluatorID)
		}
		raw, err := hex.DecodeString(e.PublicKeyHex)
		if err != nil || len(raw) != ed25519.PublicKeySize {
			return fmt.Errorf("EVAL_REGISTRY_CONFIG_BOOTSTRAP[%d]_BAD_KEY: %s (len=%d, err=%v)",
				i, e.EvaluatorID, len(raw), err)
		}
	}
	return nil
}

// BuildStore constructs the configured store implementation. For postgres,
// it borrows the *sql.DB handle from the caller (the audit sink owns the
// pool — we don't open a second one).
func (c *EvaluatorRegistryConfig) BuildStore(db *sql.DB) (EvaluatorRegistryStore, error) {
	switch c.StoreType {
	case "memory":
		return NewInMemoryEvaluatorStore(), nil
	case "file":
		return NewFileEvaluatorStore(c.StorePath)
	case "postgres":
		if db == nil {
			return nil, fmt.Errorf("EVAL_REGISTRY_CONFIG_PG_NIL_DB: postgres store requires a database handle")
		}
		return NewPostgresEvaluatorStore(db)
	default:
		return nil, fmt.Errorf("EVAL_REGISTRY_CONFIG_INVALID_STORE_TYPE: %q", c.StoreType)
	}
}

// LoadAdminKeysFromEnv returns the env-loaded admin_id → hex map. The env
// var format is `<prefix><ADMIN_NAME>=<hex_pubkey>`. Admin name is the
// portion after the prefix, lowercased.
func (c *EvaluatorRegistryConfig) LoadAdminKeysFromEnv() map[string]string {
	prefix := c.AdminKeysEnvPrefix
	if prefix == "" {
		prefix = "SARATHI_EVAL_ADMIN_KEY_"
	}
	out := make(map[string]string)
	for _, kv := range os.Environ() {
		eq := strings.IndexByte(kv, '=')
		if eq < 0 {
			continue
		}
		k, v := kv[:eq], kv[eq+1:]
		if !strings.HasPrefix(k, prefix) {
			continue
		}
		name := strings.ToLower(strings.TrimPrefix(k, prefix))
		if name == "" || v == "" {
			continue
		}
		out[name] = v
	}
	return out
}

// ApplyBootstrapEntries idempotently registers every bootstrap evaluator
// into the (already-hydrated) registry. Existing records with matching
// fingerprints are left untouched; mismatches are surfaced as fatal.
func (c *EvaluatorRegistryConfig) ApplyBootstrapEntries(
	ctx context.Context, registry *EvaluatorTrustRegistry,
) error {
	if registry == nil {
		return fmt.Errorf("EVAL_BOOTSTRAP_NIL_REGISTRY")
	}
	if len(c.MetadataAllowList) > 0 {
		registry.SetMetadataAllowList(c.MetadataAllowList)
	}
	defaultExpiry := func() *time.Time {
		if c.DefaultKeyTTLDays <= 0 {
			return nil
		}
		t := time.Now().UTC().Add(time.Duration(c.DefaultKeyTTLDays) * 24 * time.Hour)
		return &t
	}

	for _, entry := range c.BootstrapEvaluators {
		raw, err := hex.DecodeString(entry.PublicKeyHex)
		if err != nil || len(raw) != ed25519.PublicKeySize {
			return fmt.Errorf("EVAL_BOOTSTRAP_BAD_KEY: %s", entry.EvaluatorID)
		}
		pub := ed25519.PublicKey(raw)
		fp := ComputeKeyFingerprint(pub)

		existing, found := registry.GetEvaluator(entry.EvaluatorID)
		if found {
			if existing.KeyFingerprint != "" && existing.KeyFingerprint != fp {
				return fmt.Errorf(
					"EVAL_BOOTSTRAP_FINGERPRINT_MISMATCH: %s stored=%s config=%s — refuse to silently rebind key",
					entry.EvaluatorID, existing.KeyFingerprint, fp,
				)
			}
			// Idempotent skip — already present and matches.
			continue
		}

		expires := entry.ExpiresAt
		if expires == nil {
			expires = defaultExpiry()
		}
		// Use the v11 register method directly (operator-vouched, no PoP).
		if err := registry.RegisterEvaluator(
			entry.EvaluatorID, entry.Name, pub, entry.Metadata, "config-bootstrap",
		); err != nil {
			return fmt.Errorf("EVAL_BOOTSTRAP_REGISTER_FAILED: %s: %w", entry.EvaluatorID, err)
		}
		// Stamp Phase 12 fields and persist via the same persistAndChain path.
		registry.mu.Lock()
		rec := registry.evaluators[entry.EvaluatorID]
		rec.KeyFingerprint = fp
		rec.ExpiresAt = expires
		registry.bumpVersionLocked()
		registry.mu.Unlock()

		if err := registry.persistAndChain(
			ctx, rec, "REGISTER", "config-bootstrap",
			fmt.Sprintf("declarative bootstrap; fingerprint=%s", fp),
		); err != nil {
			return fmt.Errorf("EVAL_BOOTSTRAP_PERSIST_FAILED: %s: %w", entry.EvaluatorID, err)
		}
	}
	return nil
}

// BootstrapEvaluatorRegistry is the single entry point invoked from
// enforcement_adapter_main.go during startup. It is gated behind the
// SARATHI_EVALUATOR_REGISTRY_CONFIG env var so legacy deployments
// continue to run unchanged.
func BootstrapEvaluatorRegistry(
	ctx context.Context,
	adapter *EnforcementAdapter,
	postgresDB *sql.DB,
) error {
	cfgPath := os.Getenv("SARATHI_EVALUATOR_REGISTRY_CONFIG")
	if cfgPath == "" {
		// Legacy path: in-memory, empty registry, matches v11 behaviour.
		return nil
	}
	cfg, err := LoadEvaluatorRegistryConfig(cfgPath)
	if err != nil {
		return err
	}

	store, err := cfg.BuildStore(postgresDB)
	if err != nil {
		return err
	}
	if cfg.RequireDurableStore && !store.IsDurable() {
		return fmt.Errorf("FATAL: require_durable_store=true but store_type=%s is not durable", cfg.StoreType)
	}

	registry := adapter.GetEvaluatorRegistry()
	if registry == nil {
		adapter.InitExternalMode()
		registry = adapter.GetEvaluatorRegistry()
	}
	registry.SetStore(store)
	registry.SetAdminAuth(NewEvaluatorAdminAuthenticator(cfg.LoadAdminKeysFromEnv()))

	if err := registry.HydrateFromStore(ctx); err != nil {
		return fmt.Errorf("evaluator registry hydration failed: %w", err)
	}
	if err := cfg.ApplyBootstrapEntries(ctx, registry); err != nil {
		return fmt.Errorf("bootstrap entries failed: %w", err)
	}

	fmt.Printf("[Phase12] Evaluator registry bootstrap complete: store=%s durable=%v evaluators=%d admins=%d version=%d\n",
		cfg.StoreType, store.IsDurable(),
		registry.EvaluatorCount(),
		registry.AdminCountSafe(),
		registry.Version(),
	)
	return nil
}

// AdminCountSafe returns the number of admin keys wired to the registry,
// or 0 if no authenticator is set. Helper to avoid nil-deref in boot logs.
func (r *EvaluatorTrustRegistry) AdminCountSafe() int {
	r.mu.RLock()
	defer r.mu.RUnlock()
	if r.adminAuth == nil {
		return 0
	}
	return r.adminAuth.AdminCount()
}
