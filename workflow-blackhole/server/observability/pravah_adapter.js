/**
 * pravah_adapter.js
 * ==================
 * Pravah Bhiv observation adapter for workflow-blackhole Node.js runtime.
 *
 * Provides a lightweight, fire-and-forget telemetry emitter that pushes signed
 * runtime signals to the Pravah Control Plane.
 *
 * Pravah observes — not owns — the execution of this system.
 */

const crypto = require("crypto");
const axios = require("axios");

const PRAVAH_URL = process.env.PRAVAH_URL || "http://localhost:7000/api/runtime";
const SSPL_SECRET = process.env.SSPL_SECRET_KEY || "default-secret-key-change-in-prod";
const APP_NAME = "workflow-blackhole";

function signPayload(traceId, canonicalPayload) {
    const bodyHash = crypto.createHash("sha256").update(canonicalPayload).digest("hex");
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const sigData = `${traceId}:${timestamp}:${bodyHash}`;
    const signature = crypto.createHmac("sha256", SSPL_SECRET).update(sigData).digest("hex");
    return { timestamp, signature };
}

function emitPravahSignal(state = "running", latencyMs = 0.0, errorsLastMin = 0, workers = 1, extra = null) {
    const payload = {
        app: APP_NAME,
        env: process.env.ENVIRONMENT || "dev",
        state: state,
        latency_ms: parseFloat(latencyMs.toFixed(2)),
        errors_last_min: errorsLastMin,
        workers: workers
    };
    if (extra) {
        Object.assign(payload, extra);
    }

    const uuidHex = crypto.randomUUID().replace(/-/g, "");
    const traceId = `workflow-${uuidHex.substring(0, 16)}`;
    
    // Canonical JSON string (sorted keys, no spaces)
    const keys = Object.keys(payload).sort();
    const sortedPayload = {};
    keys.forEach(k => { sortedPayload[k] = payload[k]; });
    const canonical = JSON.stringify(sortedPayload);

    const { timestamp, signature } = signPayload(traceId, canonical);

    const headers = {
        "X-Trace-Id": traceId,
        "X-Timestamp": timestamp,
        "X-Trace-Signature": signature,
        "Content-Type": "application/json"
    };

    axios.post(PRAVAH_URL, payload, { headers, timeout: 4000 })
        .then(resp => {
            // console.log(`[Pravah] Telemetry sent | trace=${traceId} status=${resp.status}`);
        })
        .catch(err => {
            // console.error(`[Pravah] Telemetry failed: ${err.message}`);
        });
}

let heartbeatIntervalId = null;

function startHeartbeat(intervalSeconds = 60) {
    if (heartbeatIntervalId) return;
    heartbeatIntervalId = setInterval(() => {
        try {
            emitPravahSignal("running");
        } catch (e) {}
    }, intervalSeconds * 1000);
    // Emit immediately on start
    try {
        emitPravahSignal("running");
    } catch (e) {}
}

module.exports = { emitPravahSignal, startHeartbeat };
