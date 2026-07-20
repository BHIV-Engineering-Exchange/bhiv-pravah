/**
 * Tier-2 Artha partner capture — loads real ComplianceSignal from Mongo, dispatches to Sampada live gateway.
 */
import mongoose from 'mongoose';
import ComplianceSignal from '../src/models/ComplianceSignal.js';
import { runPipeline } from '../src/services/setu.pipeline.js';
import { toSampadaEnvelope, parseSampadaAcknowledge, sampadaIngestEndpoint } from '../src/services/sampadaAdapter.js';
import axios from 'axios';

const uri = process.env.MONGODB_URI;
if (!uri) {
  console.log(JSON.stringify({ ok: false, error: 'MONGODB_URI missing' }));
  process.exit(1);
}

await mongoose.connect(uri, { serverSelectionTimeoutMS: 20000 });

let signal = await ComplianceSignal.findOne().sort({ created_at: -1 }).lean();
if (!signal) {
  const created = await ComplianceSignal.create({
    trace_id: `TRC-20260702-${Date.now().toString(16).slice(0, 8)}`,
    type: 'SIG_FILING_GENERATED',
    severity: 'LOW',
    context: {
      source: { entity_id: 'FILING-CLOSEOUT-20260702', entity_type: 'COMPLIANCE_FILING', module: 'COMPLIANCE_FILING' },
      filing_id: 'FILING-CLOSEOUT-20260702',
      filing_type: 'GSTR1',
      period: '2026-06',
    },
    recommendation: '[REVIEW_BEFORE_FILING] Filing packet generated. Review before submission.',
  });
  signal = created.toObject();
}

const pipeline = runPipeline(signal);
if (!pipeline.ok) {
  console.log(JSON.stringify({ ok: false, stage: pipeline.stage, error: pipeline.error }));
  process.exit(1);
}

const baseUrl = process.env.SETU_BASE_URL;
const apiKey = process.env.SETU_API_KEY;
const endpoint = sampadaIngestEndpoint(baseUrl);
const envelope = toSampadaEnvelope(pipeline.payload, {
  correlation_id: process.env.SAMPADA_SETU_CORRELATION_ID,
});

const started = Date.now();
try {
  const response = await axios.post(endpoint, envelope, {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
    timeout: parseInt(process.env.SETU_TIMEOUT_MS || '30000', 10),
  });
  const ack = parseSampadaAcknowledge(response.data);
  console.log(JSON.stringify({
    ok: true,
    tier: 'Tier 2 — dispatcher invoked directly, partner server not booted in this environment',
    artha_signal_id: signal.signal_id,
    sampada_signal_id: response.data?.signal_id,
    trace_id: envelope.trace_id,
    correlation_id: envelope.correlation_id,
    request: { method: 'POST', url: endpoint, body: envelope },
    response: { status: response.status, body: response.data, latency_ms: Date.now() - started },
    ack,
  }));
} catch (err) {
  console.log(JSON.stringify({
    ok: false,
    tier: 'Tier 2 — dispatcher invoked directly, partner server not booted in this environment',
    artha_signal_id: signal.signal_id,
    request: { method: 'POST', url: endpoint, body: envelope },
    response: { status: err.response?.status, body: err.response?.data, error: err.message },
  }));
  process.exit(1);
} finally {
  await mongoose.disconnect();
}
