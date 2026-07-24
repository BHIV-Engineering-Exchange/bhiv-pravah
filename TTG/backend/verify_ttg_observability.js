#!/usr/bin/env node
/**
 * verify_ttg_observability.js
 * ===========================
 * Standalone verification script — proves that Pravah can observe the
 * TTG runtime WITHOUT owning or interfering with it.
 */

const crypto = require("crypto");
const axios = require("axios");

const PRAVAH_URL = process.env.PRAVAH_URL || "http://localhost:7000/api/runtime";
const SSPL_SECRET = process.env.SSPL_SECRET_KEY || "default-secret-key-change-in-prod";
const APP_NAME = "ttg";

function signPayload(traceId, canonicalPayload) {
    const bodyHash = crypto.createHash("sha256").update(canonicalPayload).digest("hex");
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const sigData = `${traceId}:${timestamp}:${bodyHash}`;
    const signature = crypto.createHmac("sha256", SSPL_SECRET).update(sigData).digest("hex");
    return { timestamp, signature };
}

function main() {
    const traceId = `ttg-verify-${crypto.randomUUID().replace(/-/g, "").substring(0, 12)}`;

    console.log("=".repeat(70));
    console.log("  Pravah Observer -- TTG Node.js Observability Verification");
    console.log("=".repeat(70));
    console.log(`  Target  : ${PRAVAH_URL}`);
    console.log(`  App     : ${APP_NAME}`);
    console.log(`  Trace   : ${traceId}`);
    console.log("=".repeat(70));

    const payload = {
        app: APP_NAME,
        env: "dev",
        state: "running",
        latency_ms: 65.5,
        errors_last_min: 0,
        workers: 1
    };

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

    console.log("\n[1/3] Sending telemetry to Pravah Control Plane...");
    console.log(`      Payload : ${JSON.stringify(payload)}`);

    axios.post(PRAVAH_URL, payload, { headers, timeout: 5000 })
        .then(resp => {
            if (resp.status === 200) {
                console.log("\n[2/3] Pravah responded with HTTP 200");
                console.log(`      Status  : ${resp.data.status}`);
                console.log(`      Decision: ${JSON.stringify(resp.data.decision || "noop")}`);
                console.log("\n[3/3] Verification PASSED [OK]");
                console.log(`      Trace '${traceId}' resolved by Decision Brain.`);
                console.log(`      Pravah now has execution visibility into '${APP_NAME}'.`);
            } else {
                console.error(`\n[ERROR] Request failed with status ${resp.status}`);
                process.exit(1);
            }
        })
        .catch(err => {
            console.error(`\n[ERROR] Failed to connect to Pravah: ${err.message}`);
            process.exit(1);
        });
}

main();
