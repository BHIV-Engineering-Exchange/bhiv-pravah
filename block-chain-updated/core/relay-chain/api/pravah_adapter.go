package api

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"sort"
	"strconv"
	"sync"
	"time"
)

var (
	pravahURL   = getEnvOrDefault("PRAVAH_URL", "http://localhost:7000/api/runtime")
	ssplSecret  = getEnvOrDefault("SSPL_SECRET_KEY", "default-secret-key-change-in-prod")
	appName     = "block-chain-updated"
	heartOnce   sync.Once
	httpClient  = &http.Client{Timeout: 4 * time.Second}
)

func getEnvOrDefault(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func signPayload(traceID, canonical string) (string, string) {
	bodyHashBytes := sha256.Sum256([]byte(canonical))
	bodyHash := hex.EncodeToString(bodyHashBytes[:])

	timestamp := strconv.FormatInt(time.Now().Unix(), 10)
	sigData := fmt.Sprintf("%s:%s:%s", traceID, timestamp, bodyHash)

	h := hmac.New(sha256.New, []byte(ssplSecret))
	h.Write([]byte(sigData))
	signature := hex.EncodeToString(h.Sum(nil))

	return timestamp, signature
}

func EmitPravahSignal(state string, latencyMs float64, errorsLastMin int) {
	go func() {
		defer func() {
			if r := recover(); r != nil {
				// Prevent crashes from panic
			}
		}()

		traceID := fmt.Sprintf("blockchain-%d", time.Now().UnixNano())

		payload := map[string]interface{}{
			"app":             appName,
			"env":             getEnvOrDefault("ENVIRONMENT", "dev"),
			"state":           state,
			"latency_ms":      latencyMs,
			"errors_last_min": errorsLastMin,
			"workers":         1,
		}

		// Sort keys for canonical JSON serialization
		keys := make([]string, 0, len(payload))
		for k := range payload {
			keys = append(keys, k)
		}
		sort.Strings(keys)

		canonicalBuf := bytes.NewBuffer(nil)
		canonicalBuf.WriteString("{")
		for i, k := range keys {
			valBytes, _ := json.Marshal(payload[k])
			canonicalBuf.WriteString(fmt.Sprintf("%q:%s", k, string(valBytes)))
			if i < len(keys)-1 {
				canonicalBuf.WriteString(",")
			}
		}
		canonicalBuf.WriteString("}")

		canonicalStr := canonicalBuf.String()
		timestamp, signature := signPayload(traceID, canonicalStr)

		bodyBytes, _ := json.Marshal(payload)
		req, err := http.NewRequest("POST", pravahURL, bytes.NewBuffer(bodyBytes))
		if err != nil {
			return
		}

		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("X-Trace-Id", traceID)
		req.Header.Set("X-Timestamp", timestamp)
		req.Header.Set("X-Trace-Signature", signature)

		resp, err := httpClient.Do(req)
		if err == nil && resp != nil {
			resp.Body.Close()
		}
	}()
}

func StartHeartbeat(intervalSeconds int) {
	heartOnce.Do(func() {
		go func() {
			ticker := time.NewTicker(time.Duration(intervalSeconds) * time.Second)
			defer ticker.Stop()

			// Initial signal
			EmitPravahSignal("running", 0.0, 0)

			for range ticker.C {
				EmitPravahSignal("running", 0.0, 0)
			}
		}()
	})
}
