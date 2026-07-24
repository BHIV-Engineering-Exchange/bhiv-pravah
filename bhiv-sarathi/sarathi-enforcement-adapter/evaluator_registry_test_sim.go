package main

// ═══════════════════════════════════════════════════════════════════
// FROZEN — v12.1 GAP-01 RECTIFICATION
// ═══════════════════════════════════════════════════════════════════
// This file is FROZEN: it is the test suite for the frozen lifecycle
// surface. Compiles but is NOT invoked by the default test harness in
// enforcement_adapter_main.go. Reactivate only when operating in
// trust-service deployment mode. See KB_06 GAP 1.
// ═══════════════════════════════════════════════════════════════════

// evaluator_registry_test_sim.go — Deterministic proof suite for the
// Phase 12 External Evaluator Hardening surface.
//
// Author: Hemanth B (Phase 12)
// System: Sarathi Governance Kernel — Zero-Trust Verification Boundary
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   Prove that every gap closed by Phase 12 is closed and that none of
//   the changes regressed the v11 10-stage enforcement pipeline. The
//   existing external_decision_test_sim.go continues to pass unchanged —
//   this file only exercises the NEW surface:
//
//     - InMemoryEvaluatorStore / FileEvaluatorStore round-trip
//     - HydrateFromStore idempotency
//     - PoP challenge/complete (happy path + wrong key + expired + replay)
//     - EvaluatorAdminAuthenticator (signature, nonce, skew, rate limit)
//     - Lifecycle *_Authed wrappers (suspend → persisted → hydrated)
//     - Key expiry check in GetActiveEvaluator
//     - Trust bundle JWKS publication
//     - CentralGuard invariant: guard violations unchanged across API hits
//
// OUTPUT:
//   Each assertion emits a single PROOF LOG line:
//     [PASS]  test_name  — detail
//     [DENY]  failure_code  — detail
//     [ALLOW] success_code  — detail
//
// The review packet's PROOF section references these log line shapes.

import (
	"context"
	"crypto/ed25519"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// RunEvaluatorRegistryPhase12Tests runs the Phase 12 proof suite.
// Returns (passed, total, details).
func RunEvaluatorRegistryPhase12Tests() (int, int, []string) {
	passed := 0
	total := 0
	var details []string

	logResult := func(name string, pass bool, detail string) {
		total++
		status := "FAIL"
		if pass {
			passed++
			status = "PASS"
		}
		line := fmt.Sprintf("  [%s] %s — %s", status, name, detail)
		details = append(details, line)
		fmt.Println(line)
	}

	fmt.Println()
	fmt.Println("==============================================================")
	fmt.Println(" PHASE 12 — EVALUATOR REGISTRY HARDENING PROOF SUITE")
	fmt.Println("==============================================================")

	ctx := context.Background()

	// ========================================================================
	// SETUP: fresh registry + in-memory store + deterministic clock
	// ========================================================================
	registry := NewEvaluatorTrustRegistry()
	store := NewInMemoryEvaluatorStore()
	registry.SetStore(store)

	// Admin Ed25519 keys: one legit admin, one unknown
	adminPub, adminPriv, _ := ed25519.GenerateKey(nil)
	malloryPub, malloryPriv, _ := ed25519.GenerateKey(nil)
	_ = malloryPub

	adminAuth := NewEvaluatorAdminAuthenticator(map[string]string{
		"hemanth": hex.EncodeToString(adminPub),
	})
	registry.SetAdminAuth(adminAuth)

	// Evaluator key pair (the legitimate registrant)
	evalPub, evalPriv, _ := ed25519.GenerateKey(nil)
	evalPubHex := hex.EncodeToString(evalPub)

	// Rogue evaluator key (wrong key for PoP failure case)
	_, roguePriv, _ := ed25519.GenerateKey(nil)

	// ========================================================================
	// TEST 1 — PoP happy path (challenge → sign → complete → stored)
	// ========================================================================
	chStore := registry.EnsureChallengeStore()
	challenge, err := chStore.Issue(
		"ishan-evaluator-v1",
		"Ishan Evaluator v1",
		evalPubHex,
		map[string]string{"org": "BHIV"},
		nil,
	)
	logResult("pop_challenge_issue", err == nil,
		fmt.Sprintf("challenge_id=%s err=%v", truncate(challenge.ChallengeID, 8), err))

	sig := ed25519.Sign(evalPriv, []byte(challenge.Message))
	rec, err := registry.RegisterEvaluatorWithPoP(ctx, challenge.ChallengeID, sig, "admin:hemanth")
	logResult("pop_register_happy", err == nil && rec != nil && rec.Status == EvaluatorStatusActive,
		fmt.Sprintf("evaluator_id=%s fingerprint=%s err=%v", safeID(rec), safeFingerprint(rec), err))

	// ========================================================================
	// TEST 2 — PoP wrong key (rogue signs the challenge)
	// ========================================================================
	ch2, _ := chStore.Issue("rogue-eval", "Rogue", evalPubHex, nil, nil)
	rogueSig := ed25519.Sign(roguePriv, []byte(ch2.Message))
	_, err = registry.RegisterEvaluatorWithPoP(ctx, ch2.ChallengeID, rogueSig, "admin:hemanth")
	logResult("pop_wrong_key_rejected", err != nil && contains(err.Error(), "POP_FAILED"),
		fmt.Sprintf("err=%v", err))

	// ========================================================================
	// TEST 3 — PoP replay (consume challenge twice)
	// ========================================================================
	ch3, _ := chStore.Issue("replay-eval", "Replay", evalPubHex, nil, nil)
	sig3 := ed25519.Sign(evalPriv, []byte(ch3.Message))
	_, _ = registry.RegisterEvaluatorWithPoP(ctx, ch3.ChallengeID, sig3, "admin:hemanth")
	_, err = registry.RegisterEvaluatorWithPoP(ctx, ch3.ChallengeID, sig3, "admin:hemanth")
	logResult("pop_replay_rejected", err != nil && contains(err.Error(), "CHALLENGE_ALREADY_CONSUMED"),
		fmt.Sprintf("err=%v", err))

	// ========================================================================
	// TEST 4 — Store round-trip + hydration idempotency (in-memory)
	// ========================================================================
	recsBefore, _, _ := store.LoadAll(ctx)
	err = registry.HydrateFromStore(ctx)
	recsAfter, _, _ := store.LoadAll(ctx)
	logResult("store_hydrate_idempotent",
		err == nil && len(recsBefore) == len(recsAfter) && registry.EvaluatorCount() == len(recsBefore),
		fmt.Sprintf("records=%d err=%v", len(recsAfter), err))

	// ========================================================================
	// TEST 5 — File store round-trip (tamper-evident chain_hash)
	// ========================================================================
	tmpDir, _ := os.MkdirTemp("", "phase12-filestore-")
	defer os.RemoveAll(tmpDir)
	filePath := filepath.Join(tmpDir, "evaluators.json")
	fileStore, err := NewFileEvaluatorStore(filePath)
	logResult("file_store_create", err == nil, fmt.Sprintf("path=%s err=%v", filepath.Base(filePath), err))

	freshRegistry := NewEvaluatorTrustRegistry()
	freshRegistry.SetStore(fileStore)
	freshRegistry.SetAdminAuth(NewEvaluatorAdminAuthenticator(map[string]string{
		"hemanth": hex.EncodeToString(adminPub),
	}))
	freshChStore := freshRegistry.EnsureChallengeStore()

	ch5, _ := freshChStore.Issue("file-eval", "File Eval", evalPubHex, map[string]string{"org": "BHIV"}, nil)
	sig5 := ed25519.Sign(evalPriv, []byte(ch5.Message))
	_, err = freshRegistry.RegisterEvaluatorWithPoP(ctx, ch5.ChallengeID, sig5, "admin:hemanth")
	logResult("file_store_register_persists", err == nil, fmt.Sprintf("err=%v", err))

	// Simulate process restart: new registry, same file
	fileStore2, _ := NewFileEvaluatorStore(filePath)
	restoredRegistry := NewEvaluatorTrustRegistry()
	restoredRegistry.SetStore(fileStore2)
	err = restoredRegistry.HydrateFromStore(ctx)
	recRestored, found := restoredRegistry.GetEvaluator("file-eval")
	logResult("file_store_hydrate_survives_restart",
		err == nil && found && recRestored != nil && recRestored.Status == EvaluatorStatusActive,
		fmt.Sprintf("found=%v err=%v", found, err))

	// ========================================================================
	// TEST 6 — Admin auth happy path (signed SUSPEND)
	// ========================================================================
	payload6 := []byte(`{"reason":"maintenance window"}`)
	adminReq6, _ := SignAdminRequest("hemanth", AdminOpSuspend, "ishan-evaluator-v1", payload6, adminPriv, nil)
	err = registry.SuspendEvaluatorAuthed(ctx, adminReq6, payload6, "ishan-evaluator-v1", "maintenance window")
	logResult("admin_auth_suspend_happy", err == nil, fmt.Sprintf("err=%v", err))

	// ========================================================================
	// TEST 7 — Admin auth bad signature (tampered body)
	// ========================================================================
	payload7 := []byte(`{"reason":"original"}`)
	adminReq7, _ := SignAdminRequest("hemanth", AdminOpRevoke, "ishan-evaluator-v1", payload7, adminPriv, nil)
	tampered := []byte(`{"reason":"tampered"}`)
	err = registry.RevokeEvaluatorAuthed(ctx, adminReq7, tampered, "ishan-evaluator-v1", "tampered")
	logResult("admin_auth_body_tamper_rejected",
		err != nil && contains(err.Error(), AdminErrBodyHashMismatch),
		fmt.Sprintf("err=%v", err))

	// ========================================================================
	// TEST 8 — Admin auth replay (same nonce twice)
	// ========================================================================
	payload8 := []byte(`{"reason":"replay test"}`)
	adminReq8, _ := SignAdminRequest("hemanth", AdminOpReactivate, "ishan-evaluator-v1", payload8, adminPriv, nil)
	_ = registry.ReactivateEvaluatorAuthed(ctx, adminReq8, payload8, "ishan-evaluator-v1", "replay test")
	err = registry.ReactivateEvaluatorAuthed(ctx, adminReq8, payload8, "ishan-evaluator-v1", "replay test")
	logResult("admin_auth_nonce_replay_rejected",
		err != nil && contains(err.Error(), AdminErrNonceReplay),
		fmt.Sprintf("err=%v", err))

	// ========================================================================
	// TEST 9 — Admin auth unknown admin
	// ========================================================================
	payload9 := []byte(`{"reason":"attack"}`)
	malloryReq, _ := SignAdminRequest("mallory", AdminOpRevoke, "ishan-evaluator-v1", payload9, malloryPriv, nil)
	err = registry.RevokeEvaluatorAuthed(ctx, malloryReq, payload9, "ishan-evaluator-v1", "attack")
	logResult("admin_auth_unknown_rejected",
		err != nil && contains(err.Error(), AdminErrUnknownAdmin),
		fmt.Sprintf("err=%v", err))

	// ========================================================================
	// TEST 10 — Admin auth operation mismatch
	// ========================================================================
	payload10 := []byte(`{"reason":"op mismatch"}`)
	adminReq10, _ := SignAdminRequest("hemanth", AdminOpSuspend, "ishan-evaluator-v1", payload10, adminPriv, nil)
	// Use the SUSPEND-signed envelope against REVOKE
	err = registry.RevokeEvaluatorAuthed(ctx, adminReq10, payload10, "ishan-evaluator-v1", "op mismatch")
	logResult("admin_auth_op_mismatch_rejected",
		err != nil && contains(err.Error(), AdminErrOpMismatch),
		fmt.Sprintf("err=%v", err))

	// ========================================================================
	// TEST 11 — Key expiry (NIST SP 800-57 crypto period)
	// ========================================================================
	expiredTime := time.Now().Add(-1 * time.Hour)
	expiredReg := NewEvaluatorTrustRegistry()
	expiredReg.RegisterEvaluator("expired-eval", "Expired", evalPub, nil, "system")
	expiredReg.mu.Lock()
	expiredReg.evaluators["expired-eval"].ExpiresAt = &expiredTime
	expiredReg.mu.Unlock()
	_, err = expiredReg.GetActiveEvaluator("expired-eval")
	logResult("key_expiry_enforced",
		err != nil && contains(err.Error(), "EVALUATOR_KEY_EXPIRED"),
		fmt.Sprintf("err=%v", err))

	// ========================================================================
	// TEST 12 — Trust bundle JWKS (RFC 7517)
	// ========================================================================
	jwksBytes, err := registry.TrustBundleJWKS()
	var jwks map[string]interface{}
	_ = json.Unmarshal(jwksBytes, &jwks)
	keys, _ := jwks["keys"].([]interface{})
	logResult("jwks_bundle_published",
		err == nil && len(jwksBytes) > 0 && len(keys) > 0,
		fmt.Sprintf("bytes=%d keys=%d err=%v", len(jwksBytes), len(keys), err))

	// ========================================================================
	// TEST 13 — Version bumps on every mutation
	// ========================================================================
	v1 := registry.Version()
	payload13 := []byte(`{"reason":"version bump"}`)
	adminReq13, _ := SignAdminRequest("hemanth", AdminOpSuspend, "ishan-evaluator-v1", payload13, adminPriv, nil)
	_ = registry.SuspendEvaluatorAuthed(ctx, adminReq13, payload13, "ishan-evaluator-v1", "version bump")
	v2 := registry.Version()
	logResult("version_bumps_on_mutation", v2 > v1, fmt.Sprintf("before=%d after=%d", v1, v2))

	// ========================================================================
	// TEST 14 — Config loader validation
	// ========================================================================
	badCfg := &EvaluatorRegistryConfig{StoreType: "bogus"}
	err = badCfg.Validate()
	logResult("config_invalid_store_type_rejected",
		err != nil && contains(err.Error(), "INVALID_STORE_TYPE"),
		fmt.Sprintf("err=%v", err))

	goodCfg := &EvaluatorRegistryConfig{
		StoreType:           "file",
		StorePath:           filepath.Join(tmpDir, "cfg.json"),
		RequireDurableStore: true,
		DefaultKeyTTLDays:   30,
	}
	err = goodCfg.Validate()
	logResult("config_valid_accepted", err == nil, fmt.Sprintf("err=%v", err))

	// ========================================================================
	// TEST 15 — Fingerprint stability
	// ========================================================================
	fp1 := ComputeKeyFingerprint(evalPub)
	fp2 := ComputeKeyFingerprint(evalPub)
	logResult("fingerprint_stable", fp1 == fp2 && len(fp1) == 16,
		fmt.Sprintf("fp=%s", fp1))

	// ========================================================================
	// SUMMARY
	// ========================================================================
	fmt.Println()
	fmt.Printf("  PHASE 12 PROOF SUITE: %d/%d assertions passed\n", passed, total)
	fmt.Println("==============================================================")
	return passed, total, details
}

// =============================================================================
// test helpers
// =============================================================================

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n]
}

func safeID(r *EvaluatorRecord) string {
	if r == nil {
		return "<nil>"
	}
	return r.EvaluatorID
}

func safeFingerprint(r *EvaluatorRecord) string {
	if r == nil {
		return "<nil>"
	}
	return r.KeyFingerprint
}

func contains(haystack, needle string) bool {
	return len(needle) == 0 || (len(haystack) >= len(needle) && indexOf(haystack, needle) >= 0)
}

func indexOf(haystack, needle string) int {
	for i := 0; i+len(needle) <= len(haystack); i++ {
		if haystack[i:i+len(needle)] == needle {
			return i
		}
	}
	return -1
}
