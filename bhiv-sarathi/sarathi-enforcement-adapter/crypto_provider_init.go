package main

// crypto_provider_init.go — Boot-time selector for the CryptoProvider.
//
// SARATHI_CRYPTO_PROVIDER controls which provider the process uses for the
// lifetime of the run. The selector is intentionally minimal: one env var,
// two valid values, fail-closed on anything else.
//
// Default: ed25519 (bit-for-bit identical to v15.6 behaviour).
// Opt-in:   hybrid  (Composite ML-DSA-65 + Ed25519).
//
// Operator workflow:
//
//   1. Edit `live/.env` (or export the variable in the shell).
//   2. Restart Sarathi.
//   3. Boot banner prints provider=<id>; an entry is appended to
//      proof_logs/crypto_provider.jsonl with timestamp + provider id +
//      Sarathi build version.
//   4. Verify peer keys in trust_snapshot.json declare a matching algorithm
//      column; provider-mismatch surfaces at registry lookup time, NOT at
//      first signature verify.
//
// FAIL-CLOSED INVARIANT:
//   A typo, an unknown value, or a missing dependency MUST kill the process
//   on boot. There is no "default to ed25519 on parse error" behaviour —
//   silent downgrades are a CSO-grade incident.
//
// TAG: crypto-agility-v15.7

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"time"
)

// EnvCryptoProvider is the single env var the operator flips.
const EnvCryptoProvider = "SARATHI_CRYPTO_PROVIDER"

// DefaultCryptoProvider is the value used when the env var is empty.
const DefaultCryptoProvider = "ed25519"

// CryptoProviderBootLog is the append-only JSONL audit trail of provider
// initialisations. One row per boot — used by the CRO runbook to confirm
// no silent downgrade ever occurred.
const CryptoProviderBootLog = "proof_logs/crypto_provider.jsonl"

// EnvHybridKeyRotationTag is the rotation suffix appended to composite key
// IDs. Only consulted by cmd_provider_keygen.go.
const EnvHybridKeyRotationTag = "SARATHI_HYBRID_KEY_ROTATION_TAG"

// EnvEd25519KeyRotationTag is the rotation suffix for Ed25519 key IDs.
const EnvEd25519KeyRotationTag = "SARATHI_ED25519_KEY_ROTATION_TAG"

var cryptoProviderInitOnce sync.Once

// InitCryptoProvider must be called exactly once from main(), before any
// signing or verifying code path runs. Subsequent calls are no-ops (a
// production guard against accidental re-init in tests-against-binary).
//
// Returns the selected provider so callers can log/banner it; the same
// value is also stored in the package-level activeProvider singleton.
func InitCryptoProvider() CryptoProvider {
	cryptoProviderInitOnce.Do(func() {
		raw := strings.TrimSpace(strings.ToLower(os.Getenv(EnvCryptoProvider)))
		if raw == "" {
			raw = DefaultCryptoProvider
		}
		var p CryptoProvider
		switch raw {
		case "ed25519":
			p = NewEd25519Provider()
		case "hybrid", "composite", "composite-mldsa65-ed25519":
			p = NewHybridProvider()
		default:
			// FAIL-CLOSED. Do not pick a default. Do not warn-and-continue.
			panic(fmt.Sprintf(
				"crypto_provider: SARATHI_CRYPTO_PROVIDER=%q is not a valid provider id "+
					"(want one of: ed25519, hybrid). The process refuses to boot to prevent "+
					"a silent algorithm downgrade. Edit live/.env and restart.",
				os.Getenv(EnvCryptoProvider),
			))
		}
		activeProvider = p
		appendCryptoProviderBootRow(p)
	})
	return activeProvider
}

// CryptoProviderBootRow is the JSON shape of one boot-log line.
type CryptoProviderBootRow struct {
	Timestamp     string            `json:"timestamp"`
	Algorithm     CryptoAlgorithmID `json:"algorithm"`
	EnvValueSeen  string            `json:"env_value_seen"`
	Hostname      string            `json:"hostname"`
	PID           int               `json:"pid"`
	GoVersion     string            `json:"go_version"`
	SarathiPhase  string            `json:"sarathi_phase"`
	KeyIDTemplate string            `json:"key_id_suffix_template"`
}

func appendCryptoProviderBootRow(p CryptoProvider) {
	host, _ := os.Hostname()
	row := CryptoProviderBootRow{
		Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
		Algorithm:     p.Algorithm(),
		EnvValueSeen:  os.Getenv(EnvCryptoProvider),
		Hostname:      host,
		PID:           os.Getpid(),
		GoVersion:     runtime.Version(),
		SarathiPhase:  "v15.7-crypto-agility",
		KeyIDTemplate: p.KeyIDSuffixTemplate(),
	}
	dir := filepath.Dir(CryptoProviderBootLog)
	if dir != "" && dir != "." {
		_ = os.MkdirAll(dir, 0o755)
	}
	f, err := os.OpenFile(CryptoProviderBootLog, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		// Audit failure does NOT block boot — the banner still surfaces the
		// provider id, and the operator notices the missing log file. This
		// is consistent with how peer_common.go handles best-effort logs.
		fmt.Fprintf(os.Stderr, "[crypto_provider] WARN: boot log open failed: %v\n", err)
		return
	}
	defer f.Close()
	line := fmt.Sprintf(
		`{"timestamp":%q,"algorithm":%q,"env_value_seen":%q,"hostname":%q,`+
			`"pid":%d,"go_version":%q,"sarathi_phase":%q,"key_id_suffix_template":%q}`+"\n",
		row.Timestamp, string(row.Algorithm), row.EnvValueSeen, row.Hostname,
		row.PID, row.GoVersion, row.SarathiPhase, row.KeyIDTemplate,
	)
	_, _ = f.WriteString(line)
}

// CryptoProviderBanner returns a single-line summary suitable for the boot
// banner. Mounts under [crypto] tag for grep-ability in tee'd logs.
func CryptoProviderBanner(p CryptoProvider) string {
	envRaw := os.Getenv(EnvCryptoProvider)
	if envRaw == "" {
		envRaw = "(unset → default ed25519)"
	}
	return fmt.Sprintf("[crypto] provider=%s env=%s key_id_suffix=%q",
		p.Algorithm(), envRaw, p.KeyIDSuffixTemplate())
}
