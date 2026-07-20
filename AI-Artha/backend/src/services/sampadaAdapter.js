/**
 * sampadaAdapter.js — map Artha serialized signals to Sampada SetuSignalIngest (2026-07-02).
 * Additive adapter only; does not change Artha's internal pipeline stages.
 */

import { randomUUID } from 'crypto';

const SAMPADA_SIGNAL_TYPE = 'artha_payroll_visibility';

/**
 * @param {object} arthaPayload Output of mapToSetuPayload / pipeline payload
 * @param {{ correlation_id?: string, workforce_ref_id?: string }} extras
 */
export function toSampadaEnvelope(arthaPayload, extras = {}) {
  if (!arthaPayload?.trace_id) {
    throw new Error('trace_id is required for Sampada envelope');
  }
  return {
    signal_type: SAMPADA_SIGNAL_TYPE,
    payload: arthaPayload,
    workforce_ref_id: extras.workforce_ref_id ?? null,
    source_declaration: 'artha payroll visibility participation',
    origin_system: 'artha',
    owning_system: 'artha',
    trace_id: arthaPayload.trace_id,
    correlation_id: extras.correlation_id || randomUUID(),
    trust_classification: 'observed',
    visibility_scope: 'tenant',
  };
}

/** Parse Sampada gateway ingest response (signal doc with signal_id). */
export function parseSampadaAcknowledge(responseBody) {
  if (!responseBody || typeof responseBody !== 'object') {
    return { valid: false, status: 'FAILED', error: 'Empty or invalid response body' };
  }
  if (responseBody.signal_id) {
    return {
      valid: true,
      status: 'ACCEPTED',
      setuReference: responseBody.signal_id,
      raw: responseBody,
    };
  }
  return {
    valid: false,
    status: 'REJECTED',
    error: responseBody.detail || responseBody.message || 'Unknown Sampada response',
    raw: responseBody,
  };
}

export function sampadaIngestEndpoint(baseUrl) {
  return `${baseUrl.replace(/\/$/, '')}/v1/setu/signals/${SAMPADA_SIGNAL_TYPE}`;
}
