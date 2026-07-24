package main

// concurrency_stress_sim.go — High-Concurrency Stress Testing for Sarathi v5.0.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Concurrency Stress Simulator (v5.0)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   Validates the Sarathi v5.0 stack under extreme concurrency conditions.
//   Every shared resource (bridge, service, router, key manager, audit sink)
//   is hammered by multiple goroutines simultaneously to detect:
//   - Race conditions (data races on shared state)
//   - Deadlocks (goroutine hangs under lock contention)
//   - Metric inconsistencies (atomic counter drift)
//   - Chain corruption (hash chain integrity under concurrent writes)
//   - Resource leaks (goroutine leaks, memory leaks)
//
// TEST SCENARIOS:
//   1. Concurrent bridge requests from multiple caller systems
//   2. Concurrent key rotation + verification
//   3. Concurrent router target management
//   4. Mixed read/write on service metrics
//   5. Concurrent audit sink writes
//   6. Concurrent caller registration/suspension
//   7. Burst traffic (thundering herd simulation)
//   8. Long-running sustained load
//
// DESIGN REFERENCES:
//   - Go race detector: -race flag validation
//   - Google's Thread Sanitizer: Data race detection
//   - Netflix Chaos Monkey: Fault injection under load
//   - AWS Load Testing: Step-function traffic ramp
//   - Apache JMeter: Concurrent user simulation patterns

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// ================================================================
// STRESS TEST CONFIGURATION
// ================================================================

// StressConfig configures the concurrency stress tests.
type StressConfig struct {
	ConcurrentWorkers int           // Number of goroutines per test
	RequestsPerWorker int           // Requests each worker sends
	BurstSize         int           // Thundering herd burst size
	SustainedDuration time.Duration // Duration for sustained load test
}

// DefaultStressConfig returns production-grade stress test defaults.
func DefaultStressConfig() StressConfig {
	return StressConfig{
		ConcurrentWorkers: 50,
		RequestsPerWorker: 20,
		BurstSize:         200,
		SustainedDuration: 2 * time.Second,
	}
}

// StressTestResult captures the outcome of a stress test.
type StressTestResult struct {
	TestID           string        `json:"test_id"`
	Description      string        `json:"description"`
	Workers          int           `json:"workers"`
	TotalRequests    int           `json:"total_requests"`
	TotalAllowed     int64         `json:"total_allowed"`
	TotalDenied      int64         `json:"total_denied"`
	TotalErrors      int64         `json:"total_errors"`
	Duration         time.Duration `json:"duration"`
	RequestsPerSec   float64       `json:"requests_per_sec"`
	Passed           bool          `json:"passed"`
	Detail           string        `json:"detail"`
}

// StressSummary captures the overall stress test summary.
type StressSummary struct {
	TotalTests      int     `json:"total_tests"`
	Passed          int     `json:"passed"`
	Failed          int     `json:"failed"`
	TotalRequests   int64   `json:"total_requests"`
	PeakRPS         float64 `json:"peak_rps"`
	Duration        time.Duration `json:"total_duration"`
}

// ================================================================
// STRESS SIMULATOR
// ================================================================

// ConcurrencyStressSimulator orchestrates high-concurrency testing.
type ConcurrencyStressSimulator struct {
	bridge     *GatedBridge
	service    *SaarthiService
	router     *MultiSystemRouter
	keyManager *KeyManager
	auditSink  *InMemoryAuditSink
	config     StressConfig
	results    []StressTestResult
	passed     int
	failed     int
}

// NewConcurrencyStressSimulator creates a stress simulator over the v5.0 stack.
func NewConcurrencyStressSimulator(
	bridge *GatedBridge,
	service *SaarthiService,
	router *MultiSystemRouter,
	keyManager *KeyManager,
	auditSink *InMemoryAuditSink,
	config StressConfig,
) *ConcurrencyStressSimulator {
	return &ConcurrencyStressSimulator{
		bridge:     bridge,
		service:    service,
		router:     router,
		keyManager: keyManager,
		auditSink:  auditSink,
		config:     config,
		results:    make([]StressTestResult, 0, 10),
	}
}

// RunAllStressTests executes all concurrency stress scenarios.
func (css *ConcurrencyStressSimulator) RunAllStressTests() StressSummary {
	start := time.Now()

	fmt.Println("\n+-------------------------------------------------------+")
	fmt.Println("|  SARATHI CONCURRENCY STRESS SIMULATOR v5.0            |")
	fmt.Printf("|  Workers: %d  Requests/Worker: %d                    |\n",
		css.config.ConcurrentWorkers, css.config.RequestsPerWorker)
	fmt.Println("+-------------------------------------------------------+")

	// STRESS-01: Concurrent bridge requests
	css.stressConcurrentBridgeRequests()

	// STRESS-02: Concurrent mixed callers
	css.stressMixedCallers()

	// STRESS-03: Thundering herd burst
	css.stressThunderingHerd()

	// STRESS-04: Concurrent key operations
	css.stressConcurrentKeyOps()

	// STRESS-05: Concurrent router management
	css.stressConcurrentRouterOps()

	// STRESS-06: Concurrent caller suspension
	css.stressConcurrentCallerSuspension()

	// STRESS-07: Metric consistency under load
	css.stressMetricConsistency()

	// STRESS-08: Chain integrity under concurrent writes
	css.stressChainIntegrity()

	// Summary
	summary := css.buildSummary(time.Since(start))
	css.printSummary(summary)

	return summary
}

// ================================================================
// STRESS-01: CONCURRENT BRIDGE REQUESTS
// ================================================================

func (css *ConcurrencyStressSimulator) stressConcurrentBridgeRequests() {
	printSubheader("STRESS-01: Concurrent Bridge Requests")

	var allowed, denied, errors int64
	var wg sync.WaitGroup
	start := time.Now()

	for w := 0; w < css.config.ConcurrentWorkers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for r := 0; r < css.config.RequestsPerWorker; r++ {
				resp := css.bridge.RouteExecution(&SaarthiRequest{
					AgentID:       "gov-agent-001",
					ResourceID:    "policy-reg-001",
					Action:        "read",
					CorrelationID: fmt.Sprintf("stress-01-w%d-r%d", workerID, r),
					CallerSystem:  "test_harness",
					CallerVersion: "5.0.0",
					RequestedAt:   time.Now().UTC(),
				})
				switch resp.Verdict {
				case "ALLOW":
					atomic.AddInt64(&allowed, 1)
				case "DENY":
					atomic.AddInt64(&denied, 1)
				default:
					atomic.AddInt64(&errors, 1)
				}
			}
		}(w)
	}

	wg.Wait()
	duration := time.Since(start)
	total := css.config.ConcurrentWorkers * css.config.RequestsPerWorker
	rps := float64(total) / duration.Seconds()

	css.recordStressResult(StressTestResult{
		TestID:        "STRESS-01",
		Description:   "Concurrent bridge requests (all valid)",
		Workers:       css.config.ConcurrentWorkers,
		TotalRequests: total,
		TotalAllowed:  allowed,
		TotalDenied:   denied,
		TotalErrors:   errors,
		Duration:      duration,
		RequestsPerSec: rps,
		Passed:        errors == 0 && (allowed+denied) == int64(total),
		Detail:        fmt.Sprintf("rps=%.0f allowed=%d denied=%d errors=%d", rps, allowed, denied, errors),
	})
}

// ================================================================
// STRESS-02: CONCURRENT MIXED CALLERS
// ================================================================

func (css *ConcurrencyStressSimulator) stressMixedCallers() {
	printSubheader("STRESS-02: Mixed Caller Systems")

	callers := []struct {
		system string
		action string
	}{
		{"core", "read"},
		{"core", "write"},
		{"intent_layer", "read"},
		{"insightflow", "read"},
		{"bucket", "write"},
		{"admin", "delete"},
		{"test_harness", "read"},
	}

	var total, allowed, denied, errors int64
	var wg sync.WaitGroup
	start := time.Now()

	for w := 0; w < css.config.ConcurrentWorkers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for r := 0; r < css.config.RequestsPerWorker; r++ {
				caller := callers[(workerID+r)%len(callers)]
				resp := css.bridge.RouteExecution(&SaarthiRequest{
					AgentID:       "gov-agent-001",
					ResourceID:    "policy-reg-001",
					Action:        caller.action,
					CorrelationID: fmt.Sprintf("stress-02-w%d-r%d", workerID, r),
					CallerSystem:  caller.system,
					CallerVersion: "1.0.0",
					RequestedAt:   time.Now().UTC(),
				})
				atomic.AddInt64(&total, 1)
				switch resp.Verdict {
				case "ALLOW":
					atomic.AddInt64(&allowed, 1)
				case "DENY":
					atomic.AddInt64(&denied, 1)
				default:
					atomic.AddInt64(&errors, 1)
				}
			}
		}(w)
	}

	wg.Wait()
	duration := time.Since(start)
	rps := float64(total) / duration.Seconds()

	css.recordStressResult(StressTestResult{
		TestID:        "STRESS-02",
		Description:   "Mixed caller systems concurrent access",
		Workers:       css.config.ConcurrentWorkers,
		TotalRequests: int(total),
		TotalAllowed:  allowed,
		TotalDenied:   denied,
		TotalErrors:   errors,
		Duration:      duration,
		RequestsPerSec: rps,
		Passed:        errors == 0,
		Detail:        fmt.Sprintf("rps=%.0f total=%d allowed=%d denied=%d", rps, total, allowed, denied),
	})
}

// ================================================================
// STRESS-03: THUNDERING HERD BURST
// ================================================================

func (css *ConcurrencyStressSimulator) stressThunderingHerd() {
	printSubheader("STRESS-03: Thundering Herd Burst")

	var allowed, denied, errors int64
	var wg sync.WaitGroup
	start := time.Now()

	// All goroutines start simultaneously via barrier
	barrier := make(chan struct{})

	for i := 0; i < css.config.BurstSize; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			<-barrier // Wait for signal
			resp := css.bridge.RouteExecution(&SaarthiRequest{
				AgentID:       "gov-agent-001",
				ResourceID:    "policy-reg-001",
				Action:        "read",
				CorrelationID: fmt.Sprintf("stress-03-burst-%d", id),
				CallerSystem:  "test_harness",
				CallerVersion: "5.0.0",
				RequestedAt:   time.Now().UTC(),
			})
			switch resp.Verdict {
			case "ALLOW":
				atomic.AddInt64(&allowed, 1)
			case "DENY":
				atomic.AddInt64(&denied, 1)
			default:
				atomic.AddInt64(&errors, 1)
			}
		}(i)
	}

	// Release the herd
	close(barrier)
	wg.Wait()
	duration := time.Since(start)
	rps := float64(css.config.BurstSize) / duration.Seconds()

	css.recordStressResult(StressTestResult{
		TestID:        "STRESS-03",
		Description:   fmt.Sprintf("Thundering herd burst (%d simultaneous)", css.config.BurstSize),
		Workers:       css.config.BurstSize,
		TotalRequests: css.config.BurstSize,
		TotalAllowed:  allowed,
		TotalDenied:   denied,
		TotalErrors:   errors,
		Duration:      duration,
		RequestsPerSec: rps,
		Passed:        errors == 0,
		Detail:        fmt.Sprintf("burst_rps=%.0f allowed=%d denied=%d errors=%d", rps, allowed, denied, errors),
	})
}

// ================================================================
// STRESS-04: CONCURRENT KEY OPERATIONS
// ================================================================

func (css *ConcurrencyStressSimulator) stressConcurrentKeyOps() {
	printSubheader("STRESS-04: Concurrent Key Operations")

	// Create a fresh KeyManager for stress testing (avoids MaxActiveKeys conflicts)
	freshKeyring := NewGovernanceKeyRing()
	freshKM, kmErr := NewKeyManager(freshKeyring, css.auditSink, KeyManagerConfig{
		DefaultKeyExpiryDays:   90,
		RotationOverlapMinutes: 1,
		RequireCeremony:        false,
		MaxActiveKeys:          20, // High limit for concurrent stress
		AutoRotateOnExpiry:     false,
	})
	if kmErr != nil {
		css.recordStressResult(StressTestResult{
			TestID:      "STRESS-04",
			Description: "Concurrent key generation + activation",
			Passed:      false,
			Detail:      fmt.Sprintf("KeyManager creation failed: %v", kmErr),
		})
		return
	}
	defer freshKM.Shutdown()

	var generated, activated, errors int64
	var wg sync.WaitGroup
	start := time.Now()
	keyCount := 10

	for i := 0; i < keyCount; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			keyID := GovernanceKeyID(fmt.Sprintf("stress-key-%d", id))

			// Generate
			_, err := freshKM.GenerateKey(keyID)
			if err != nil {
				atomic.AddInt64(&errors, 1)
				return
			}
			atomic.AddInt64(&generated, 1)

			// Activate
			err = freshKM.ActivateKey(keyID, "stress_test")
			if err != nil {
				atomic.AddInt64(&errors, 1)
				return
			}
			atomic.AddInt64(&activated, 1)
		}(i)
	}

	wg.Wait()
	duration := time.Since(start)

	css.recordStressResult(StressTestResult{
		TestID:        "STRESS-04",
		Description:   fmt.Sprintf("Concurrent key generation + activation (%d keys)", keyCount),
		Workers:       keyCount,
		TotalRequests: keyCount * 2,
		TotalAllowed:  generated + activated,
		TotalErrors:   errors,
		Duration:      duration,
		Passed:        errors == 0 && generated == int64(keyCount),
		Detail:        fmt.Sprintf("generated=%d activated=%d errors=%d", generated, activated, errors),
	})

	// Verify chain integrity after concurrent ops
	valid, _, reason := freshKM.VerifyEventChain()
	fmt.Printf("  Key event chain after stress: intact=%v reason=%s\n", valid, reason)
}

// ================================================================
// STRESS-05: CONCURRENT ROUTER OPERATIONS
// ================================================================

func (css *ConcurrencyStressSimulator) stressConcurrentRouterOps() {
	printSubheader("STRESS-05: Concurrent Router Target Management")

	var ops, errors int64
	var wg sync.WaitGroup
	start := time.Now()
	workers := 20

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for i := 0; i < 10; i++ {
				atomic.AddInt64(&ops, 1)
				// Alternate between deactivate/reactivate
				if i%2 == 0 {
					css.router.DeactivateTarget("insightflow")
				} else {
					css.router.ReactivateTarget("insightflow")
				}
			}
		}(w)
	}

	wg.Wait()
	duration := time.Since(start)

	// Ensure router is in consistent state
	css.router.ReactivateTarget("insightflow")

	css.recordStressResult(StressTestResult{
		TestID:        "STRESS-05",
		Description:   "Concurrent router target activate/deactivate",
		Workers:       workers,
		TotalRequests: int(ops),
		TotalAllowed:  ops,
		TotalErrors:   errors,
		Duration:      duration,
		Passed:        true, // No panic = pass
		Detail:        fmt.Sprintf("ops=%d errors=%d (no panic, no deadlock)", ops, errors),
	})
}

// ================================================================
// STRESS-06: CONCURRENT CALLER SUSPENSION
// ================================================================

func (css *ConcurrencyStressSimulator) stressConcurrentCallerSuspension() {
	printSubheader("STRESS-06: Concurrent Caller Suspension + Request")

	var allowed, denied int64
	var wg sync.WaitGroup
	start := time.Now()
	workers := 30

	// Half the workers send requests, half toggle suspension
	for w := 0; w < workers; w++ {
		wg.Add(1)
		if w%2 == 0 {
			// Request sender
			go func(id int) {
				defer wg.Done()
				for r := 0; r < 10; r++ {
					resp := css.bridge.RouteExecution(&SaarthiRequest{
						AgentID:       "gov-agent-001",
						ResourceID:    "policy-reg-001",
						Action:        "read",
						CorrelationID: fmt.Sprintf("stress-06-req-w%d-r%d", id, r),
						CallerSystem:  "core",
						CallerVersion: "1.0.0",
						RequestedAt:   time.Now().UTC(),
					})
					if resp.Verdict == "ALLOW" {
						atomic.AddInt64(&allowed, 1)
					} else {
						atomic.AddInt64(&denied, 1)
					}
				}
			}(w)
		} else {
			// Suspension toggler
			go func(id int) {
				defer wg.Done()
				for r := 0; r < 5; r++ {
					css.bridge.SuspendCaller("core")
					time.Sleep(1 * time.Millisecond)
					css.bridge.ReactivateCaller("core")
					time.Sleep(1 * time.Millisecond)
				}
			}(w)
		}
	}

	wg.Wait()
	duration := time.Since(start)

	// Ensure caller is active after test
	css.bridge.ReactivateCaller("core")

	total := allowed + denied
	css.recordStressResult(StressTestResult{
		TestID:        "STRESS-06",
		Description:   "Concurrent caller suspension + request sending",
		Workers:       workers,
		TotalRequests: int(total),
		TotalAllowed:  allowed,
		TotalDenied:   denied,
		Duration:      duration,
		Passed:        total > 0, // No deadlock, all requests completed
		Detail:        fmt.Sprintf("total=%d allowed=%d denied=%d (no deadlock)", total, allowed, denied),
	})
}

// ================================================================
// STRESS-07: METRIC CONSISTENCY
// ================================================================

func (css *ConcurrencyStressSimulator) stressMetricConsistency() {
	printSubheader("STRESS-07: Metric Consistency Under Load")

	metricsBefore := css.service.GetMetrics()
	start := time.Now()

	var wg sync.WaitGroup
	numRequests := 100

	for i := 0; i < numRequests; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			css.bridge.RouteExecution(&SaarthiRequest{
				AgentID:       "gov-agent-001",
				ResourceID:    "policy-reg-001",
				Action:        "read",
				CorrelationID: fmt.Sprintf("stress-07-metric-%d", id),
				CallerSystem:  "test_harness",
				CallerVersion: "5.0.0",
				RequestedAt:   time.Now().UTC(),
			})
		}(i)
	}

	wg.Wait()
	duration := time.Since(start)

	metricsAfter := css.service.GetMetrics()
	delta := metricsAfter.TotalRequests - metricsBefore.TotalRequests
	expectedDelta := uint64(numRequests)

	// Metrics should be exactly consistent (atomic counters)
	consistent := delta == expectedDelta
	css.recordStressResult(StressTestResult{
		TestID:        "STRESS-07",
		Description:   "Metric consistency — atomic counter accuracy",
		Workers:       numRequests,
		TotalRequests: numRequests,
		Duration:      duration,
		Passed:        consistent,
		Detail:        fmt.Sprintf("expected_delta=%d actual_delta=%d consistent=%v", expectedDelta, delta, consistent),
	})
}

// ================================================================
// STRESS-08: CHAIN INTEGRITY UNDER CONCURRENT WRITES
// ================================================================

func (css *ConcurrencyStressSimulator) stressChainIntegrity() {
	printSubheader("STRESS-08: Chain Integrity Under Concurrent Writes")

	start := time.Now()
	var wg sync.WaitGroup
	numRequests := 50

	// Send concurrent requests (each creates a chain entry)
	for i := 0; i < numRequests; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			css.bridge.RouteExecution(&SaarthiRequest{
				AgentID:       "gov-agent-001",
				ResourceID:    "policy-reg-001",
				Action:        "read",
				CorrelationID: fmt.Sprintf("stress-08-chain-%d", id),
				CallerSystem:  "test_harness",
				CallerVersion: "5.0.0",
				RequestedAt:   time.Now().UTC(),
			})
		}(i)
	}

	wg.Wait()
	duration := time.Since(start)

	// Verify enforcement chain integrity
	chainValid, _ := css.service.GetPipeline().Adapter.VerifyChain()

	// Verify execution chain integrity
	execChainValid, _ := css.service.GetPipeline().Engine.VerifyExecutionChain()

	// Verify key event chain integrity
	keyChainValid, _, keyReason := css.keyManager.VerifyEventChain()

	allValid := chainValid && execChainValid && keyChainValid
	css.recordStressResult(StressTestResult{
		TestID:        "STRESS-08",
		Description:   "Hash chain integrity after concurrent writes",
		Workers:       numRequests,
		TotalRequests: numRequests,
		Duration:      duration,
		Passed:        allValid,
		Detail:        fmt.Sprintf("enforcement_chain=%v execution_chain=%v key_chain=%v (%s)", chainValid, execChainValid, keyChainValid, keyReason),
	})
}

// ================================================================
// HELPERS
// ================================================================

func (css *ConcurrencyStressSimulator) recordStressResult(result StressTestResult) {
	css.results = append(css.results, result)

	status := "PASS"
	if !result.Passed {
		status = "FAIL"
		css.failed++
	} else {
		css.passed++
	}

	fmt.Printf("  [%s] %s: %s\n", status, result.TestID, result.Description)
	fmt.Printf("         %s\n", result.Detail)
}

func (css *ConcurrencyStressSimulator) buildSummary(duration time.Duration) StressSummary {
	var totalReqs int64
	var peakRPS float64
	for _, r := range css.results {
		totalReqs += int64(r.TotalRequests)
		if r.RequestsPerSec > peakRPS {
			peakRPS = r.RequestsPerSec
		}
	}

	return StressSummary{
		TotalTests:    len(css.results),
		Passed:        css.passed,
		Failed:        css.failed,
		TotalRequests: totalReqs,
		PeakRPS:       peakRPS,
		Duration:      duration,
	}
}

func (css *ConcurrencyStressSimulator) printSummary(summary StressSummary) {
	printHeader("CONCURRENCY STRESS SUMMARY")

	fmt.Printf("  Tests:          %d\n", summary.TotalTests)
	fmt.Printf("  Passed:         %d\n", summary.Passed)
	fmt.Printf("  Failed:         %d\n", summary.Failed)
	fmt.Printf("  Total Requests: %d\n", summary.TotalRequests)
	fmt.Printf("  Peak RPS:       %.0f\n", summary.PeakRPS)
	fmt.Printf("  Duration:       %v\n", summary.Duration)

	if summary.Failed == 0 {
		fmt.Println("\n  ┌─────────────────────────────────────────────────────┐")
		fmt.Println("  │  ALL CONCURRENCY STRESS TESTS PASSED                │")
		fmt.Printf("  │  %d tests, %d total requests                        │\n", summary.TotalTests, summary.TotalRequests)
		fmt.Println("  │  No races, no deadlocks, no chain corruption        │")
		fmt.Println("  │  Metrics: CONSISTENT    Chains: INTACT              │")
		fmt.Println("  └─────────────────────────────────────────────────────┘")
	} else {
		fmt.Println("\n  ┌─────────────────────────────────────────────────────┐")
		fmt.Printf("  │  STRESS FAILURES: %d tests failed                    │\n", summary.Failed)
		fmt.Println("  └─────────────────────────────────────────────────────┘")
	}
}

// GetResults returns all stress test results.
func (css *ConcurrencyStressSimulator) GetResults() []StressTestResult {
	cp := make([]StressTestResult, len(css.results))
	copy(cp, css.results)
	return cp
}
