// cross_machine_telemetry.go (v14.8 Sovereign Authority Closure)
//
// Measures and records the two properties the task.md cross-machine gate
// cares about:
//
//   1. Per-hop HTTP round-trip latency (p50/p99).
//   2. Clock skew between the Sarathi host and each peer host, computed from
//      the peer's /v1/handshake-peer timestamp response vs the Sarathi
//      wall-clock at the moment of the call.
//
// Neither property is allowed to invalidate byte-identity — v14.6 already
// proves canonical hashing is wall-clock-agnostic. This file exists purely
// to SURFACE the observed skew/latency to the reviewer so they can confirm
// that the cross-machine gate held under realistic network conditions.
//
// TAG: sovereign-authority-v14.8

package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"time"
)

// CrossMachineTelemetryLogPath is the append-only telemetry journal.
const CrossMachineTelemetryLogPath = "proof_logs/cross_machine_telemetry.jsonl"

// CrossMachineTelemetrySchema pins the row schema.
const CrossMachineTelemetrySchema = "sarathi.cross-machine.telemetry/v14.8"

// DefaultClockSkewToleranceMs is the max acceptable |skew| between Sarathi
// and any peer before CodeCrossMachineClockSkewExcessive is raised. Override
// via SARATHI_CLOCK_SKEW_TOLERANCE_MS (default: 5000).
const DefaultClockSkewToleranceMs = 5000

// PeerHealthSample is one probe's observations.
type PeerHealthSample struct {
	PeerKind       string `json:"peer_kind"`
	PeerURL        string `json:"peer_url"`
	RTTms          int64  `json:"rtt_ms"`
	SkewMs         int64  `json:"clock_skew_ms"`
	PeerTimestamp  string `json:"peer_timestamp"`
	LocalTimestamp string `json:"local_timestamp"`
	ErrorCode      string `json:"error_code,omitempty"`
	Detail         string `json:"detail,omitempty"`
}

// PeerTelemetry aggregates multiple samples into p50/p99.
type PeerTelemetry struct {
	PeerKind    string  `json:"peer_kind"`
	URL         string  `json:"url"`
	Samples     int     `json:"samples"`
	RTTP50ms    int64   `json:"rtt_p50_ms"`
	RTTP99ms    int64   `json:"rtt_p99_ms"`
	RTTMaxMs    int64   `json:"rtt_max_ms"`
	SkewMs      int64   `json:"clock_skew_ms"` // peer - sarathi (worst)
	SkewMeanMs  int64   `json:"clock_skew_mean_ms"`
	Reachable   bool    `json:"reachable"`
	Pubkey      string  `json:"pubkey,omitempty"`
	ErrorCode   string  `json:"error_code,omitempty"`
	Detail      string  `json:"detail,omitempty"`
}

// CaptureHopLatency probes the peer's /health endpoint samples times and
// records round-trip latency. Writes one PeerHealthSample per probe to the
// cross-machine telemetry log.
func CaptureHopLatency(peerKind, peerURL string, samples int) []PeerHealthSample {
	if samples <= 0 {
		samples = 5
	}
	out := make([]PeerHealthSample, 0, samples)
	client := &http.Client{Timeout: 3 * time.Second}
	for i := 0; i < samples; i++ {
		sample := PeerHealthSample{
			PeerKind:       peerKind,
			PeerURL:        peerURL,
			LocalTimestamp: time.Now().UTC().Format(time.RFC3339Nano),
		}
		start := time.Now()
		resp, err := client.Get(peerURL + "/health")
		if err != nil {
			sample.ErrorCode = CodeCrossMachineUnreachable
			sample.Detail = err.Error()
			_ = appendTelemetryRow(sample)
			out = append(out, sample)
			continue
		}
		sample.RTTms = time.Since(start).Milliseconds()
		_ = resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			sample.ErrorCode = CodeCrossMachineUnreachable
			sample.Detail = fmt.Sprintf("status=%d", resp.StatusCode)
		}
		_ = appendTelemetryRow(sample)
		out = append(out, sample)
	}
	return out
}

// MeasureClockSkew fetches the peer's /health endpoint, parses its
// "started_at" timestamp, and computes the skew from the Sarathi wall-clock
// at the moment of the call. Also extracts the peer public key.
func MeasureClockSkew(peerKind, peerURL string) PeerHealthSample {
	sample := PeerHealthSample{
		PeerKind:       peerKind,
		PeerURL:        peerURL,
		LocalTimestamp: time.Now().UTC().Format(time.RFC3339Nano),
	}
	client := &http.Client{Timeout: 3 * time.Second}
	start := time.Now().UTC()
	resp, err := client.Get(peerURL + "/health")
	if err != nil {
		sample.ErrorCode = CodeCrossMachineUnreachable
		sample.Detail = err.Error()
		return sample
	}
	defer resp.Body.Close()
	sample.RTTms = time.Since(start).Milliseconds()

	body, err := io.ReadAll(io.LimitReader(resp.Body, 64*1024))
	if err != nil {
		sample.ErrorCode = CodeCrossMachineUnreachable
		sample.Detail = "read_health: " + err.Error()
		return sample
	}
	var h map[string]interface{}
	if err := json.Unmarshal(body, &h); err != nil {
		sample.ErrorCode = CodeCrossMachineUnreachable
		sample.Detail = "parse_health: " + err.Error()
		return sample
	}
	if ts, ok := h["started_at"].(string); ok {
		sample.PeerTimestamp = ts
		// Compute skew at mid-point of RTT — the peer's wall-clock at the
		// moment we observed it is approximately startedAt + (peer's
		// own uptime elapsed). Since we don't have a "now" from the peer,
		// we compute the skew against started_at by deriving "peer now" as
		// startedAt + uptime_sec. uptime_sec is typically present in /health.
		if upSec, ok := h["uptime_sec"].(float64); ok {
			peerNow, terr := time.Parse(time.RFC3339Nano, ts)
			if terr == nil {
				peerNow = peerNow.Add(time.Duration(upSec) * time.Second)
				sample.SkewMs = peerNow.Sub(start).Milliseconds()
			}
		}
	}
	if pk, ok := h["pubkey_hex"].(string); ok {
		sample.Detail = "pubkey_hex=" + pk
	}
	return sample
}

// AggregateSamples summarises a list of per-sample observations into a
// single PeerTelemetry row for the distributed report. Samples with errors
// are dropped from the latency percentile; if ALL samples are errors, the
// PeerTelemetry.Reachable is false.
func AggregateSamples(peerKind, url string, samples []PeerHealthSample) PeerTelemetry {
	tel := PeerTelemetry{
		PeerKind: peerKind,
		URL:      url,
		Samples:  len(samples),
	}
	rtts := make([]int64, 0, len(samples))
	skews := make([]int64, 0, len(samples))
	for _, s := range samples {
		if s.ErrorCode != "" {
			if tel.ErrorCode == "" {
				tel.ErrorCode = s.ErrorCode
				tel.Detail = s.Detail
			}
			continue
		}
		rtts = append(rtts, s.RTTms)
		skews = append(skews, s.SkewMs)
	}
	if len(rtts) == 0 {
		tel.Reachable = false
		if tel.ErrorCode == "" {
			tel.ErrorCode = CodeCrossMachineUnreachable
		}
		return tel
	}
	tel.Reachable = true
	sort.Slice(rtts, func(i, j int) bool { return rtts[i] < rtts[j] })
	tel.RTTP50ms = rtts[len(rtts)/2]
	tel.RTTP99ms = rtts[int(float64(len(rtts))*0.99)]
	if tel.RTTP99ms >= int64(len(rtts)) {
		tel.RTTP99ms = rtts[len(rtts)-1]
	}
	tel.RTTMaxMs = rtts[len(rtts)-1]
	if len(skews) > 0 {
		// worst (largest |skew|)
		worst := int64(0)
		sum := int64(0)
		for _, v := range skews {
			abs := v
			if abs < 0 {
				abs = -abs
			}
			if abs > worst {
				worst = v
			}
			sum += v
		}
		tel.SkewMs = worst
		tel.SkewMeanMs = sum / int64(len(skews))
	}
	return tel
}

// ClockSkewTolerated returns true when |skewMs| <= tolerance.
func ClockSkewTolerated(skewMs int64) bool {
	tol := int64(DefaultClockSkewToleranceMs)
	if env := os.Getenv("SARATHI_CLOCK_SKEW_TOLERANCE_MS"); env != "" {
		if v, err := time.ParseDuration(env + "ms"); err == nil {
			tol = v.Milliseconds()
		}
	}
	abs := skewMs
	if abs < 0 {
		abs = -abs
	}
	return abs <= tol
}

func appendTelemetryRow(sample PeerHealthSample) error {
	if err := os.MkdirAll(filepath.Dir(CrossMachineTelemetryLogPath), 0o755); err != nil {
		return err
	}
	row := map[string]interface{}{
		"schema_version": CrossMachineTelemetrySchema,
		"peer_kind":      sample.PeerKind,
		"peer_url":       sample.PeerURL,
		"rtt_ms":         sample.RTTms,
		"clock_skew_ms":  sample.SkewMs,
		"peer_timestamp": sample.PeerTimestamp,
		"local_timestamp": sample.LocalTimestamp,
		"error_code":     sample.ErrorCode,
		"detail":         sample.Detail,
	}
	b, err := json.Marshal(row)
	if err != nil {
		return err
	}
	f, err := os.OpenFile(CrossMachineTelemetryLogPath,
		os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	if _, err := f.Write(append(b, '\n')); err != nil {
		return err
	}
	return f.Sync()
}
