// canonical_json.go (v14.5 Cross-System Propagation Layer)
//
// RFC 8785 JCS-equivalent canonical JSON serializer. Used by the Cross-System
// Deterministic Propagation Layer to produce byte-stable representations of
// response envelopes so that Sha256Hex(CanonicalMarshal(v)) is deterministic
// across processes, runs, and Go runtime versions.
//
// Why this exists:
//   Go's encoding/json randomizes map[string]interface{} iteration at runtime,
//   so json.Marshal on a map produces non-deterministic bytes. response_contract.go
//   builds responses as maps — those bytes cannot be used for cross-system hashing.
//   This file provides the ONE canonical-bytes primitive used by pdp_adapter.go,
//   propagation_envelope.go, and propagation_harness.go.
//
// Canonical form properties (RFC 8785):
//   - JSON object keys sorted lexicographically at every nesting level.
//   - No insignificant whitespace between tokens.
//   - No HTML-safety escaping (& < > emitted literally inside strings).
//   - Numbers: integers in plain decimal; floats via strconv 'g' -1 (shortest round-trip).
//   - Arrays: element order preserved.
//   - Strings: standard JSON escaping (\", \\, \b, \f, \n, \r, \t, \u00XX for 0x00-0x1F).
//
// The primary entry points are CanonicalMarshal(v) and CanonicalJSONHash(v).

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"sort"
	"strconv"
	"unicode/utf8"
)

// CanonicalMarshal produces RFC 8785-equivalent canonical JSON bytes for v.
// Deterministic across Go runtimes: any v containing map[string]interface{}
// (or equivalent) has its keys sorted rather than randomized.
//
// Implementation strategy: round-trip through encoding/json to handle all Go types
// (struct tags, custom MarshalJSON, time.Time, etc.), then re-walk the decoded tree
// in canonical order.
func CanonicalMarshal(v interface{}) ([]byte, error) {
	raw, err := json.Marshal(v)
	if err != nil {
		return nil, fmt.Errorf("canonical_json: initial marshal: %w", err)
	}
	return CanonicalMarshalBytes(raw)
}

// CanonicalMarshalBytes re-serializes already-marshaled JSON bytes in canonical form.
// Useful at a propagation hop: incoming bytes on the wire can be re-canonicalized
// and compared byte-for-byte with the input to prove canonicality.
func CanonicalMarshalBytes(raw []byte) ([]byte, error) {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber() // Preserve numeric precision; avoid silent float64 conversion.
	var tree interface{}
	if err := dec.Decode(&tree); err != nil {
		return nil, fmt.Errorf("canonical_json: decode: %w", err)
	}
	var buf bytes.Buffer
	if err := canonicalEncode(&buf, tree); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// CanonicalMarshalStruct is an explicit alias for CanonicalMarshal. Provided
// for call-site clarity when the input is a typed struct (Go's json.Marshal
// already emits struct fields in declaration order, but this wrapper documents
// that deterministic ordering is the intent).
func CanonicalMarshalStruct(v interface{}) ([]byte, error) {
	return CanonicalMarshal(v)
}

// CanonicalJSONHash returns (hex SHA-256 of canonical bytes, canonical bytes, error).
// This is the primary helper used by propagation_envelope.go and propagation_harness.go.
func CanonicalJSONHash(v interface{}) (string, []byte, error) {
	b, err := CanonicalMarshal(v)
	if err != nil {
		return "", nil, err
	}
	return Sha256Hex(b), b, nil
}

// VerifyCanonicalBytes parses data and re-canonicalizes it, then compares the
// result against the input. Returns (true, "") if data is already canonical;
// otherwise (false, detail) with a diagnostic message suitable for logging.
//
// Used at every propagation hop on receipt: the downstream recomputes the
// canonical form locally and compares byte-for-byte with what Sarathi sent.
// Any drift (re-ordering, whitespace, HTML escape, etc.) triggers
// CodePropagationByteMismatch.
func VerifyCanonicalBytes(data []byte) (bool, string) {
	reCan, err := CanonicalMarshalBytes(data)
	if err != nil {
		return false, fmt.Sprintf("parse_error: %v", err)
	}
	if !bytes.Equal(reCan, data) {
		return false, fmt.Sprintf("non_canonical: sha256(input)=%s sha256(reCanonical)=%s size_in=%d size_re=%d",
			Sha256Hex(data), Sha256Hex(reCan), len(data), len(reCan))
	}
	return true, ""
}

// CanonicalJoinChain returns the canonical-bytes encoding of a []string as a
// JSON array. Used to compute chain_binding_hash = Sha256Hex(CanonicalJoinChain(chain)).
// Matches CanonicalMarshal([]interface{}{"a", "b", ...}) exactly.
func CanonicalJoinChain(chain []string) []byte {
	var buf bytes.Buffer
	buf.WriteByte('[')
	for i, s := range chain {
		if i > 0 {
			buf.WriteByte(',')
		}
		encodeString(&buf, s)
	}
	buf.WriteByte(']')
	return buf.Bytes()
}

// canonicalEncode writes v to buf in canonical JSON form. Supported types
// (those produced by json.Decode with UseNumber):
//   - map[string]interface{}  → sorted object
//   - []interface{}           → array (order preserved)
//   - json.Number             → numeric literal (integer or float)
//   - string, bool, nil       → standard JSON literals
//   - float64 / int / int64   → fallback for direct (non-decoded) inputs
func canonicalEncode(buf *bytes.Buffer, v interface{}) error {
	switch x := v.(type) {
	case nil:
		buf.WriteString("null")
	case bool:
		if x {
			buf.WriteString("true")
		} else {
			buf.WriteString("false")
		}
	case string:
		encodeString(buf, x)
	case json.Number:
		return encodeNumber(buf, string(x))
	case float64:
		return encodeNumber(buf, strconv.FormatFloat(x, 'g', -1, 64))
	case int64:
		buf.WriteString(strconv.FormatInt(x, 10))
	case int:
		buf.WriteString(strconv.FormatInt(int64(x), 10))
	case []interface{}:
		buf.WriteByte('[')
		for i, elem := range x {
			if i > 0 {
				buf.WriteByte(',')
			}
			if err := canonicalEncode(buf, elem); err != nil {
				return err
			}
		}
		buf.WriteByte(']')
	case map[string]interface{}:
		keys := make([]string, 0, len(x))
		for k := range x {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		buf.WriteByte('{')
		for i, k := range keys {
			if i > 0 {
				buf.WriteByte(',')
			}
			encodeString(buf, k)
			buf.WriteByte(':')
			if err := canonicalEncode(buf, x[k]); err != nil {
				return err
			}
		}
		buf.WriteByte('}')
	default:
		return fmt.Errorf("canonical_json: unsupported type %T", v)
	}
	return nil
}

// encodeString writes a canonical JSON string literal:
//   - Enclose in double quotes.
//   - Escape: \", \\, \b, \f, \n, \r, \t.
//   - Control characters 0x00-0x1F not otherwise escaped: \u00XX (lowercase hex).
//   - All other characters (including & < >): raw UTF-8. NO HTML-safety escaping.
func encodeString(buf *bytes.Buffer, s string) {
	buf.WriteByte('"')
	for i := 0; i < len(s); {
		r, size := utf8.DecodeRuneInString(s[i:])
		switch {
		case r == '"':
			buf.WriteString(`\"`)
		case r == '\\':
			buf.WriteString(`\\`)
		case r == '\b':
			buf.WriteString(`\b`)
		case r == '\f':
			buf.WriteString(`\f`)
		case r == '\n':
			buf.WriteString(`\n`)
		case r == '\r':
			buf.WriteString(`\r`)
		case r == '\t':
			buf.WriteString(`\t`)
		case r < 0x20:
			fmt.Fprintf(buf, `\u%04x`, r)
		default:
			buf.WriteString(s[i : i+size])
		}
		i += size
	}
	buf.WriteByte('"')
}

// encodeNumber writes a JSON number in canonical form.
//   - Integers (no '.', 'e', 'E' in input): parsed as int64, emitted in plain decimal.
//   - Floats: shortest round-trip via strconv.FormatFloat('g', -1, 64).
// Rejects NaN/+Inf/-Inf (JSON has no representation for these).
func encodeNumber(buf *bytes.Buffer, raw string) error {
	if !containsAnyRune(raw, ".eE") {
		n, err := strconv.ParseInt(raw, 10, 64)
		if err == nil {
			buf.WriteString(strconv.FormatInt(n, 10))
			return nil
		}
		// fall through (may be a very large integer best handled as float)
	}
	f, err := strconv.ParseFloat(raw, 64)
	if err != nil {
		return fmt.Errorf("canonical_json: invalid number %q: %w", raw, err)
	}
	// Reject non-finite values — JSON has no representation.
	if f != f || f > 1.797693134862315708e+308 || f < -1.797693134862315708e+308 {
		return fmt.Errorf("canonical_json: non-finite number %q", raw)
	}
	buf.WriteString(strconv.FormatFloat(f, 'g', -1, 64))
	return nil
}

func containsAnyRune(s, chars string) bool {
	for _, c := range s {
		for _, cc := range chars {
			if c == cc {
				return true
			}
		}
	}
	return false
}
