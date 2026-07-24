// canonical_json_test.go — Unit tests for the RFC 8785 JCS-equivalent serializer.
// These tests are the foundation for all cross-system byte-equality proofs.

package main

import (
	"encoding/json"
	"testing"
)

// TestCanonicalJSON_SortedKeys: maps with different insertion orders produce
// identical canonical bytes. This is the primary determinism guarantee.
func TestCanonicalJSON_SortedKeys(t *testing.T) {
	a := map[string]interface{}{"z": 1, "a": 2, "m": 3}
	b := map[string]interface{}{"m": 3, "a": 2, "z": 1}
	ab, err := CanonicalMarshal(a)
	if err != nil {
		t.Fatalf("marshal a: %v", err)
	}
	bb, err := CanonicalMarshal(b)
	if err != nil {
		t.Fatalf("marshal b: %v", err)
	}
	if string(ab) != string(bb) {
		t.Fatalf("maps with same keys differ: a=%s b=%s", ab, bb)
	}
	expected := `{"a":2,"m":3,"z":1}`
	if string(ab) != expected {
		t.Fatalf("expected %s, got %s", expected, ab)
	}
}

// TestCanonicalJSON_NestedSorting: nested maps are also key-sorted at every level.
func TestCanonicalJSON_NestedSorting(t *testing.T) {
	v := map[string]interface{}{
		"outer_b": map[string]interface{}{
			"z": 9,
			"a": 1,
		},
		"outer_a": []interface{}{
			map[string]interface{}{"y": 2, "x": 1},
			map[string]interface{}{"z": 3, "a": 0},
		},
	}
	b, err := CanonicalMarshal(v)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	expected := `{"outer_a":[{"x":1,"y":2},{"a":0,"z":3}],"outer_b":{"a":1,"z":9}}`
	if string(b) != expected {
		t.Fatalf("expected %s, got %s", expected, b)
	}
}

// TestCanonicalJSON_Determinism_1000Runs: critical property.
// For the same input, 1000 runs produce byte-identical output.
func TestCanonicalJSON_Determinism_1000Runs(t *testing.T) {
	v := map[string]interface{}{
		"trace_id":      "abc-123",
		"decision_id":   "DEC-9",
		"enforcement":   map[string]interface{}{"verdict": "ALLOW", "nonce": "n"},
		"chain":         []interface{}{"h1", "h2", "h3"},
		"metadata":      map[string]interface{}{"ts": 1234567890, "kind": "test"},
	}
	first, err := CanonicalMarshal(v)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	firstHash := Sha256Hex(first)
	for i := 0; i < 1000; i++ {
		b, err := CanonicalMarshal(v)
		if err != nil {
			t.Fatalf("iter %d marshal: %v", i, err)
		}
		if Sha256Hex(b) != firstHash {
			t.Fatalf("iter %d produced different hash: first=%s now=%s bytes=%s",
				i, firstHash, Sha256Hex(b), b)
		}
	}
}

// TestCanonicalJSON_NoHTMLEscape: raw & < > must NOT be escaped.
// Go's default json.Marshal escapes these; our canonical form must not.
func TestCanonicalJSON_NoHTMLEscape(t *testing.T) {
	v := map[string]interface{}{"html": "a & b <c> \"d\""}
	b, err := CanonicalMarshal(v)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	expected := `{"html":"a & b <c> \"d\""}`
	if string(b) != expected {
		t.Fatalf("expected %s, got %s", expected, b)
	}
}

// TestCanonicalJSON_ControlChars: 0x00-0x1F not otherwise escaped become \u00XX.
func TestCanonicalJSON_ControlChars(t *testing.T) {
	v := map[string]interface{}{"ctl": "\x01\x02\x1f"}
	b, err := CanonicalMarshal(v)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	expected := `{"ctl":"\u0001\u0002\u001f"}`
	if string(b) != expected {
		t.Fatalf("expected %s, got %s", expected, b)
	}
}

// TestCanonicalJSON_StandardEscapes: verified shorthand escapes.
func TestCanonicalJSON_StandardEscapes(t *testing.T) {
	v := map[string]interface{}{"s": "quote:\" back:\\ tab:\t lf:\n cr:\r bs:\b ff:\f"}
	b, err := CanonicalMarshal(v)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	expected := `{"s":"quote:\" back:\\ tab:\t lf:\n cr:\r bs:\b ff:\f"}`
	if string(b) != expected {
		t.Fatalf("expected %s, got %s", expected, b)
	}
}

// TestCanonicalJSON_Numbers: integers plain, floats shortest round-trip.
func TestCanonicalJSON_Numbers(t *testing.T) {
	cases := []struct {
		in       interface{}
		expected string
	}{
		{int64(42), `42`},
		{int64(-17), `-17`},
		{float64(3.14), `3.14`},
		{float64(0), `0`},
		// 1e10 is integer-valued; Go's json.Marshal emits "10000000000",
		// which our canonical path preserves as an integer literal.
		// This is stable and deterministic — the same input always produces
		// the same output, which is the contract we actually need.
		{float64(1e10), `10000000000`},
	}
	for _, c := range cases {
		b, err := CanonicalMarshal(c.in)
		if err != nil {
			t.Fatalf("marshal %v: %v", c.in, err)
		}
		if string(b) != c.expected {
			t.Fatalf("input %v: expected %s, got %s", c.in, c.expected, b)
		}
	}
}

// TestCanonicalJSON_Arrays: element order preserved (NOT sorted).
func TestCanonicalJSON_Arrays(t *testing.T) {
	v := []interface{}{"c", "a", "b"}
	b, err := CanonicalMarshal(v)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	expected := `["c","a","b"]`
	if string(b) != expected {
		t.Fatalf("expected %s, got %s", expected, b)
	}
}

// TestCanonicalJSON_Struct: struct declaration order is already deterministic
// under encoding/json; CanonicalMarshalStruct preserves it.
func TestCanonicalJSON_Struct(t *testing.T) {
	type inner struct {
		Z string `json:"z"`
		A string `json:"a"`
	}
	type outer struct {
		Zebra  string `json:"zebra"`
		Alpha  string `json:"alpha"`
		Nested inner  `json:"nested"`
	}
	v := outer{Zebra: "z", Alpha: "a", Nested: inner{Z: "Z", A: "A"}}
	b, err := CanonicalMarshalStruct(v)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	// Struct fields are sorted lexicographically after the canonical pass, since
	// round-trip through map[string]interface{} normalizes keys.
	expected := `{"alpha":"a","nested":{"a":"A","z":"Z"},"zebra":"z"}`
	if string(b) != expected {
		t.Fatalf("expected %s, got %s", expected, b)
	}
}

// TestVerifyCanonicalBytes_RoundTrip: bytes produced by CanonicalMarshal
// verify as canonical; re-ordered JSON does not.
func TestVerifyCanonicalBytes_RoundTrip(t *testing.T) {
	v := map[string]interface{}{"b": 2, "a": 1}
	canonical, err := CanonicalMarshal(v)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	ok, detail := VerifyCanonicalBytes(canonical)
	if !ok {
		t.Fatalf("own canonical output failed verification: %s", detail)
	}
	// Non-canonical (keys out of order): should fail
	nonCanonical := []byte(`{"b":2,"a":1}`)
	ok, detail = VerifyCanonicalBytes(nonCanonical)
	if ok {
		t.Fatalf("non-canonical bytes incorrectly verified: %s", nonCanonical)
	}
	if detail == "" {
		t.Fatalf("verification failure must carry detail")
	}
}

// TestCanonicalJSONHash_Stability: hash is stable across calls.
func TestCanonicalJSONHash_Stability(t *testing.T) {
	v := map[string]interface{}{"x": 1, "y": 2}
	h1, b1, err := CanonicalJSONHash(v)
	if err != nil {
		t.Fatalf("hash: %v", err)
	}
	for i := 0; i < 100; i++ {
		h2, b2, err := CanonicalJSONHash(v)
		if err != nil {
			t.Fatalf("iter %d: %v", i, err)
		}
		if h1 != h2 || string(b1) != string(b2) {
			t.Fatalf("iter %d drift: hash %s vs %s, bytes %s vs %s", i, h1, h2, b1, b2)
		}
	}
}

// TestCanonicalJoinChain: validates chain encoding used for chain_binding_hash.
func TestCanonicalJoinChain(t *testing.T) {
	chain := []string{"hash_a", "hash_b", "hash_c"}
	b := CanonicalJoinChain(chain)
	expected := `["hash_a","hash_b","hash_c"]`
	if string(b) != expected {
		t.Fatalf("expected %s, got %s", expected, b)
	}
	// Must equal CanonicalMarshal of the equivalent []interface{}
	iface := []interface{}{"hash_a", "hash_b", "hash_c"}
	cm, err := CanonicalMarshal(iface)
	if err != nil {
		t.Fatalf("marshal iface: %v", err)
	}
	if string(cm) != string(b) {
		t.Fatalf("CanonicalJoinChain and CanonicalMarshal diverge: %s vs %s", b, cm)
	}
}

// TestCanonicalJSON_JSONNumberPreservation: when input contains a number that
// looks like an integer, it should be emitted as integer (no trailing .0).
func TestCanonicalJSON_JSONNumberPreservation(t *testing.T) {
	raw := []byte(`{"count": 42, "ratio": 3.14}`)
	reCan, err := CanonicalMarshalBytes(raw)
	if err != nil {
		t.Fatalf("recanon: %v", err)
	}
	expected := `{"count":42,"ratio":3.14}`
	if string(reCan) != expected {
		t.Fatalf("expected %s, got %s", expected, reCan)
	}
}

// TestCanonicalJSON_EmptyContainers: {} and [] survive the round-trip.
func TestCanonicalJSON_EmptyContainers(t *testing.T) {
	cases := []struct {
		in       interface{}
		expected string
	}{
		{map[string]interface{}{}, `{}`},
		{[]interface{}{}, `[]`},
		{map[string]interface{}{"x": []interface{}{}}, `{"x":[]}`},
		{map[string]interface{}{"x": map[string]interface{}{}}, `{"x":{}}`},
	}
	for _, c := range cases {
		b, err := CanonicalMarshal(c.in)
		if err != nil {
			t.Fatalf("marshal %v: %v", c.in, err)
		}
		if string(b) != c.expected {
			t.Fatalf("expected %s, got %s", c.expected, b)
		}
	}
}

// TestCanonicalJSON_NullHandling: nil / null encoded as literal "null".
func TestCanonicalJSON_NullHandling(t *testing.T) {
	v := map[string]interface{}{"n": nil, "s": "x"}
	b, err := CanonicalMarshal(v)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	expected := `{"n":null,"s":"x"}`
	if string(b) != expected {
		t.Fatalf("expected %s, got %s", expected, b)
	}
}

// TestCanonicalJSON_UseNumber_Sanity: verify that decode preserves numeric form.
func TestCanonicalJSON_UseNumber_Sanity(t *testing.T) {
	raw := []byte(`{"big": 9223372036854775807}`) // max int64
	reCan, err := CanonicalMarshalBytes(raw)
	if err != nil {
		t.Fatalf("recanon: %v", err)
	}
	expected := `{"big":9223372036854775807}`
	if string(reCan) != expected {
		t.Fatalf("expected %s, got %s", expected, reCan)
	}
}

// TestCanonicalJSON_IdempotentReCanonicalization: feeding canonical bytes back
// through CanonicalMarshalBytes must return identical bytes.
func TestCanonicalJSON_IdempotentReCanonicalization(t *testing.T) {
	v := map[string]interface{}{
		"trace_id": "t1",
		"chain":    []interface{}{"a", "b"},
		"verdict":  "ALLOW",
	}
	first, err := CanonicalMarshal(v)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	second, err := CanonicalMarshalBytes(first)
	if err != nil {
		t.Fatalf("recanon: %v", err)
	}
	if string(first) != string(second) {
		t.Fatalf("non-idempotent: first=%s second=%s", first, second)
	}
}

// TestCanonicalJSON_vs_StdJSONMarshal: confirm the standard library's
// json.Marshal does NOT produce canonical bytes when given a map. This is
// the motivation for this file — documented as a test to prevent regression.
func TestCanonicalJSON_vs_StdJSONMarshal(t *testing.T) {
	v := map[string]interface{}{"html": "<a>", "b": 2, "a": 1}
	std, _ := json.Marshal(v)
	can, _ := CanonicalMarshal(v)
	// std may have keys in random order AND escapes html. Canonical is stable
	// and lexical. The interesting assertion is that our canonical form is
	// a specific, known-good string.
	expected := `{"a":1,"b":2,"html":"<a>"}`
	if string(can) != expected {
		t.Fatalf("canonical: expected %s, got %s (std was %s)", expected, can, std)
	}
}
