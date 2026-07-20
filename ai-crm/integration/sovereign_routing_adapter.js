const REQUIRED_FIELDS = [
  'execution_id',
  'trace_id',
  'source_system',
  'actor',
  'intent_type',
  'target_system',
  'parameters',
  'priority',
  'timestamp',
  'schema_version',
  'tenant_id'
];

const REQUIRED_GATED_FIELDS = [
  'status',
  'attestation_id',
  'policy_id',
  'policy_version',
  'checked_at'
];

const assertRequired = (execution) => {
  const missing = REQUIRED_FIELDS.filter((field) => execution?.[field] === undefined || execution?.[field] === null);
  if (missing.length > 0) {
    throw new Error(`Missing execution fields: ${missing.join(', ')}`);
  }
};

const defaultGatedBridgeValidator = (execution) => {
  const gated = execution?.governance?.gated_bridge;
  if (!gated) {
    return { ok: false, reason: 'gated_bridge_missing' };
  }

  const missing = REQUIRED_GATED_FIELDS.filter((field) => gated[field] === undefined || gated[field] === null);
  if (missing.length > 0) {
    return { ok: false, reason: 'gated_bridge_incomplete', missing_fields: missing };
  }

  if (gated.status !== 'approved') {
    return { ok: false, reason: 'gated_bridge_not_approved', status: gated.status };
  }

  return { ok: true, governance: { gated_bridge: gated } };
};

const buildSarathiPayload = (execution) => ({
  sarathi_version: '1.0',
  execution_id: execution.execution_id,
  trace_id: execution.trace_id,
  tenant_id: execution.tenant_id,
  intent_type: execution.intent_type,
  source_system: execution.source_system,
  target_system: execution.target_system,
  parameters: execution.parameters,
  priority: execution.priority,
  timestamp: execution.timestamp,
  schema_version: execution.schema_version,
  actor: execution.actor
});

const buildBhivEnvelope = (execution, sarathiPayload) => ({
  envelope_version: '1.0',
  execution: {
    execution_id: execution.execution_id,
    trace_id: execution.trace_id,
    tenant_id: execution.tenant_id,
    intent_type: execution.intent_type,
    source_system: execution.source_system,
    target_system: execution.target_system,
    parameters: execution.parameters,
    priority: execution.priority,
    timestamp: execution.timestamp,
    schema_version: execution.schema_version,
    actor: execution.actor
  },
  routing: sarathiPayload,
  governance: execution.governance || null,
  provenance: execution.provenance || null,
  replay: execution.replay || null
});

export const createSovereignRoutingAdapter = (config = {}) => {
  const { validateGatedBridge = defaultGatedBridgeValidator } = config;

  return {
    validateGatedBridge,
    toSarathiPayload: (execution) => {
      assertRequired(execution);
      return buildSarathiPayload(execution);
    },
    toBhivEnvelope: (execution) => {
      assertRequired(execution);
      const sarathiPayload = buildSarathiPayload(execution);
      return buildBhivEnvelope(execution, sarathiPayload);
    },
    buildRoutingPacket: (execution) => {
      try {
        assertRequired(execution);
      } catch (error) {
        return {
          ok: false,
          reason: 'execution_contract_invalid',
          details: error?.message || 'missing required fields'
        };
      }

      const gated = validateGatedBridge(execution);
      if (!gated.ok) {
        return {
          ok: false,
          reason: gated.reason,
          details: gated.missing_fields || gated.status || null
        };
      }

      const sarathiPayload = buildSarathiPayload(execution);
      const bhivEnvelope = buildBhivEnvelope(execution, sarathiPayload);

      return {
        ok: true,
        sarathi_payload: sarathiPayload,
        bhiv_envelope: bhivEnvelope,
        governance: gated.governance
      };
    }
  };
};
