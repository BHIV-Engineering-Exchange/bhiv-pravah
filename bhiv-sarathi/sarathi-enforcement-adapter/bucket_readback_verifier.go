// bucket_readback_verifier.go (v14.7 Live Integration Closure)
//
// Phase 2 helper: given a Bucket URL and a sealed envelope, GET the stored
// bytes and prove end-to-end state integrity:
//
//   1. stored_bytes == envelope.CanonicalResponseBytes()   (byte-equal)
//   2. sha256(stored_bytes) == envelope.ResponseHash()     (hash-equal)
//   3. VerifyCanonicalBytes(stored_bytes) == (true, "")    (still canonical)
//
// If any of the three fails, return CodeBucketReadbackMismatch. This is the
// primitive that closes the Output = Propagation = Storage loop required by
// task.md. Used by:
//   - live_integration_runner.go (v14.7)
//   - Optionally by bucket_state_verifier.go / cross_system_integration_validator.go
//     (via the shared helper; originals untouched to preserve v14.6 audit).
//
// TAG: live-integration

package main

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"time"
)

// BucketReadbackResult captures the verdict and diagnostic fields.
type BucketReadbackResult struct {
	DecisionID   string `json:"decision_id"`
	ExecutionID  string `json:"execution_id"`
	ResponseHash string `json:"response_hash"`
	BucketHash   string `json:"bucket_hash"`
	Match        bool   `json:"match"`
	VerifiedAt   string `json:"verified_at"`
	ErrorCode    string `json:"error_code,omitempty"`
	Detail       string `json:"detail,omitempty"`
	HTTPStatus   int    `json:"http_status"`
	BytesLength  int    `json:"bytes_length"`
}

// VerifyBucketReadback performs the GET + canonical + hash + byte-equal checks.
// bucketURL should be the Bucket peer's base (e.g. http://127.0.0.1:7103).
// The GET path is {bucketURL}/v1/audit/{decisionID}.
func VerifyBucketReadback(
	ctx context.Context, bucketURL, decisionID, executionID string,
	expectedBytes []byte, expectedHash string,
) BucketReadbackResult {
	result := BucketReadbackResult{
		DecisionID:   decisionID,
		ExecutionID:  executionID,
		ResponseHash: expectedHash,
		VerifiedAt:   time.Now().UTC().Format(time.RFC3339Nano),
	}

	if bucketURL == "" {
		result.ErrorCode = CodeBucketReadbackMismatch
		result.Detail = "bucket_url_empty"
		return result
	}
	url := fmt.Sprintf("%s/v1/audit/%s", bucketURL, decisionID)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		result.ErrorCode = CodeBucketReadbackMismatch
		result.Detail = fmt.Sprintf("build_request: %v", err)
		return result
	}
	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		result.ErrorCode = CodeBucketReadbackMismatch
		result.Detail = fmt.Sprintf("http_do: %v", err)
		return result
	}
	defer resp.Body.Close()
	result.HTTPStatus = resp.StatusCode

	body, err := io.ReadAll(io.LimitReader(resp.Body, LivePeerMaxBodyBytes))
	if err != nil {
		result.ErrorCode = CodeBucketReadbackMismatch
		result.Detail = fmt.Sprintf("read_body: %v", err)
		return result
	}
	result.BytesLength = len(body)

	if resp.StatusCode != http.StatusOK {
		result.ErrorCode = CodeBucketReadbackMismatch
		result.Detail = fmt.Sprintf("bad_status: %d", resp.StatusCode)
		return result
	}

	// Hash check.
	result.BucketHash = Sha256Hex(body)
	if result.BucketHash != expectedHash {
		result.ErrorCode = CodeBucketReadbackMismatch
		result.Detail = fmt.Sprintf("hash_mismatch: want=%s got=%s",
			expectedHash, result.BucketHash)
		return result
	}

	// Byte-equal check (strictest).
	if expectedBytes != nil && !bytes.Equal(body, expectedBytes) {
		result.ErrorCode = CodeBucketReadbackMismatch
		result.Detail = "byte_mismatch_despite_hash_equal_indicates_collision_or_corruption"
		return result
	}

	// Canonicalisation check.
	if ok, detail := VerifyCanonicalBytes(body); !ok {
		result.ErrorCode = CodeBucketReadbackMismatch
		result.Detail = "non_canonical_readback: " + detail
		return result
	}

	result.Match = true
	return result
}
