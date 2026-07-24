// node_id_clock_env.go (v14.6 Global Determinism Validation)
//
// Shared helpers for the v14.6 distributed-determinism harnesses. Three
// primitives are exported:
//
//   - parseNodeIDFromEnv reads SARATHI_NODE_ID (defaults to "default") so
//     each multi-node child process knows its own identity when it writes
//     per-node artefacts (propagation_byte_equality_report_<id>.json).
//
//   - parseClockSkewFromEnv reads SARATHI_CLOCK_SKEW_SECONDS (defaults to
//     0). The value is interpreted as a signed integer number of seconds
//     applied to every Clock.NowUTC() read inside the process.
//
//   - SkewedClock wraps the existing Clock interface (clock.go) with a
//     fixed time offset. It is used by the clock-drift harness to prove
//     that ProduceStableEnvelope zeroes out timestamp-bearing fields.
//
// No production code path reads these env vars — they are activated only
// under the v14.6 CLI sub-commands. The zero-value defaults preserve v14.5
// behaviour when the vars are unset.
//
// TAG: test-affordance-only

package main

import (
	"os"
	"strconv"
	"strings"
	"time"
)

// EnvNodeID is the process-local node identifier for multi-node runs.
const EnvNodeID = "SARATHI_NODE_ID"

// EnvClockSkewSeconds is the signed offset in seconds applied to SkewedClock.
const EnvClockSkewSeconds = "SARATHI_CLOCK_SKEW_SECONDS"

// DefaultNodeID is returned when SARATHI_NODE_ID is unset or empty.
const DefaultNodeID = "default"

// parseNodeIDFromEnv returns the value of SARATHI_NODE_ID, or DefaultNodeID
// when the variable is absent or empty. Leading/trailing whitespace is
// stripped so shell-escaping artefacts don't bleed into artefact names.
func parseNodeIDFromEnv() string {
	v := strings.TrimSpace(os.Getenv(EnvNodeID))
	if v == "" {
		return DefaultNodeID
	}
	return v
}

// parseClockSkewFromEnv returns the signed integer number of seconds from
// SARATHI_CLOCK_SKEW_SECONDS. Invalid or missing values yield 0 (no skew).
func parseClockSkewFromEnv() time.Duration {
	v := strings.TrimSpace(os.Getenv(EnvClockSkewSeconds))
	if v == "" {
		return 0
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return 0
	}
	return time.Duration(n) * time.Second
}

// SkewedClock is an injectable Clock implementation that adds a fixed
// offset to wall-clock time. A positive Offset makes the clock read
// "into the future"; a negative Offset reads into the past.
//
// Instances are safe for concurrent use — time.Now() is goroutine-safe
// and Offset is read-only after construction.
type SkewedClock struct {
	Offset time.Duration
}

// NowUTC satisfies the Clock interface (clock.go). Returns the real
// system time in UTC plus the configured offset.
func (c SkewedClock) NowUTC() time.Time {
	return time.Now().UTC().Add(c.Offset)
}

// NewSkewedClockFromEnv constructs a SkewedClock using SARATHI_CLOCK_SKEW_SECONDS.
// When the env var is unset it returns SkewedClock{Offset: 0} which is behaviourally
// equivalent to RealClock for the purposes of NowUTC().
func NewSkewedClockFromEnv() SkewedClock {
	return SkewedClock{Offset: parseClockSkewFromEnv()}
}
