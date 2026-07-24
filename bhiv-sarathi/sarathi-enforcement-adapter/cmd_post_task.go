// cmd_post_task.go (v15.4 BHIV Core Input Bootstrap)
//
// CLI subcommand: --post-task-to-core
//
// Posts a fresh task input to BHIV Core API /execute_task and prints the
// response (which contains Core's generated trace_id, decision verdict,
// decision_hash, etc.). After this call, Core drives the rest of the BHIV
// chain back through MCP Bridge -> Sovereign Core -> Sarathi /sarathi/enforce
// -> downstream propagation.
//
// This is the v15.4 input-bootstrap entry point; the historical decision-
// ingestion entry (POST /v1/ingest-decision) is unaffected and continues to
// work in parallel.
//
// Usage:
//
//	./sarathi --post-task-to-core --input "summarize document X"
//	./sarathi --post-task-to-core --input "deploy v2" --context-json '{"agent":"hemanth"}'
//	./sarathi --post-task-to-core=summarize        # short form, no context
//
// Endpoint URL is read from SARATHI_CORE_EXECUTE_TASK_URL (set via
// scripts/ngrok_env.sh or manually). HTTP timeout is 15s by default
// (override SARATHI_ECOSYSTEM_TIMEOUT_MS).
//
// TAG: post-task-input-v15.4

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

const (
	PostTaskToCoreFlag = "--post-task-to-core"
	PostTaskInputFlag  = "--input"
	PostTaskCtxFlag    = "--context-json"
)

// PostTaskMode is the parsed --post-task-to-core invocation.
type PostTaskMode struct {
	Input       string
	ContextJSON string
	Ok          bool
}

// ParsePostTaskArgs scans argv for --post-task-to-core, --input, and
// --context-json. Returns Ok=false if --post-task-to-core is absent.
//
// Supported forms:
//
//	--post-task-to-core --input "..." [--context-json '{}']
//	--post-task-to-core=<input>
//	--post-task-to-core <input-as-next-positional>     (only if no --input flag)
func ParsePostTaskArgs(argv []string) PostTaskMode {
	mode := PostTaskMode{}
	flagSeen := false
	for i := 1; i < len(argv); i++ {
		a := argv[i]
		// --post-task-to-core=<value>
		if strings.HasPrefix(a, PostTaskToCoreFlag+"=") {
			flagSeen = true
			mode.Input = strings.TrimPrefix(a, PostTaskToCoreFlag+"=")
			continue
		}
		if a == PostTaskToCoreFlag {
			flagSeen = true
			continue
		}
		// --input <value> or --input=<value>
		if a == PostTaskInputFlag && i+1 < len(argv) {
			mode.Input = argv[i+1]
			i++
			continue
		}
		if strings.HasPrefix(a, PostTaskInputFlag+"=") {
			mode.Input = strings.TrimPrefix(a, PostTaskInputFlag+"=")
			continue
		}
		// --context-json <value> or --context-json=<value>
		if a == PostTaskCtxFlag && i+1 < len(argv) {
			mode.ContextJSON = argv[i+1]
			i++
			continue
		}
		if strings.HasPrefix(a, PostTaskCtxFlag+"=") {
			mode.ContextJSON = strings.TrimPrefix(a, PostTaskCtxFlag+"=")
			continue
		}
	}
	if flagSeen {
		mode.Ok = true
	}
	return mode
}

// RunPostTaskToCore executes the input-bootstrap call and prints results.
// Returns the process exit code (0 = success, non-zero = failure).
func RunPostTaskToCore(mode PostTaskMode) int {
	fmt.Println("+-------------------------------------------------------+")
	fmt.Println("|  SARATHI v15.4 -- POST TASK TO BHIV CORE              |")
	fmt.Println("|  Input-bootstrap path                                 |")
	fmt.Println("|  Core generates trace_id, drives full BHIV chain      |")
	fmt.Println("+-------------------------------------------------------+")

	if strings.TrimSpace(mode.Input) == "" {
		fmt.Fprintln(os.Stderr,
			"FATAL: --input is required (or pass --post-task-to-core=<input>)")
		fmt.Fprintln(os.Stderr,
			"Example: ./sarathi --post-task-to-core --input \"summarize doc X\"")
		return 2
	}

	// Resolve ecosystem endpoints from env vars / defaults.
	endpoints, err := LoadEcosystemEndpoints()
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: LoadEcosystemEndpoints: %v\n", err)
		return 2
	}
	fmt.Printf("  endpoints source: %s\n", endpoints.Source)
	fmt.Printf("  Core /execute_task URL: %s\n", endpoints.Core.ExecuteTask)

	// Refuse to call placeholder URLs (operator forgot to set env vars).
	if strings.Contains(endpoints.Core.ExecuteTask, PlaceholderHostMarker) {
		fmt.Fprintln(os.Stderr,
			"FATAL: SARATHI_CORE_EXECUTE_TASK_URL is still the unset-default placeholder.")
		fmt.Fprintln(os.Stderr,
			"       Run: source scripts/ngrok_env.sh --core-api <https://...>")
		fmt.Fprintln(os.Stderr,
			"       Or:  export SARATHI_CORE_EXECUTE_TASK_URL=<https://...>/execute_task")
		return 2
	}

	// Allow timeout override via env, mirroring ecosystem_clients.
	if v, perr := strconv.Atoi(os.Getenv("SARATHI_ECOSYSTEM_TIMEOUT_MS")); perr == nil && v > 0 {
		fmt.Printf("  http timeout: %dms (from SARATHI_ECOSYSTEM_TIMEOUT_MS)\n", v)
	} else {
		fmt.Printf("  http timeout: %s (default; override with SARATHI_ECOSYSTEM_TIMEOUT_MS)\n",
			EcosystemClientDefaultTimeout)
	}

	// Parse optional context JSON.
	var contextMap map[string]interface{}
	if strings.TrimSpace(mode.ContextJSON) != "" {
		if err := json.Unmarshal([]byte(mode.ContextJSON), &contextMap); err != nil {
			fmt.Fprintf(os.Stderr, "FATAL: --context-json is not valid JSON: %v\n", err)
			return 2
		}
	} else {
		contextMap = map[string]interface{}{}
	}

	client := NewCoreClient(endpoints.Core)
	fmt.Printf("\n  -> POST %s\n", endpoints.Core.ExecuteTask)
	fmt.Printf("     trace_id: \"\" (Core will generate)\n")
	fmt.Printf("     input: %q\n", mode.Input)
	if len(contextMap) > 0 {
		fmt.Printf("     context: %v\n", contextMap)
	}

	t0 := time.Now()
	respBytes, err := client.PostTaskInput(mode.Input, contextMap)
	rtt := time.Since(t0)

	if err != nil {
		fmt.Fprintf(os.Stderr, "\nFATAL: PostTaskInput: %v\n", err)
		return 1
	}

	fmt.Printf("\n  <- response received (rtt=%s, %d bytes)\n", rtt, len(respBytes))

	// Pretty-print structured fields if response parses as JSON.
	var parsed map[string]interface{}
	if err := json.Unmarshal(respBytes, &parsed); err == nil {
		printRespField(parsed, "trace_id")
		printRespField(parsed, "decision")
		printRespField(parsed, "decision_hash")
		printRespField(parsed, "policy_reference")
		printRespField(parsed, "input_hash")
		printRespField(parsed, "timestamp")
	}

	// Always echo the raw body for full visibility.
	fmt.Println("\n  raw response body:")
	fmt.Println("  ----------------------------------------------------------------")
	pretty, perr := json.MarshalIndent(json.RawMessage(respBytes), "  ", "  ")
	if perr == nil {
		fmt.Println("  " + string(pretty))
	} else {
		fmt.Println("  " + string(respBytes))
	}
	fmt.Println("  ----------------------------------------------------------------")

	fmt.Println("\n[post-task-to-core] OK")
	fmt.Println("[post-task-to-core] Core has accepted the task and will drive the chain:")
	fmt.Println("                    Core -> MCP /handle_task -> Sovereign /sovereign/decide")
	fmt.Println("                    -> Sarathi /sarathi/enforce -> propagation downstream")
	fmt.Println("                    Watch the Sarathi --service log for the inbound callback.")
	return 0
}

// printRespField is a small helper to render one field if present.
func printRespField(m map[string]interface{}, key string) {
	if v, ok := m[key]; ok {
		fmt.Printf("    %-18s %v\n", key+":", v)
	}
}
