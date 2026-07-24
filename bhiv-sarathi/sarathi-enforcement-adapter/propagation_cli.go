// propagation_cli.go (v14.5 Cross-System Propagation Layer)
//
// Thin CLI adapter that turns `--propagation-replay N` (and
// `--propagation-fault-injection`) into calls to the harness functions.
// Kept separate from enforcement_adapter_main.go so the main harness is not
// bloated with argument parsing specific to the new layer.

package main

import (
	"fmt"
	"os"
	"strconv"
)

// parsePropagationReplayArgs inspects the argv slice and returns:
//   mode == "replay"          for `--propagation-replay [N]`
//   mode == "fault-injection" for `--propagation-fault-injection`
//   mode == ""                if no propagation flag is present
// N defaults to PropagationReplayDefaultIterations when omitted.
func parsePropagationReplayArgs(argv []string) (mode string, n int, ok bool) {
	n = PropagationReplayDefaultIterations
	for i := 1; i < len(argv); i++ {
		a := argv[i]
		switch a {
		case "--propagation-replay":
			ok = true
			mode = "replay"
			// optional positional count
			if i+1 < len(argv) {
				if v, err := strconv.Atoi(argv[i+1]); err == nil && v > 0 {
					n = v
				}
			}
			return
		case "--propagation-fault-injection":
			ok = true
			mode = "fault-injection"
			return
		}
		// Support --propagation-replay=N form.
		if len(a) > len("--propagation-replay=") && a[:len("--propagation-replay=")] == "--propagation-replay=" {
			if v, err := strconv.Atoi(a[len("--propagation-replay="):]); err == nil && v > 0 {
				ok = true
				mode = "replay"
				n = v
				return
			}
		}
	}
	return "", 0, false
}

// runPropagationReplayCLI spins up the minimum viable stack (EnforcementAdapter
// + PDPAdapter + MultiSystemRouter with in-memory OK handlers) and invokes
// the replay harness. On exit the process terminates with status 0 when the
// harness passes and 1 otherwise, so CI can gate on the result.
func runPropagationReplayCLI(mode string, iterations int) {
	printHeader(fmt.Sprintf("CROSS-SYSTEM PROPAGATION CLI MODE: %s", mode))

	fx, err := BuildOrLoadReplayFixture()
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: build replay fixture: %v\n", err)
		os.Exit(1)
	}

	// Stand up a standalone EnforcementAdapter in EXTERNAL mode. Nil PDP +
	// nil PolicyRegistry + nil TokenAuthority is sufficient for the
	// propagation flow — the fixture verdict is ALLOW and the integrity
	// checks (hash recomputation, signature verify) do not need them.
	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()
	if err := ea.GetEvaluatorRegistry().RegisterEvaluator(
		fx.EvaluatorID, "replay fixture evaluator", fx.PublicKey,
		map[string]string{"fixture": "true"}, "cli",
	); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: register fixture evaluator: %v\n", err)
		os.Exit(1)
	}
	mc := NewModeController(BHIVModeExternal)
	pa := NewPDPAdapter(ea, mc)

	router := NewMultiSystemRouter(nil)
	// In-memory OK handlers for all standard targets. Real deployments call
	// router.WireDeterministicTargets(env) once per envelope; the CLI replay
	// proves byte-equality purely in-process.
	for _, name := range []string{"core_workflow", "insightflow", "bucket"} {
		router.InstallPropagationHandler(name, func(event *RoutedEvent) error { return nil }, true, false)
	}
	router.InstallPropagationHandler("intent_layer",
		func(event *RoutedEvent) error { return nil }, false, true)

	switch mode {
	case "replay":
		cfg := PropagationReplayConfig{
			Iterations:      iterations,
			StopOnFirstFail: false,
		}
		passed, failed, report, rerr := RunPropagationReplay(pa, router, fx.Bytes, cfg)
		if rerr != nil {
			fmt.Fprintf(os.Stderr, "ERROR: %v\n", rerr)
			os.Exit(1)
		}
		_ = passed
		_ = failed
		if !report.AllByteIdentical {
			os.Exit(1)
		}
		os.Exit(0)

	case "fault-injection":
		// Delegate to the dedicated simulator which installs a byte-mutating
		// handler and asserts the stop error fires.
		passed, failed := RunPropagationFaultInjection(pa, router, fx.Bytes)
		fmt.Printf("\n  Fault injection: passed=%d failed=%d\n", passed, failed)
		if failed > 0 {
			os.Exit(1)
		}
		os.Exit(0)

	default:
		fmt.Fprintf(os.Stderr, "unknown propagation CLI mode: %s\n", mode)
		os.Exit(2)
	}
}
