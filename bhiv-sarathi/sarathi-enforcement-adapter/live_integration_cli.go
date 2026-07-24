// live_integration_cli.go (v14.7 Live Integration Closure)
//
// CLI dispatch for v14.7 modes:
//
//   --peer-core                 Run the BHIV Core conformance peer process
//   --peer-insightflow          Run the InsightFlow conformance peer
//   --peer-bucket               Run the Bucket conformance peer
//   --live-integration [N]      Run the full live-integration orchestrator
//                               (spawns peers + N executions + verifies gate +
//                                writes live_integration_report.json)
//   --live-integration-suite [N] Run the full integration test suite
//
// These flags are parsed AFTER the v14.6 flags (in enforcement_adapter_main.go)
// so v14.7 never interferes with v14.6 audit modes.
//
// TAG: live-integration

package main

import (
	"fmt"
	"os"
	"strconv"
)

// LivePeerCoreFlag, LivePeerInsightFlowFlag, LivePeerBucketFlag are the
// sub-command flags that turn the process into a standalone peer.
const (
	LivePeerCoreFlag          = "--peer-core"
	LivePeerInsightFlowFlag   = "--peer-insightflow"
	LivePeerBucketFlag        = "--peer-bucket"
	LiveIntegrationFlag       = "--live-integration"
	LiveIntegrationSuiteFlag  = "--live-integration-suite"
	LiveRetryDeterminismFlag  = "--live-retry-determinism"
)

// LiveIntegrationDefaultCount is the default number of executions the runner
// performs when --live-integration is passed without a count.
const LiveIntegrationDefaultCount = 25

// V14_7Mode is the parsed v14.7 CLI action.
type V14_7Mode struct {
	Name string
	N    int
	Ok   bool
}

// ParseV14_7Args looks for v14.7 flags and returns the parsed mode.
func ParseV14_7Args(argv []string) V14_7Mode {
	for i := 1; i < len(argv); i++ {
		a := argv[i]
		// --flag=value form
		if idx := indexOfEq(a); idx > 0 {
			base := a[:idx]
			val := a[idx+1:]
			n, _ := strconv.Atoi(val)
			switch base {
			case LiveIntegrationFlag:
				if n <= 0 {
					n = LiveIntegrationDefaultCount
				}
				return V14_7Mode{Name: "live-integration", N: n, Ok: true}
			case LiveIntegrationSuiteFlag:
				if n <= 0 {
					n = LiveIntegrationDefaultCount
				}
				return V14_7Mode{Name: "live-integration-suite", N: n, Ok: true}
			}
		}
		switch a {
		case LivePeerCoreFlag:
			return V14_7Mode{Name: "peer-core", Ok: true}
		case LivePeerInsightFlowFlag:
			return V14_7Mode{Name: "peer-insightflow", Ok: true}
		case LivePeerBucketFlag:
			return V14_7Mode{Name: "peer-bucket", Ok: true}
		case LiveIntegrationFlag:
			n := LiveIntegrationDefaultCount
			if i+1 < len(argv) {
				if v, err := strconv.Atoi(argv[i+1]); err == nil && v > 0 {
					n = v
				}
			}
			return V14_7Mode{Name: "live-integration", N: n, Ok: true}
		case LiveIntegrationSuiteFlag:
			n := LiveIntegrationDefaultCount
			if i+1 < len(argv) {
				if v, err := strconv.Atoi(argv[i+1]); err == nil && v > 0 {
					n = v
				}
			}
			return V14_7Mode{Name: "live-integration-suite", N: n, Ok: true}
		case LiveRetryDeterminismFlag:
			return V14_7Mode{Name: "retry-determinism", Ok: true}
		}
	}
	return V14_7Mode{Ok: false}
}

// RunV14_7CLI dispatches to the selected v14.7 entry point.
func RunV14_7CLI(mode V14_7Mode) {
	switch mode.Name {
	case "peer-core":
		runPeerProcess(PeerCore)
	case "peer-insightflow":
		runPeerProcess(PeerInsightFlow)
	case "peer-bucket":
		runPeerProcess(PeerBucket)
	case "live-integration":
		exitCode := RunLiveIntegration(mode.N)
		os.Exit(exitCode)
	case "live-integration-suite":
		exitCode := RunLiveIntegrationSuite(mode.N)
		os.Exit(exitCode)
	case "retry-determinism":
		exitCode := RunRetryDeterminismCLI()
		os.Exit(exitCode)
	default:
		fmt.Fprintf(os.Stderr, "unknown v14.7 mode: %s\n", mode.Name)
		os.Exit(2)
	}
}

// runPeerProcess boots a single peer server and blocks until shutdown.
// Reads configuration from environment variables so each peer is a clean,
// self-contained process that knows nothing about the others.
func runPeerProcess(kind PeerKind) {
	cfg := PeerServerConfig{
		Kind:          kind,
		Addr:          os.Getenv("SARATHI_PEER_ADDR"),
		StorageRoot:   envOrDefault("SARATHI_PEER_STORAGE_ROOT", LivePeerDefaultStorageRoot),
		SarathiAckURL: os.Getenv("SARATHI_PEER_ACK_URL"),
		HandshakeURL:  os.Getenv("SARATHI_PEER_HANDSHAKE_URL"),
	}
	if pid, _ := strconv.Atoi(os.Getenv("SARATHI_PEER_PARENT_PID")); pid > 0 {
		cfg.ParentPID = pid
	}
	srv, err := NewPeerServer(cfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "peer %s: init: %v\n", kind, err)
		os.Exit(1)
	}
	if err := srv.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "peer %s: start: %v\n", kind, err)
		os.Exit(1)
	}
}

func envOrDefault(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
