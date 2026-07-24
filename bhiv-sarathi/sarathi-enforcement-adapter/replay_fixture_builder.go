// replay_fixture_builder.go (v14.5 Cross-System Propagation Layer)
//
// Builds (and caches to disk) a DETERMINISTIC PDP replay fixture so the
// propagation replay harness can prove byte-equality across iterations.
//
// Determinism comes from:
//   - Ed25519 key pair derived from a FIXED seed (ReplayFixtureEvaluatorSeed)
//   - Fixed timestamp, fixed nonce, fixed decision_id
//   - Computed hashes (DecisionHash, DecisionCoreHash) — self-consistent
//   - Ed25519 signature over DecisionCoreHash is deterministic given fixed key + message
//
// Output: fixtures/pdp_replay_fixture.json — a signed ExternalDecision, byte-
// identical across runs. If the file exists on disk and its bytes parse to
// a valid fixture, BuildOrLoadReplayFixture reuses those bytes; otherwise it
// regenerates them and writes a fresh file.
//
// IMPORTANT: the fixture evaluator (id "replay-fixture-evaluator") MUST be
// registered with the EnforcementAdapter's trust registry before Ingest() is
// called; the builder exposes its public key for that purpose.

package main

import (
	"crypto/ed25519"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"
)

// ReplayFixtureEvaluatorID is the trust-registry ID for the replay fixture
// evaluator. The fixture decision is signed by the key derived from
// ReplayFixtureEvaluatorSeed.
const ReplayFixtureEvaluatorID = "replay-fixture-evaluator"

// ReplayFixtureEvaluatorSeed seeds the deterministic Ed25519 key used to sign
// the replay fixture. MUST be exactly ed25519.SeedSize (32) bytes. Any value
// works as long as it's fixed — this is a test-only artifact.
var ReplayFixtureEvaluatorSeed = []byte("sarathi-replay-fixture-seed-v14-5")

// ReplayFixtureDecisionID is the fixed decision_id in the fixture.
const ReplayFixtureDecisionID = "DEC-REPLAY-FIXTURE-0001"

// ReplayFixtureNonce is the fixed nonce in the fixture.
const ReplayFixtureNonce = "NONCE-REPLAY-FIXTURE-0001"

// ReplayFixtureTimestamp is the fixed RFC3339 timestamp in the fixture.
// Chosen in the past so expiry logic at replay time is independent of runtime
// clocks (the fixture TTL is set large to cover test runs; for ALLOW paths
// TTL is enforced so we keep it generous).
const ReplayFixtureTimestamp = "2026-01-01T00:00:00.000000Z"

// ReplayFixturePath is the on-disk location of the fixture.
const ReplayFixturePath = "fixtures/pdp_replay_fixture.json"

// ReplayFixture bundles the fixture bytes with the signing keypair so the
// caller can register the evaluator before Ingest().
type ReplayFixture struct {
	Bytes       []byte
	PublicKey   ed25519.PublicKey
	PrivateKey  ed25519.PrivateKey
	EvaluatorID string
	DecisionID  string
}

// BuildOrLoadReplayFixture returns a deterministic signed ExternalDecision.
// If ReplayFixturePath exists and decodes to a valid-hash fixture, those
// bytes are returned verbatim. Otherwise a fresh fixture is built and written.
// The evaluator public key is always returned — register it with the trust
// registry before the fixture can be ingested.
func BuildOrLoadReplayFixture() (*ReplayFixture, error) {
	priv, pub, err := deriveReplayKey()
	if err != nil {
		return nil, err
	}

	// Attempt disk reuse first.
	if b, err := os.ReadFile(ReplayFixturePath); err == nil && len(b) > 0 {
		// Validate the cached file: must unmarshal and its decision_hash +
		// decision_core_hash must recompute correctly. If not, regenerate.
		d := &ExternalDecision{}
		if jerr := json.Unmarshal(b, d); jerr == nil && d.VerifyIntegrity() && d.VerifyCoreHashIntegrity() {
			// Also verify the signature is valid under the derived pubkey.
			if ok, _ := d.VerifySignature(pub); ok {
				return &ReplayFixture{
					Bytes:       b,
					PublicKey:   pub,
					PrivateKey:  priv,
					EvaluatorID: d.EvaluatorID,
					DecisionID:  d.DecisionID,
				}, nil
			}
		}
	}

	// Build fresh.
	fx, err := buildReplayFixtureBytes(priv, pub)
	if err != nil {
		return nil, err
	}

	// Persist for cross-run byte stability.
	if err := writeFixture(ReplayFixturePath, fx.Bytes); err != nil {
		return nil, fmt.Errorf("replay_fixture: write %s: %w", ReplayFixturePath, err)
	}
	return fx, nil
}

// deriveReplayKey derives (or re-derives) the Ed25519 key pair from the
// deterministic seed. Any call with the same seed returns the identical key.
func deriveReplayKey() (ed25519.PrivateKey, ed25519.PublicKey, error) {
	seed := make([]byte, ed25519.SeedSize)
	if len(ReplayFixtureEvaluatorSeed) < ed25519.SeedSize {
		return nil, nil, fmt.Errorf("replay_fixture: seed too short (%d bytes, need %d)",
			len(ReplayFixtureEvaluatorSeed), ed25519.SeedSize)
	}
	copy(seed, ReplayFixtureEvaluatorSeed[:ed25519.SeedSize])
	priv := ed25519.NewKeyFromSeed(seed)
	pub, ok := priv.Public().(ed25519.PublicKey)
	if !ok {
		return nil, nil, fmt.Errorf("replay_fixture: failed to derive public key")
	}
	return priv, pub, nil
}

// buildReplayFixtureBytes constructs the decision struct with fixed fields,
// computes hashes, signs with the derived private key, and marshals it.
func buildReplayFixtureBytes(priv ed25519.PrivateKey, pub ed25519.PublicKey) (*ReplayFixture, error) {
	ts, err := time.Parse("2006-01-02T15:04:05.000000Z", ReplayFixtureTimestamp)
	if err != nil {
		return nil, fmt.Errorf("replay_fixture: timestamp parse: %w", err)
	}

	// Use agent/resource IDs that exist in the default RegistryInterface
	// (registry_interface.go:40-82) so enforcement does not fail on lookup.
	d := &ExternalDecision{
		DecisionID:  ReplayFixtureDecisionID,
		EvaluatorID: ReplayFixtureEvaluatorID,
		AgentID:     "gov-agent-001",
		ResourceID:  "policy-reg-001",
		Action:      "read",
		Verdict:     ExternalVerdictAllow,
		Obligations: []string{},
		Timestamp:   ts,
		TTL:         365 * 24 * time.Hour, // long TTL — fixture never expires within test runs
		ExpiresAt:   ts.Add(365 * 24 * time.Hour),
		Metadata:    map[string]string{"fixture": "replay", "version": "v14.5"},
		Reason:      "Replay fixture — deterministic byte-equality test",
		Nonce:       ReplayFixtureNonce,
	}
	d.DecisionHash = d.computeHash()
	d.DecisionCoreHash = d.computeCoreHash()
	d.SignDecision(priv)

	b, err := json.Marshal(d)
	if err != nil {
		return nil, fmt.Errorf("replay_fixture: marshal: %w", err)
	}
	return &ReplayFixture{
		Bytes:       b,
		PublicKey:   pub,
		PrivateKey:  priv,
		EvaluatorID: d.EvaluatorID,
		DecisionID:  d.DecisionID,
	}, nil
}

// writeFixture writes bytes to path atomically (via a temp file + rename).
// Creates the parent directory if it doesn't exist.
func writeFixture(path string, data []byte) error {
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	tmp := path + ".tmp"
	f, err := os.Create(tmp)
	if err != nil {
		return err
	}
	if _, err := io.Copy(f, newByteReader(data)); err != nil {
		_ = f.Close()
		_ = os.Remove(tmp)
		return err
	}
	if err := f.Close(); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	return os.Rename(tmp, path)
}

// byteReader is a minimal io.Reader over a []byte, used by writeFixture to
// avoid pulling in bytes.NewReader in this file (keeps imports minimal).
type byteReader struct {
	b   []byte
	pos int
}

func newByteReader(b []byte) *byteReader { return &byteReader{b: b} }

func (r *byteReader) Read(p []byte) (int, error) {
	if r.pos >= len(r.b) {
		return 0, io.EOF
	}
	n := copy(p, r.b[r.pos:])
	r.pos += n
	return n, nil
}
