// v14_6_cli.go (v14.6 Global Determinism Validation — CLI dispatch)
//
// Top-of-main entry points for all v14.6 sub-commands. Parsing is kept
// intentionally tiny: a single pass over os.Args collects the chosen mode
// plus any trailing integer. Unknown flags return (mode="", ok=false) so
// the legacy main continues to dispatch.
//
// Supported flags:
//
//   --multi-node [N]         Phase 1 + 2 together (N default 3)
//   --clock-drift            Phase 2
//   --transport-adversarial  Phase 3
//   --bucket-verify [N]      Phase 4 (N default 100)
//   --cross-system-validate  Phase 6
//   --high-iteration-replay [N]
//                            Phase 5 (N default 1000)
//   --vc-demo                Phase 7
//   --v14-6-audit            Audit pass only
//   --v14-6                  Run every phase in sequence + audit
//   --multi-node-child       Internal: invoked by parent; per-node replay
//
// TAG: test-affordance-only

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"time"
)

// V14_6Mode is the parsed CLI action.
type V14_6Mode struct {
	Name string
	N    int  // positional count, when applicable
	Ok   bool // a v14.6 flag was matched
}

// ParseV14_6Args inspects argv for any v14.6 flag and returns the parsed mode.
// The caller (enforcement_adapter_main.go) routes to RunV14_6CLI when Ok==true.
func ParseV14_6Args(argv []string) V14_6Mode {
	for i := 1; i < len(argv); i++ {
		a := argv[i]
		if m, ok := matchV14_6Flag(a, argv, i); ok {
			return m
		}
	}
	return V14_6Mode{Ok: false}
}

func matchV14_6Flag(flag string, argv []string, i int) (V14_6Mode, bool) {
	// Handle --key=value form first.
	if idx := indexOfEq(flag); idx > 0 {
		base := flag[:idx]
		val := flag[idx+1:]
		n, _ := strconv.Atoi(val)
		switch base {
		case "--multi-node":
			if n <= 0 {
				n = 3
			}
			return V14_6Mode{Name: "multi-node", N: n, Ok: true}, true
		case "--bucket-verify":
			if n <= 0 {
				n = BucketStateDefaultCount
			}
			return V14_6Mode{Name: "bucket-verify", N: n, Ok: true}, true
		case "--high-iteration-replay":
			if n <= 0 {
				n = HighIterationReplayDefault
			}
			return V14_6Mode{Name: "high-iteration-replay", N: n, Ok: true}, true
		}
	}

	switch flag {
	case "--multi-node":
		n := 3
		if i+1 < len(argv) {
			if v, err := strconv.Atoi(argv[i+1]); err == nil && v > 0 {
				n = v
			}
		}
		return V14_6Mode{Name: "multi-node", N: n, Ok: true}, true
	case "--clock-drift":
		return V14_6Mode{Name: "clock-drift", Ok: true}, true
	case "--transport-adversarial":
		return V14_6Mode{Name: "transport-adversarial", Ok: true}, true
	case "--bucket-verify":
		n := BucketStateDefaultCount
		if i+1 < len(argv) {
			if v, err := strconv.Atoi(argv[i+1]); err == nil && v > 0 {
				n = v
			}
		}
		return V14_6Mode{Name: "bucket-verify", N: n, Ok: true}, true
	case "--cross-system-validate":
		return V14_6Mode{Name: "cross-system-validate", Ok: true}, true
	case "--high-iteration-replay":
		n := HighIterationReplayDefault
		if i+1 < len(argv) {
			if v, err := strconv.Atoi(argv[i+1]); err == nil && v > 0 {
				n = v
			}
		}
		return V14_6Mode{Name: "high-iteration-replay", N: n, Ok: true}, true
	case "--vc-demo":
		return V14_6Mode{Name: "vc-demo", Ok: true}, true
	case "--v14-6-audit":
		return V14_6Mode{Name: "audit", Ok: true}, true
	case "--v14-6":
		return V14_6Mode{Name: "all", Ok: true}, true
	case MultiNodeChildFlag:
		return V14_6Mode{Name: "multi-node-child", Ok: true}, true
	}
	return V14_6Mode{}, false
}

func indexOfEq(s string) int {
	for i := 0; i < len(s); i++ {
		if s[i] == '=' {
			return i
		}
	}
	return -1
}

// RunV14_6CLI is the entry point for the v14.6 CLI. It terminates the process
// with an exit code reflecting the phase's success.
func RunV14_6CLI(mode V14_6Mode) {
	switch mode.Name {
	case "multi-node":
		runMultiNodeCLI(mode.N)
	case "clock-drift":
		runClockDriftCLI()
	case "transport-adversarial":
		runTransportAdversarialCLI()
	case "bucket-verify":
		runBucketVerifyCLI(mode.N)
	case "cross-system-validate":
		runCrossSystemCLI()
	case "high-iteration-replay":
		runHighIterCLI(mode.N)
	case "vc-demo":
		runVCDemoCLI()
	case "audit":
		runAuditCLI()
	case "all":
		runV14_6All()
	case "multi-node-child":
		runMultiNodeChild()
	default:
		fmt.Fprintf(os.Stderr, "unknown v14.6 mode: %s\n", mode.Name)
		os.Exit(2)
	}
}

// --- individual runners ---

func runMultiNodeCLI(nodes int) {
	if nodes <= 0 {
		nodes = 3
	}
	skews := []int{0, 5, -5, 30, -30, 300, -300}
	if nodes > len(skews) {
		// extend with zeros
		pad := make([]int, nodes)
		copy(pad, skews)
		skews = pad
	} else {
		skews = skews[:nodes]
	}
	results, err := RunMultiNode(MultiNodeRunConfig{
		NodeCount:        nodes,
		ClockSkewSeconds: skews,
		Iterations:       MultiNodeDefaultIterations,
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, "multi-node: %v\n", err)
		os.Exit(1)
	}
	rep, verr := ValidateMultiNode(results)
	if verr != nil {
		fmt.Fprintf(os.Stderr, "multi-node validate: %v\n", verr)
		os.Exit(1)
	}
	if !rep.AllByteIdentical {
		os.Exit(1)
	}
	os.Exit(0)
}

func runClockDriftCLI() {
	rep, err := RunClockDriftHarness()
	if err != nil {
		fmt.Fprintf(os.Stderr, "clock-drift: %v\n", err)
		os.Exit(1)
	}
	if rep.DriftDetected {
		os.Exit(1)
	}
	os.Exit(0)
}

func runTransportAdversarialCLI() {
	rep, err := RunTransportAdversarialHarness()
	if err != nil {
		fmt.Fprintf(os.Stderr, "transport-adversarial: %v\n", err)
		os.Exit(1)
	}
	if !rep.TransportIntegrityVerified {
		os.Exit(1)
	}
	os.Exit(0)
}

func runBucketVerifyCLI(n int) {
	rep, err := RunBucketStateVerifierN(n)
	if err != nil {
		fmt.Fprintf(os.Stderr, "bucket-verify: %v\n", err)
		os.Exit(1)
	}
	if !rep.BucketStateVerified {
		os.Exit(1)
	}
	os.Exit(0)
}

func runCrossSystemCLI() {
	rep, err := RunCrossSystemIntegration()
	if err != nil {
		fmt.Fprintf(os.Stderr, "cross-system: %v\n", err)
		os.Exit(1)
	}
	if !rep.CrossSystemIntegrationVerified {
		os.Exit(1)
	}
	os.Exit(0)
}

func runHighIterCLI(n int) {
	_, err := RunHighIterationReplay(n)
	if err != nil {
		fmt.Fprintf(os.Stderr, "high-iter: %v\n", err)
		os.Exit(1)
	}
	os.Exit(0)
}

func runVCDemoCLI() {
	rep, err := RunVCValidationDemo()
	if err != nil {
		fmt.Fprintf(os.Stderr, "vc-demo: %v\n", err)
		os.Exit(1)
	}
	if !rep.AllPassed {
		os.Exit(1)
	}
	os.Exit(0)
}

func runAuditCLI() {
	rep, err := RunV14_6Audit()
	if err != nil {
		fmt.Fprintf(os.Stderr, "audit: %v\n", err)
		os.Exit(1)
	}
	if !rep.AllPassed {
		os.Exit(1)
	}
	os.Exit(0)
}

// runV14_6All executes every phase in sequence and finishes with the audit.
// Any phase failure breaks the chain; the audit still runs to record what did
// and did not produce its artefacts.
func runV14_6All() {
	printHeader("SARATHI v14.6 — FULL END-TO-END SEQUENCE")
	fmt.Println("  Phases: multi-node → clock-drift → transport → bucket → cross-system → 1000-iter → vc-demo → audit")
	fmt.Println()

	ran := 0
	failed := 0

	// 1. Multi-node.
	ran++
	{
		results, err := RunMultiNode(MultiNodeRunConfig{
			NodeCount:        3,
			ClockSkewSeconds: []int{0, 5, -5},
			Iterations:       MultiNodeDefaultIterations,
		})
		if err != nil {
			fmt.Fprintf(os.Stderr, "PHASE 1 multi-node: %v\n", err)
			failed++
		} else if rep, verr := ValidateMultiNode(results); verr != nil || !rep.AllByteIdentical {
			fmt.Fprintf(os.Stderr, "PHASE 1 validate failed: verr=%v all_byte_identical=%t\n",
				verr, rep != nil && rep.AllByteIdentical)
			failed++
		}
	}
	// 2. Clock drift.
	ran++
	if _, err := RunClockDriftHarness(); err != nil {
		fmt.Fprintf(os.Stderr, "PHASE 2 clock-drift: %v\n", err)
		failed++
	}
	// 3. Transport adversarial. The transport harness intentionally produces
	// halt violations — those ARE the success criterion for adversarial
	// scenarios. After this phase the global determinism_violation_log holds
	// adversarial entries that do not represent true drift, so we rotate it
	// to proof_logs/determinism_violation_log_transport.jsonl before the
	// canonical (non-adversarial) phases run. The audit check then asserts
	// the post-rotation log remains empty.
	ran++
	if rep, err := RunTransportAdversarialHarness(); err != nil || !rep.TransportIntegrityVerified {
		fmt.Fprintf(os.Stderr, "PHASE 3 transport: err=%v verified=%t\n",
			err, rep != nil && rep.TransportIntegrityVerified)
		failed++
	}
	rotateAdversarialViolationLog()
	// 4. Bucket.
	ran++
	if rep, err := RunBucketStateVerifier(); err != nil || !rep.BucketStateVerified {
		fmt.Fprintf(os.Stderr, "PHASE 4 bucket: err=%v verified=%t\n",
			err, rep != nil && rep.BucketStateVerified)
		failed++
	}
	// 5. Cross-system.
	ran++
	if rep, err := RunCrossSystemIntegration(); err != nil || !rep.CrossSystemIntegrationVerified {
		fmt.Fprintf(os.Stderr, "PHASE 6 cross-system: err=%v verified=%t\n",
			err, rep != nil && rep.CrossSystemIntegrationVerified)
		failed++
	}
	// 6. High-iter replay.
	ran++
	if _, err := RunHighIterationReplay(HighIterationReplayDefault); err != nil {
		fmt.Fprintf(os.Stderr, "PHASE 5 high-iter: %v\n", err)
		failed++
	}
	// 7. VC demo.
	ran++
	if rep, err := RunVCValidationDemo(); err != nil || !rep.AllPassed {
		fmt.Fprintf(os.Stderr, "PHASE 7 vc-demo: err=%v all_passed=%t\n",
			err, rep != nil && rep.AllPassed)
		failed++
	}
	// 8. Audit.
	auditRep, aerr := RunV14_6Audit()
	if aerr != nil || !auditRep.AllPassed {
		fmt.Fprintf(os.Stderr, "AUDIT: err=%v all_passed=%t\n",
			aerr, auditRep != nil && auditRep.AllPassed)
		failed++
	}

	fmt.Printf("\n  v14.6 full sequence: phases_run=%d failures=%d audit_pass=%t\n",
		ran, failed, auditRep != nil && auditRep.AllPassed)
	if failed > 0 || auditRep == nil || !auditRep.AllPassed {
		os.Exit(1)
	}
	os.Exit(0)
}

// rotateAdversarialViolationLog moves the global determinism violation log
// aside after the transport adversarial phase. The adversarial phase
// intentionally triggers response-hash-mismatch halts as its success
// criterion — those entries are not true drift. Moving the file keeps the
// original record (for inspection) while letting the audit pass assert that
// subsequent canonical phases produce an EMPTY violation log.
func rotateAdversarialViolationLog() {
	const src = "proof_logs/determinism_violation_log.jsonl"
	const dst = "proof_logs/determinism_violation_log_transport.jsonl"
	if _, err := os.Stat(src); err != nil {
		return
	}
	_ = os.Remove(dst)
	if err := os.Rename(src, dst); err != nil {
		fmt.Fprintf(os.Stderr, "WARN: rotate violation log: %v\n", err)
	}
}

// --- multi-node child worker ---

// runMultiNodeChild is the process invoked as `<self> --multi-node-child ...`.
// It performs a minimal per-node replay, writes its own artefacts, and writes
// the envelope manifest the parent reads.
func runMultiNodeChild() {
	iters := MultiNodeDefaultIterations
	nodeID := DefaultNodeID
	nodeDir := MultiNodeReportRoot

	argv := os.Args
	for i := 1; i < len(argv); i++ {
		switch argv[i] {
		case "--iterations":
			if i+1 < len(argv) {
				if v, err := strconv.Atoi(argv[i+1]); err == nil && v > 0 {
					iters = v
				}
			}
		case "--node-id":
			if i+1 < len(argv) {
				nodeID = argv[i+1]
			}
		case "--node-dir":
			if i+1 < len(argv) {
				nodeDir = argv[i+1]
			}
		}
	}
	if envID := os.Getenv(EnvNodeID); envID != "" {
		nodeID = envID
	}
	skew := int(parseClockSkewFromEnv() / time.Second)

	if err := os.MkdirAll(nodeDir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "multi-node-child: mkdir: %v\n", err)
		os.Exit(1)
	}

	reportPath := filepath.Join(nodeDir, MultiNodeReportName)
	manifestPath := filepath.Join(nodeDir, MultiNodeManifestName)
	logPath := filepath.Join(nodeDir, MultiNodeJSONLLogName)

	fx, err := BuildOrLoadReplayFixture()
	if err != nil {
		fmt.Fprintf(os.Stderr, "multi-node-child: fixture: %v\n", err)
		os.Exit(1)
	}
	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()
	if err := ea.GetEvaluatorRegistry().RegisterEvaluator(
		fx.EvaluatorID, "replay fixture evaluator", fx.PublicKey,
		map[string]string{"fixture": "true"}, "multi_node_child",
	); err != nil {
		fmt.Fprintf(os.Stderr, "multi-node-child: register: %v\n", err)
		os.Exit(1)
	}
	mc := NewModeController(BHIVModeExternal)
	pa := NewPDPAdapter(ea, mc)

	router := NewMultiSystemRouter(nil)
	for _, name := range []string{"core_workflow", "insightflow", "bucket"} {
		router.InstallPropagationHandler(name, func(event *RoutedEvent) error { return nil }, true, false)
	}
	router.InstallPropagationHandler("intent_layer",
		func(event *RoutedEvent) error { return nil }, false, true)

	// Single representative envelope for the manifest.
	pa.ResetReplayTrackerForHarness()
	env, ierr := pa.Ingest(fx.Bytes,
		fmt.Sprintf("EXEC-MN-%s-0", nodeID),
		fmt.Sprintf("corr-mn-%s-0", nodeID),
		nil)
	if ierr != nil {
		fmt.Fprintf(os.Stderr, "multi-node-child: ingest: %v\n", ierr)
		os.Exit(1)
	}
	canonical := env.CanonicalResponseBytes()
	stable := ProduceStableEnvelope(env)
	manifest := MultiNodeChildEnvelopeManifest{
		SchemaVersion:          "sarathi.multi_node.child_manifest/v1.0",
		NodeID:                 nodeID,
		ClockSkewSeconds:       skew,
		GeneratedAt:            time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		InputHash:              Sha256Hex(fx.Bytes),
		DecisionHash:           env.DecisionHash(),
		DecisionCoreHash:       env.DecisionCoreHash(),
		EnforcementHash:        env.EnforcementHash(),
		ResponseHash:           env.ResponseHash(),
		ChainBindingHash:       env.ChainBindingHash(),
		ResponseHashStable:     Sha256Hex(stable),
		ChainBindingHashStable: stableChainBindingHash(env),
		CanonicalLength:        len(canonical),
		CanonicalSha256:        Sha256Hex(canonical),
		StableCanonicalLength:  len(stable),
		StableCanonicalSha256:  Sha256Hex(stable),
	}
	if mb, jerr := json.MarshalIndent(manifest, "", "  "); jerr == nil {
		_ = os.WriteFile(manifestPath, mb, 0o644)
	}

	// Now run the full replay with per-node paths.
	cfg := PropagationReplayConfig{
		Iterations:      iters,
		StopOnFirstFail: false,
		LogFile:         logPath,
		ReportFile:      reportPath,
		Quiet:           true,
	}
	_, _, _, rerr := RunPropagationReplay(pa, router, fx.Bytes, cfg)
	if rerr != nil {
		fmt.Fprintf(os.Stderr, "multi-node-child: replay: %v\n", rerr)
		os.Exit(1)
	}
	fmt.Printf("multi-node-child %s complete skew=%+ds iters=%d\n", nodeID, skew, iters)
	os.Exit(0)
}
