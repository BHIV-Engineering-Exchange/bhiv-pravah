package main

// bridge_only_mode.go — v15.6 Bridge-Only Surface Gate.
//
// Purpose: when SARATHI_BRIDGE_ONLY_MODE=1 the operator declares that this
// instance is reachable only by an external Bridge verifier. Routes that the
// Bridge does not consume (/v1/enforce, /v1/ingest-decision, /v1/bridge/info,
// peer-receipt endpoints) are short-circuited with HTTP 404 so a misbehaving
// caller cannot stumble onto a path the deployment did not intend to expose.
//
// What stays reachable in bridge-only mode:
//   - POST /sarathi/enforce            (the Sovereign ingestion path)
//   - GET  /sarathi/.well-known/jwks.json
//   - GET  /sarathi/.well-known/sarathi-authority
//   - POST /sarathi/v1/token/introspect
//   - GET  /sarathi/validate-token
//   - GET  /health, /health/deep, /metrics, /metrics/prometheus
//
// What 404s in bridge-only mode:
//   - POST /v1/enforce
//   - POST /v1/ingest-decision
//   - GET  /v1/bridge/info
//   - POST /v1/handshake, POST /v1/downstream-ack
//   - every /v1/evaluators/* admin route (already frozen)
//
// This helper is intentionally tiny: a single bool, two helpers, no goroutines,
// no state. It is read once at boot from the env (cheap) and cached on the
// ServiceBoundary so handlers don't re-read the env per request.
//
// TAG: bridge-only-mode-v15.6

import (
	"encoding/json"
	"net/http"
	"os"
	"strings"
	"sync/atomic"
)

// EnvBridgeOnlyMode is the operator-facing toggle. Set to "1" to enable.
// Any other value (including unset) leaves the v15.5 behaviour unchanged.
const EnvBridgeOnlyMode = "SARATHI_BRIDGE_ONLY_MODE"

// BridgeOnlyModeFromEnv reads the env var. Exported so service_runtime_cli
// can read it during bootstrap before constructing the boundary, AND so the
// failure-demo harness can verify the gate from outside the boundary.
func BridgeOnlyModeFromEnv() bool {
	return strings.TrimSpace(os.Getenv(EnvBridgeOnlyMode)) == "1"
}

// BlockNonBridgePath writes a 404 response and returns true when the boundary
// is in bridge-only mode. Handlers protected by this gate should call it as
// their first statement:
//
//	func (sb *ServiceBoundary) handleEnforce(w, r) {
//	    if sb.BlockNonBridgePath(w, r) { return }
//	    ...
//	}
//
// Returning true signals the handler MUST return without further work; the
// response has already been written.
func (sb *ServiceBoundary) BlockNonBridgePath(w http.ResponseWriter, r *http.Request) bool {
	if !sb.bridgeOnlyMode {
		return false
	}
	atomic.AddUint64(&sb.totalHTTPErrors, 1)
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Sarathi-Error-Code", "ERR_BRIDGE_ONLY_MODE_PATH_HIDDEN")
	w.WriteHeader(http.StatusNotFound)
	_ = json.NewEncoder(w).Encode(map[string]string{
		"error":  "NOT_FOUND",
		"detail": "this endpoint is hidden by SARATHI_BRIDGE_ONLY_MODE=1; use /sarathi/enforce instead",
	})
	return true
}

// IsBridgeOnly reports the cached flag. Useful for banners and audits.
func (sb *ServiceBoundary) IsBridgeOnly() bool { return sb.bridgeOnlyMode }
