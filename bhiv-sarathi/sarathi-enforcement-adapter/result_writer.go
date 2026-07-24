package main

// result_writer.go — Canonical Result File Writer.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Result Canonicalization (v14.4)
// Host Organization: Blackhole Infiverse (BHIV)
//
// PURPOSE:
//   Wraps all test/attack/simulation result JSON files with a canonical
//   envelope containing schema_version, timestamp, test category, and
//   pass/fail counts. Ensures consistent format across all result files.

import (
	"encoding/json"
	"fmt"
	"os"
	"time"
)

// ResultSchemaVersion is the canonical version for result envelopes.
const ResultSchemaVersion = "sarathi.results/v1.0"

// CanonicalResultEnvelope wraps any test result set with standard metadata.
type CanonicalResultEnvelope struct {
	SchemaVersion string      `json:"schema_version"`
	GeneratedAt   string      `json:"generated_at"`
	SystemVersion string      `json:"system_version"`
	TestCategory  string      `json:"test_category"`
	TotalTests    int         `json:"total_tests"`
	Passed        int         `json:"passed"`
	Failed        int         `json:"failed"`
	Results       interface{} `json:"results"`
}

// WriteCanonicalResults writes a test result set to a JSON file wrapped in
// the canonical envelope. Returns nil on success.
func WriteCanonicalResults(filename, category string, total, passed, failed int, results interface{}) error {
	envelope := CanonicalResultEnvelope{
		SchemaVersion: ResultSchemaVersion,
		GeneratedAt:   time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		SystemVersion: "v14.4",
		TestCategory:  category,
		TotalTests:    total,
		Passed:        passed,
		Failed:        failed,
		Results:       results,
	}

	data, err := json.MarshalIndent(envelope, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal %s results: %w", category, err)
	}

	if err := os.WriteFile(filename, data, 0644); err != nil {
		return fmt.Errorf("failed to write %s: %w", filename, err)
	}

	fmt.Printf("  [OK] %s generated: %d/%d passed (%s)\n", filename, passed, total, category)
	return nil
}

// DeterministicReplayResult holds the result of a single replay comparison.
type DeterministicReplayResult struct {
	TestName         string            `json:"test_name"`
	Input            map[string]string `json:"input"`
	Passed           bool              `json:"passed"`
	DeterministicFields map[string]bool `json:"deterministic_fields"`
	MismatchedFields []string          `json:"mismatched_fields,omitempty"`
	Run1Verdict      string            `json:"run1_verdict"`
	Run2Verdict      string            `json:"run2_verdict"`
	Run1ErrorCode    string            `json:"run1_error_code"`
	Run2ErrorCode    string            `json:"run2_error_code"`
}

// RunDeterministicReplayTests runs the same inputs through the pipeline twice
// and compares deterministic fields to prove reproducibility.
func RunDeterministicReplayTests(pipeline *SarathiEnforcementPipeline) (int, int, []DeterministicReplayResult) {
	printHeader("DETERMINISTIC REPLAY TEST (Gap F)")
	fmt.Println("  Proving: SAME input → SAME deterministic output across runs")
	fmt.Println()

	results := make([]DeterministicReplayResult, 0)
	passed := 0
	total := 0

	// Test cases: mix of ALLOW, DENY, and edge cases
	testCases := []struct {
		name      string
		agentID   string
		resource  string
		action    string
		corrID    string
	}{
		{"ALLOW_replay", "gov-agent-001", "policy-reg-001", "read", "replay-allow-001"},
		{"DENY_unknown_agent", "ghost-agent-999", "ops-data-001", "read", "replay-deny-001"},
		{"DENY_classification", "std-agent-003", "config-001", "read", "replay-class-001"},
		{"DENY_invalid_action", "gov-agent-001", "policy-reg-001", "destroy", "replay-action-001"},
	}

	// Deterministic fields that MUST match between runs
	deterministicFields := []string{
		"verdict", "error_code", "execution_state", "schema_version",
	}

	for _, tc := range testCases {
		total++
		fmt.Printf("  [REPLAY] %s: ", tc.name)

		run1 := pipeline.Execute(tc.agentID, tc.resource, tc.action, tc.corrID)
		run2 := pipeline.Execute(tc.agentID, tc.resource, tc.action, tc.corrID)

		result := DeterministicReplayResult{
			TestName: tc.name,
			Input: map[string]string{
				"agent_id":    tc.agentID,
				"resource_id": tc.resource,
				"action":      tc.action,
			},
			DeterministicFields: make(map[string]bool),
		}

		// Extract string values safely
		getStr := func(m map[string]interface{}, key string) string {
			if v, ok := m[key]; ok {
				if s, ok := v.(string); ok {
					return s
				}
			}
			return ""
		}

		result.Run1Verdict = getStr(run1, "verdict")
		result.Run2Verdict = getStr(run2, "verdict")
		result.Run1ErrorCode = getStr(run1, "error_code")
		result.Run2ErrorCode = getStr(run2, "error_code")

		allMatch := true
		for _, field := range deterministicFields {
			v1 := getStr(run1, field)
			v2 := getStr(run2, field)
			match := v1 == v2
			result.DeterministicFields[field] = match
			if !match {
				allMatch = false
				result.MismatchedFields = append(result.MismatchedFields, field)
			}
		}

		// Also compare request hash (must be identical for same input)
		if reqMap1, ok := run1["request"].(map[string]interface{}); ok {
			if reqMap2, ok := run2["request"].(map[string]interface{}); ok {
				rh1 := getStr(reqMap1, "request_hash")
				rh2 := getStr(reqMap2, "request_hash")
				match := rh1 == rh2
				result.DeterministicFields["request.request_hash"] = match
				if !match {
					allMatch = false
					result.MismatchedFields = append(result.MismatchedFields, "request.request_hash")
				}
			}
		}

		result.Passed = allMatch
		if allMatch {
			passed++
			fmt.Printf("PASS (verdict=%s, error_code=%s)\n", result.Run1Verdict, result.Run1ErrorCode)
		} else {
			fmt.Printf("FAIL (mismatched: %v)\n", result.MismatchedFields)
		}
		results = append(results, result)
	}

	fmt.Printf("\n  Replay Tests: %d/%d PASSED\n", passed, total)

	// Write results
	_ = WriteCanonicalResults("deterministic_replay_results.json",
		"deterministic_replay", total, passed, total-passed, results)

	return passed, total, results
}
