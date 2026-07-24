package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"sync"
)

// ================================================================
// POLICY REGISTRY — Versioned, Immutable Policy Management
// ================================================================
//
// The PolicyRegistry manages multiple frozen policy versions.
// Each version is hash-verified on load and immutable at runtime.
// The registry enforces:
//   - No silent mutation (SHA-256 hash verification)
//   - Version isolation (separate PolicyStore per version)
//   - Single active policy (explicit designation via config)
//   - Historical access (any loaded version retrievable for replay)
//   - Config-driven activation (deterministic, not hardcoded)

// PolicyLifecycle represents the lifecycle state of a policy version.
type PolicyLifecycle string

const (
	PolicyFrozen     PolicyLifecycle = "FROZEN"
	PolicyActive     PolicyLifecycle = "ACTIVE"
	PolicyDeprecated PolicyLifecycle = "DEPRECATED"
)

// PolicyEntry wraps a PolicyStore with lifecycle metadata.
type PolicyEntry struct {
	Store     *PolicyStore
	Lifecycle PolicyLifecycle
}

// RegistryConfig defines the deterministic configuration for active policy selection.
// Loaded from registry_config.json — no hardcoded version strings.
type RegistryConfig struct {
	ActiveVersion string `json:"active_version"`
	PoliciesDir   string `json:"policies_dir"`
	Description   string `json:"description"`
}

// PolicyRegistry manages multiple versioned, immutable policy stores.
// Thread-safe for concurrent reads. Write operations (Load, SetActive)
// are serialized via mutex.
type PolicyRegistry struct {
	mu            sync.RWMutex
	policiesDir   string
	versions      map[string]*PolicyEntry
	activeVersion string
	config        *RegistryConfig // nil if no config loaded
}

// NewPolicyRegistry creates an empty registry pointed at a policies directory.
// No policies are loaded until LoadPolicy() is called explicitly.
func NewPolicyRegistry(policiesDir string) *PolicyRegistry {
	return &PolicyRegistry{
		policiesDir: policiesDir,
		versions:    make(map[string]*PolicyEntry),
	}
}

// NewPolicyRegistryFromConfig creates a registry from a configuration file.
// The config file specifies the policies directory and which version should be active.
// This is the RECOMMENDED production constructor — it ensures deterministic,
// config-driven active policy selection instead of hardcoded version strings.
//
// Config file format (registry_config.json):
//
//	{
//	  "active_version": "v1",
//	  "policies_dir": "./policies",
//	  "description": "Production policy registry configuration"
//	}
func NewPolicyRegistryFromConfig(configPath string) (*PolicyRegistry, error) {
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("cannot read registry config: %w", err)
	}

	var config RegistryConfig
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("cannot parse registry config: %w", err)
	}

	if config.ActiveVersion == "" {
		return nil, fmt.Errorf("registry config missing required field: active_version")
	}
	if config.PoliciesDir == "" {
		return nil, fmt.Errorf("registry config missing required field: policies_dir")
	}

	pr := &PolicyRegistry{
		policiesDir: config.PoliciesDir,
		versions:    make(map[string]*PolicyEntry),
		config:      &config,
	}

	fmt.Printf("[PolicyRegistry] Loaded config: active_version=%s, policies_dir=%s\n",
		config.ActiveVersion, config.PoliciesDir)

	return pr, nil
}

// InitializeFromConfig loads all policies and activates the config-specified version.
// This is the complete initialization path for production use:
//   1. Scan policies directory → load all policy_*.json files
//   2. Verify all hashes
//   3. Activate the version specified in registry_config.json
//
// Returns error if:
//   - No config was loaded (use NewPolicyRegistryFromConfig first)
//   - Config-specified version is not found in policies directory
//   - Any policy fails hash verification
func (pr *PolicyRegistry) InitializeFromConfig() (int, error) {
	if pr.config == nil {
		return 0, fmt.Errorf("no config loaded — use NewPolicyRegistryFromConfig()")
	}

	loaded, err := pr.LoadAllPolicies()
	if err != nil {
		return loaded, err
	}

	if err := pr.VerifyAllPolicies(); err != nil {
		return loaded, err
	}

	if err := pr.SetActivePolicy(pr.config.ActiveVersion); err != nil {
		return loaded, fmt.Errorf("config specifies active_version=%q but: %w",
			pr.config.ActiveVersion, err)
	}

	return loaded, nil
}

// LoadPolicy loads a policy file from the policies directory, verifies its
// hash integrity, and stores it in the registry as FROZEN.
//
// File naming convention: policy_{version}.json
// Example: LoadPolicy("v1") loads policies/policy_v1.json
//
// Returns error if:
//   - File does not exist or cannot be read
//   - Hash verification fails (policy_hash mismatch)
//   - Version is already loaded (duplicate prevention)
//   - Policy has empty policy_hash (DRAFT state, not loadable)
func (pr *PolicyRegistry) LoadPolicy(version string) error {
	pr.mu.Lock()
	defer pr.mu.Unlock()

	// Reject duplicate loads — version identifiers must be unique (PL-07)
	if _, exists := pr.versions[version]; exists {
		return fmt.Errorf("policy version %q already loaded", version)
	}

	// Construct path: policies/policy_v1.json
	filename := fmt.Sprintf("policy_%s.json", version)
	path := filepath.Join(pr.policiesDir, filename)

	// Load and verify via existing PolicyStore (hash verification built in)
	store, err := NewPolicyStore(path)
	if err != nil {
		return fmt.Errorf("failed to load policy %s: %w", version, err)
	}

	// Reject DRAFT policies — empty hash means not frozen (PL-01)
	if store.GetPolicyHash() == "" {
		return fmt.Errorf("policy %s has empty policy_hash (DRAFT state, cannot load)", version)
	}

	// Verify version string matches the file's declared policy_version
	if store.GetPolicyVersion() != "" && store.GetPolicyVersion() != version {
		// Allow version mapping: file declares "1.0.0", loaded as "v1"
		// We store under the requested version key but log the mapping
		fmt.Printf("[PolicyRegistry] Version mapping: requested=%q, file declares=%q\n",
			version, store.GetPolicyVersion())
	}

	pr.versions[version] = &PolicyEntry{
		Store:     store,
		Lifecycle: PolicyFrozen,
	}

	fmt.Printf("[PolicyRegistry] Loaded policy %s (hash=%s..., rules=%d, lifecycle=FROZEN)\n",
		version, store.GetPolicyHash()[:16], store.RuleCount())

	return nil
}

// GetActivePolicy returns the PolicyStore designated as active.
// Used by PDP for live evaluations.
// Returns nil if no active policy is set.
func (pr *PolicyRegistry) GetActivePolicy() *PolicyStore {
	pr.mu.RLock()
	defer pr.mu.RUnlock()

	if pr.activeVersion == "" {
		return nil
	}
	entry, exists := pr.versions[pr.activeVersion]
	if !exists {
		return nil
	}
	return entry.Store
}

// GetActivePolicyVersion returns the version string of the active policy.
func (pr *PolicyRegistry) GetActivePolicyVersion() string {
	pr.mu.RLock()
	defer pr.mu.RUnlock()
	return pr.activeVersion
}

// GetPolicy returns a specific policy version's PolicyStore.
// Used by replay harness for historical evaluation.
// Returns nil if version is not loaded.
func (pr *PolicyRegistry) GetPolicy(version string) *PolicyStore {
	pr.mu.RLock()
	defer pr.mu.RUnlock()

	entry, exists := pr.versions[version]
	if !exists {
		return nil
	}
	return entry.Store
}

// SetActivePolicy designates a loaded policy version as ACTIVE.
// The previous active policy (if any) transitions to DEPRECATED.
// Target version must already be loaded and verified (PL-03).
func (pr *PolicyRegistry) SetActivePolicy(version string) error {
	pr.mu.Lock()
	defer pr.mu.Unlock()

	entry, exists := pr.versions[version]
	if !exists {
		return fmt.Errorf("policy version %q not loaded, cannot activate", version)
	}

	// Transition previous active policy to DEPRECATED
	if pr.activeVersion != "" && pr.activeVersion != version {
		if prevEntry, ok := pr.versions[pr.activeVersion]; ok {
			prevEntry.Lifecycle = PolicyDeprecated
			fmt.Printf("[PolicyRegistry] Policy %s transitioned: ACTIVE -> DEPRECATED\n",
				pr.activeVersion)
		}
	}

	// Activate the new version
	entry.Lifecycle = PolicyActive
	pr.activeVersion = version

	fmt.Printf("[PolicyRegistry] Policy %s is now ACTIVE (hash=%s...)\n",
		version, entry.Store.GetPolicyHash()[:16])

	return nil
}

// ListPolicyVersions returns all loaded policy version identifiers,
// sorted lexicographically for deterministic output.
func (pr *PolicyRegistry) ListPolicyVersions() []string {
	pr.mu.RLock()
	defer pr.mu.RUnlock()

	versions := make([]string, 0, len(pr.versions))
	for v := range pr.versions {
		versions = append(versions, v)
	}
	sort.Strings(versions)
	return versions
}

// GetPolicyLifecycle returns the lifecycle state of a specific policy version.
func (pr *PolicyRegistry) GetPolicyLifecycle(version string) (PolicyLifecycle, error) {
	pr.mu.RLock()
	defer pr.mu.RUnlock()

	entry, exists := pr.versions[version]
	if !exists {
		return "", fmt.Errorf("policy version %q not loaded", version)
	}
	return entry.Lifecycle, nil
}

// VerifyAllPolicies recomputes hashes for all loaded policies and validates integrity.
// Returns error on first integrity violation detected.
// This is the explicit per-version hash validation proof — each version is
// independently recomputed and compared.
func (pr *PolicyRegistry) VerifyAllPolicies() error {
	pr.mu.RLock()
	defer pr.mu.RUnlock()

	for version, entry := range pr.versions {
		// Recompute the hash using the same canonical method as PolicyStore
		rules := entry.Store.Rules() // defensive copy via accessor
		recomputedHash := computePolicyHash(rules)
		if recomputedHash != entry.Store.GetPolicyHash() {
			return fmt.Errorf(
				"POLICY INTEGRITY VIOLATION: version=%s stored_hash=%s recomputed_hash=%s",
				version, entry.Store.GetPolicyHash(), recomputedHash)
		}
	}
	return nil
}

// VerifyPolicyVersion recomputes the hash for a single policy version.
// Returns the stored hash, recomputed hash, and whether they match.
// Used for explicit per-version hash validation proof in test output.
func (pr *PolicyRegistry) VerifyPolicyVersion(version string) (storedHash string, recomputedHash string, match bool, err error) {
	pr.mu.RLock()
	defer pr.mu.RUnlock()

	entry, exists := pr.versions[version]
	if !exists {
		return "", "", false, fmt.Errorf("policy version %q not loaded", version)
	}

	rules := entry.Store.Rules()
	recomputed := computePolicyHash(rules)
	stored := entry.Store.GetPolicyHash()
	return stored, recomputed, stored == recomputed, nil
}

// computePolicyHash computes SHA-256 from canonical rules JSON.
// Delegates to the shared computePolicyHashFromRules in policy_store.go (GAP-11).
func computePolicyHash(rules []AuthorityRule) string {
	// Sort by RuleID for canonical ordering
	sorted := make([]AuthorityRule, len(rules))
	copy(sorted, rules)
	sort.SliceStable(sorted, func(i, j int) bool {
		return sorted[i].RuleID < sorted[j].RuleID
	})

	hash, err := computePolicyHashFromRules(sorted)
	if err != nil {
		// Fail-closed: return error indicator instead of empty string
		return fmt.Sprintf("HASH_ERROR:%v", err)
	}
	return hash
}

// PrintRegistryStatus outputs a summary of all loaded policies and their states.
func (pr *PolicyRegistry) PrintRegistryStatus() {
	pr.mu.RLock()
	defer pr.mu.RUnlock()

	fmt.Println("\n+-------------------------------------------------------+")
	fmt.Println("|  SARATHI POLICY REGISTRY STATUS                        |")
	fmt.Println("+-------------------------------------------------------+")
	fmt.Printf("  Policies Directory: %s\n", pr.policiesDir)
	fmt.Printf("  Loaded Versions:    %d\n", len(pr.versions))
	fmt.Printf("  Active Version:     %s\n", pr.activeVersion)
	if pr.config != nil {
		fmt.Printf("  Config Source:      registry_config.json\n")
		fmt.Printf("  Config Active:      %s\n", pr.config.ActiveVersion)
	}
	fmt.Println()

	versions := make([]string, 0, len(pr.versions))
	for v := range pr.versions {
		versions = append(versions, v)
	}
	sort.Strings(versions)

	for _, v := range versions {
		entry := pr.versions[v]
		fmt.Printf("  [%s] version=%s hash=%s... rules=%d\n",
			entry.Lifecycle, v, entry.Store.GetPolicyHash()[:16], entry.Store.RuleCount())
	}
	fmt.Println()
}

// LoadAllPolicies scans the policies directory and loads all policy_*.json files.
// Returns the number of policies loaded and any errors encountered.
func (pr *PolicyRegistry) LoadAllPolicies() (int, error) {
	pattern := filepath.Join(pr.policiesDir, "policy_*.json")
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return 0, fmt.Errorf("failed to scan policies directory: %w", err)
	}

	loaded := 0
	for _, match := range matches {
		base := filepath.Base(match)
		// Extract version from "policy_v1.json" -> "v1"
		version := base[len("policy_"):]
		version = version[:len(version)-len(".json")]

		if err := pr.LoadPolicy(version); err != nil {
			fmt.Fprintf(os.Stderr, "[PolicyRegistry] WARNING: skipping %s: %v\n", base, err)
			continue
		}
		loaded++
	}

	return loaded, nil
}
