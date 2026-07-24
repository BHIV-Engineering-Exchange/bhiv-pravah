// v14_8_cli.go (v14.8 Sovereign Authority Closure)
//
// CLI dispatch for v14.8 modes:
//
//   --failure-demo                       Spawn peers + Sarathi ack server, run 3
//                                        live failure injections, keep peers
//                                        alive for manual reviewer tampering.
//   --legacy-shim                        Run the reference legacy-enforcement
//                                        shim (BHIV-Core-compatible wire).
//   --parallel-execute [N]               Run N iterations through Sarathi AND
//                                        the legacy path, compare byte-for-byte.
//   --parallel-execute-suite [N]         Same + write the Phase-2 shaped report.
//   --distributed-integration [N]        Run against ALREADY-RUNNING peers
//                                        (local or cross-machine).
//   --peer-standalone-core               Long-lived peer; ParentPID defaults to
//   --peer-standalone-insightflow        0 (no parent watchdog); honours an
//   --peer-standalone-bucket             optional SARATHI_PEER_HEARTBEAT_URL.
//
// These flags are parsed BEFORE v14.7 flags (in enforcement_adapter_main.go)
// so v14.8 never interferes with v14.6/v14.7 audit modes — when no v14.8 flag
// is passed, execution falls through to the existing v14.7 dispatch exactly
// as before. All CLI state is additive.
//
// TAG: sovereign-authority-v14.8

package main

import (
	"fmt"
	"os"
	"strconv"
)

// v14.8 CLI flag constants.
const (
	FailureDemoFlag             = "--failure-demo"
	LegacyShimFlag              = "--legacy-shim"
	ParallelExecuteFlag         = "--parallel-execute"
	ParallelExecuteSuiteFlag    = "--parallel-execute-suite"
	DistributedIntegrationFlag  = "--distributed-integration"
	PeerStandaloneCoreFlag      = "--peer-standalone-core"
	PeerStandaloneInsightFlag   = "--peer-standalone-insightflow"
	PeerStandaloneBucketFlag    = "--peer-standalone-bucket"
)

// ParallelExecuteDefaultCount is the default iteration count for
// --parallel-execute when no N is supplied.
const ParallelExecuteDefaultCount = 10

// DistributedIntegrationDefaultCount is the default iteration count for
// --distributed-integration when no N is supplied.
const DistributedIntegrationDefaultCount = 10

// V14_8Mode is the parsed v14.8 CLI action.
type V14_8Mode struct {
	Name string
	N    int
	Ok   bool
}

// ParseV14_8Args looks for v14.8 flags and returns the parsed mode.
// Returns Ok=false when no v14.8 flag is present so the caller can fall
// through to the v14.7 dispatcher unchanged.
func ParseV14_8Args(argv []string) V14_8Mode {
	for i := 1; i < len(argv); i++ {
		a := argv[i]

		// --flag=value form
		if idx := indexOfEq(a); idx > 0 {
			base := a[:idx]
			val := a[idx+1:]
			n, _ := strconv.Atoi(val)
			switch base {
			case ParallelExecuteFlag:
				if n <= 0 {
					n = ParallelExecuteDefaultCount
				}
				return V14_8Mode{Name: "parallel-execute", N: n, Ok: true}
			case ParallelExecuteSuiteFlag:
				if n <= 0 {
					n = ParallelExecuteDefaultCount
				}
				return V14_8Mode{Name: "parallel-execute-suite", N: n, Ok: true}
			case DistributedIntegrationFlag:
				if n <= 0 {
					n = DistributedIntegrationDefaultCount
				}
				return V14_8Mode{Name: "distributed-integration", N: n, Ok: true}
			}
		}

		// bare flag / flag + count forms
		switch a {
		case FailureDemoFlag:
			return V14_8Mode{Name: "failure-demo", Ok: true}
		case LegacyShimFlag:
			return V14_8Mode{Name: "legacy-shim", Ok: true}
		case PeerStandaloneCoreFlag:
			return V14_8Mode{Name: "peer-standalone-core", Ok: true}
		case PeerStandaloneInsightFlag:
			return V14_8Mode{Name: "peer-standalone-insightflow", Ok: true}
		case PeerStandaloneBucketFlag:
			return V14_8Mode{Name: "peer-standalone-bucket", Ok: true}
		case ParallelExecuteFlag:
			n := ParallelExecuteDefaultCount
			if i+1 < len(argv) {
				if v, err := strconv.Atoi(argv[i+1]); err == nil && v > 0 {
					n = v
				}
			}
			return V14_8Mode{Name: "parallel-execute", N: n, Ok: true}
		case ParallelExecuteSuiteFlag:
			n := ParallelExecuteDefaultCount
			if i+1 < len(argv) {
				if v, err := strconv.Atoi(argv[i+1]); err == nil && v > 0 {
					n = v
				}
			}
			return V14_8Mode{Name: "parallel-execute-suite", N: n, Ok: true}
		case DistributedIntegrationFlag:
			n := DistributedIntegrationDefaultCount
			if i+1 < len(argv) {
				if v, err := strconv.Atoi(argv[i+1]); err == nil && v > 0 {
					n = v
				}
			}
			return V14_8Mode{Name: "distributed-integration", N: n, Ok: true}
		}
	}
	return V14_8Mode{Ok: false}
}

// RunV14_8CLI dispatches to the selected v14.8 entry point.
func RunV14_8CLI(mode V14_8Mode) {
	switch mode.Name {
	case "failure-demo":
		os.Exit(RunFailureDemo())
	case "legacy-shim":
		os.Exit(RunLegacyShim())
	case "parallel-execute":
		os.Exit(RunParallelExecution(mode.N))
	case "parallel-execute-suite":
		os.Exit(RunParallelExecutionSuite(mode.N))
	case "distributed-integration":
		os.Exit(RunDistributedIntegration(mode.N))
	case "peer-standalone-core":
		runPeerStandalone(PeerCore)
	case "peer-standalone-insightflow":
		runPeerStandalone(PeerInsightFlow)
	case "peer-standalone-bucket":
		runPeerStandalone(PeerBucket)
	default:
		fmt.Fprintf(os.Stderr, "unknown v14.8 mode: %s\n", mode.Name)
		os.Exit(2)
	}
}

// runPeerStandalone boots a long-lived peer whose lifetime is NOT bound to a
// parent Sarathi process. Used for cross-machine deployments where the peer
// runs on Machine B and Sarathi runs on Machine A. Reads configuration from
// environment variables; the operator is responsible for supplying them.
func runPeerStandalone(kind PeerKind) {
	cfg := PeerServerConfig{
		Kind:          kind,
		Addr:          os.Getenv("SARATHI_PEER_ADDR"),
		StorageRoot:   envOrDefault("SARATHI_PEER_STORAGE_ROOT", LivePeerDefaultStorageRoot),
		SarathiAckURL: os.Getenv("SARATHI_PEER_ACK_URL"),
		HandshakeURL:  os.Getenv("SARATHI_PEER_HANDSHAKE_URL"),
		// ParentPID defaults to 0 → parent-watchdog disabled. If the operator
		// explicitly sets SARATHI_PEER_PARENT_PID to a positive value, the
		// watchdog reactivates (useful when standalone mode is launched via
		// ssh from the Sarathi host and we DO want the peer to die if the
		// ssh session collapses).
	}
	if pid, _ := strconv.Atoi(os.Getenv("SARATHI_PEER_PARENT_PID")); pid > 0 {
		cfg.ParentPID = pid
	}
	if cfg.Addr == "" {
		fmt.Fprintf(os.Stderr,
			"peer-standalone %s: SARATHI_PEER_ADDR is required (e.g. 0.0.0.0:7101)\n",
			kind)
		os.Exit(1)
	}
	srv, err := NewPeerServer(cfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "peer-standalone %s: init: %v\n", kind, err)
		os.Exit(1)
	}
	fmt.Printf("[peer-standalone %s] starting; ctrl-c to stop\n", kind)
	if err := srv.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "peer-standalone %s: start: %v\n", kind, err)
		os.Exit(1)
	}
}
