package main

// peer_key_registry_test.go — end-to-end tests for the v15.9 peer-key
// registry, the receipt-replay store, and the integrated VerifyReceipt gates.
//
// Every test runs against the REAL `peer_common.go::VerifyReceipt` — no
// mocks, no stubs. The signature is produced by the real `PeerReceiptSigner`
// (stdlib Ed25519), the canonical JSON is the real `canonical_json.go`, the
// pinning + replay gates are the real package-level singletons.
//
// TAG: peer-key-registry-v15.9

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"testing"
	"time"
)

// helperFreshKeypair returns (pub_hex, signer) for use in test fixtures.
func helperFreshKeypair(t *testing.T) (string, *PeerReceiptSigner) {
	t.Helper()
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("ed25519 keygen: %v", err)
	}
	return hex.EncodeToString(pub), &PeerReceiptSigner{pub: pub, priv: priv}
}

// helperBuildReceipt builds a fully-signed PeerReceipt for the given peer
// using the supplied signer. Returns the canonical wire bytes.
func helperBuildReceipt(t *testing.T, peer string, signer *PeerReceiptSigner) []byte {
	t.Helper()
	r := &PeerReceipt{
		Peer:             peer,
		ExecutionID:      "EXEC-TEST-" + peer,
		DecisionID:       "DEC-TEST-" + peer,
		ResponseHash:     "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
		ReceivedBodyHash: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
		ChainBindingHash: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
		PersistedAt:      time.Now().UTC().Format(time.RFC3339Nano),
		StoragePath:      "test/" + peer,
	}
	raw, err := signer.Sign(r)
	if err != nil {
		t.Fatalf("sign receipt: %v", err)
	}
	return raw
}

func TestPeerKeyRegistry_RelaxedMode_NoEntry_AcceptsTOFU(t *testing.T) {
	SetActivePeerKeyRegistryForTest(&PeerKeyRegistry{
		byPeer: map[string]*PeerKeyEntry{},
		mode:   PeerKeyPinningRelaxed,
	})
	SetActivePeerReceiptReplayStoreForTest(NewTestReplayStore())
	defer SetActivePeerKeyRegistryForTest(nil)
	defer SetActivePeerReceiptReplayStoreForTest(nil)

	_, signer := helperFreshKeypair(t)
	raw := helperBuildReceipt(t, "bucket", signer)

	_, ok, reason := VerifyReceipt(raw)
	if !ok {
		t.Fatalf("relaxed-mode TOFU should accept: %s", reason)
	}
}

func TestPeerKeyRegistry_StrictMode_NoEntry_Rejects(t *testing.T) {
	SetActivePeerKeyRegistryForTest(&PeerKeyRegistry{
		byPeer: map[string]*PeerKeyEntry{},
		mode:   PeerKeyPinningStrict,
	})
	SetActivePeerReceiptReplayStoreForTest(NewTestReplayStore())
	defer SetActivePeerKeyRegistryForTest(nil)
	defer SetActivePeerReceiptReplayStoreForTest(nil)

	_, signer := helperFreshKeypair(t)
	raw := helperBuildReceipt(t, "bucket", signer)

	_, ok, reason := VerifyReceipt(raw)
	if ok {
		t.Fatalf("strict-mode unregistered peer should reject")
	}
	if !peerKeyTestContains(reason, "no registered key") || !peerKeyTestContains(reason, "strict") {
		t.Errorf("unexpected reason: %s", reason)
	}
}

func TestPeerKeyRegistry_RegisteredAndMatching_Accepts(t *testing.T) {
	pubHex, signer := helperFreshKeypair(t)
	SetActivePeerKeyRegistryForTest(&PeerKeyRegistry{
		byPeer: map[string]*PeerKeyEntry{
			"bucket": {
				Peer:         "bucket",
				Status:       PeerKeyStatusActive,
				PublicKeyHex: pubHex,
			},
		},
		mode: PeerKeyPinningStrict,
	})
	SetActivePeerReceiptReplayStoreForTest(NewTestReplayStore())
	defer SetActivePeerKeyRegistryForTest(nil)
	defer SetActivePeerReceiptReplayStoreForTest(nil)

	raw := helperBuildReceipt(t, "bucket", signer)
	_, ok, reason := VerifyReceipt(raw)
	if !ok {
		t.Fatalf("registered-and-matching should accept: %s", reason)
	}
}

func TestPeerKeyRegistry_RegisteredButMismatchedKey_Rejects(t *testing.T) {
	// The registry has key A; the receipt is signed by (and embeds) key B.
	otherPub, _ := helperFreshKeypair(t)
	SetActivePeerKeyRegistryForTest(&PeerKeyRegistry{
		byPeer: map[string]*PeerKeyEntry{
			"bucket": {
				Peer:         "bucket",
				Status:       PeerKeyStatusActive,
				PublicKeyHex: otherPub, // not the signer's key
			},
		},
		mode: PeerKeyPinningRelaxed,
	})
	SetActivePeerReceiptReplayStoreForTest(NewTestReplayStore())
	defer SetActivePeerKeyRegistryForTest(nil)
	defer SetActivePeerReceiptReplayStoreForTest(nil)

	_, signer := helperFreshKeypair(t)
	raw := helperBuildReceipt(t, "bucket", signer)

	_, ok, reason := VerifyReceipt(raw)
	if ok {
		t.Fatalf("mismatched key should reject")
	}
	if !peerKeyTestContains(reason, "does not match registered key") {
		t.Errorf("unexpected reason: %s", reason)
	}
}

func TestPeerKeyRegistry_SuspendedPeer_Rejects(t *testing.T) {
	pubHex, signer := helperFreshKeypair(t)
	SetActivePeerKeyRegistryForTest(&PeerKeyRegistry{
		byPeer: map[string]*PeerKeyEntry{
			"bucket": {
				Peer:         "bucket",
				Status:       PeerKeyStatusSuspended,
				PublicKeyHex: pubHex,
			},
		},
		mode: PeerKeyPinningStrict,
	})
	SetActivePeerReceiptReplayStoreForTest(NewTestReplayStore())
	defer SetActivePeerKeyRegistryForTest(nil)
	defer SetActivePeerReceiptReplayStoreForTest(nil)

	raw := helperBuildReceipt(t, "bucket", signer)
	_, ok, reason := VerifyReceipt(raw)
	if ok {
		t.Fatalf("suspended peer should reject even with matching key")
	}
	if !peerKeyTestContains(reason, "SUSPENDED") || !peerKeyTestContains(reason, "must be ACTIVE") {
		t.Errorf("unexpected reason: %s", reason)
	}
}

func TestPeerKeyRegistry_CrossPeerImpersonation_Rejects(t *testing.T) {
	// Attacker holds InsightFlow's private key. They forge a receipt
	// CLAIMING peer="bucket" but signing with the InsightFlow key. The
	// signature internally verifies, but pinning must reject because the
	// bucket registry entry expects a DIFFERENT key.
	bucketPub, _ := helperFreshKeypair(t)
	insightPub, insightSigner := helperFreshKeypair(t)
	_ = insightPub

	SetActivePeerKeyRegistryForTest(&PeerKeyRegistry{
		byPeer: map[string]*PeerKeyEntry{
			"bucket": {
				Peer:         "bucket",
				Status:       PeerKeyStatusActive,
				PublicKeyHex: bucketPub,
			},
			"insightflow": {
				Peer:         "insightflow",
				Status:       PeerKeyStatusActive,
				PublicKeyHex: insightPub,
			},
		},
		mode: PeerKeyPinningStrict,
	})
	SetActivePeerReceiptReplayStoreForTest(NewTestReplayStore())
	defer SetActivePeerKeyRegistryForTest(nil)
	defer SetActivePeerReceiptReplayStoreForTest(nil)

	// Attacker forges a "bucket" receipt with insightflow's signer.
	raw := helperBuildReceipt(t, "bucket", insightSigner)
	_, ok, reason := VerifyReceipt(raw)
	if ok {
		t.Fatalf("cross-peer impersonation should reject")
	}
	if !peerKeyTestContains(reason, "does not match registered key") {
		t.Errorf("unexpected reason: %s", reason)
	}
}

func TestPeerKeyRegistry_UnknownPeerKind_Rejects(t *testing.T) {
	SetActivePeerKeyRegistryForTest(&PeerKeyRegistry{
		byPeer: map[string]*PeerKeyEntry{},
		mode:   PeerKeyPinningRelaxed,
	})
	SetActivePeerReceiptReplayStoreForTest(NewTestReplayStore())
	defer SetActivePeerKeyRegistryForTest(nil)
	defer SetActivePeerReceiptReplayStoreForTest(nil)

	_, signer := helperFreshKeypair(t)
	raw := helperBuildReceipt(t, "evil_attacker", signer)
	_, ok, reason := VerifyReceipt(raw)
	if ok {
		t.Fatalf("unknown peer kind should reject")
	}
	if !peerKeyTestContains(reason, "evil_attacker") || !peerKeyTestContains(reason, "not one of") {
		t.Errorf("unexpected reason: %s", reason)
	}
}

func TestPeerReceiptReplay_DuplicateRejected(t *testing.T) {
	pubHex, signer := helperFreshKeypair(t)
	SetActivePeerKeyRegistryForTest(&PeerKeyRegistry{
		byPeer: map[string]*PeerKeyEntry{
			"bucket": {
				Peer:         "bucket",
				Status:       PeerKeyStatusActive,
				PublicKeyHex: pubHex,
			},
		},
		mode: PeerKeyPinningStrict,
	})
	SetActivePeerReceiptReplayStoreForTest(NewTestReplayStore())
	defer SetActivePeerKeyRegistryForTest(nil)
	defer SetActivePeerReceiptReplayStoreForTest(nil)

	raw := helperBuildReceipt(t, "bucket", signer)
	if _, ok, _ := VerifyReceipt(raw); !ok {
		t.Fatal("first verify should accept")
	}
	_, ok, reason := VerifyReceipt(raw)
	if ok {
		t.Fatal("second verify (replay) should reject")
	}
	if !peerKeyTestContains(reason, "peer_receipt_replay") {
		t.Errorf("unexpected reason: %s", reason)
	}
}

func TestPeerKeyRegistry_ConstantTimeHexEqual(t *testing.T) {
	a := "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
	if !constantTimeHexEqual(a, a) {
		t.Error("identical hex should compare equal")
	}
	if !constantTimeHexEqual(a, "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF") {
		t.Error("case-insensitive comparison should compare equal")
	}
	b := "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdee"
	if constantTimeHexEqual(a, b) {
		t.Error("differing keys should NOT compare equal")
	}
	if constantTimeHexEqual("zzzz", "yyyy") {
		t.Error("malformed hex must NOT compare equal")
	}
}

func TestPeerKeyRegistry_ValidatePeerKeyEntryShape(t *testing.T) {
	good := []PeerKeyEntry{
		{Peer: "bucket", PublicKeyHex: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", Status: "ACTIVE"},
		{Peer: "core", PublicKeyHex: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
		{Peer: "insightflow", PublicKeyHex: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", Status: "SUSPENDED"},
	}
	for i := range good {
		if err := validatePeerKeyEntryShape(&good[i]); err != nil {
			t.Errorf("good entry %d rejected: %v", i, err)
		}
	}
	bad := []PeerKeyEntry{
		{Peer: "", PublicKeyHex: "00"},
		{Peer: "evil", PublicKeyHex: "00"},
		{Peer: "bucket", PublicKeyHex: "not-hex"},
		{Peer: "bucket", PublicKeyHex: "00"},
		{Peer: "bucket", PublicKeyHex: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", Status: "BOGUS"},
	}
	for i := range bad {
		if err := validatePeerKeyEntryShape(&bad[i]); err == nil {
			t.Errorf("bad entry %d accepted (peer=%q)", i, bad[i].Peer)
		}
	}
}

// NewTestReplayStore is a small helper because the production
// BootstrapPeerReceiptReplayStore writes to a package singleton; tests want
// a fresh instance each time.
func NewTestReplayStore() PeerReceiptReplayStore {
	return &memoryPeerReceiptReplayStore{
		bySig:  make(map[string]time.Time),
		ttl:    time.Duration(PeerReceiptReplayTTLSeconds) * time.Second,
		maxLen: 1024,
	}
}

func peerKeyTestContains(haystack, needle string) bool {
	if len(needle) == 0 {
		return true
	}
	for i := 0; i+len(needle) <= len(haystack); i++ {
		if haystack[i:i+len(needle)] == needle {
			return true
		}
	}
	return false
}
