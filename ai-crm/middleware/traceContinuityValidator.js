import crypto from 'crypto';

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

// Stable stringify to ensure deterministic lineage hashing.
const stableStringify = (value) => {
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(',')}]`;
  }
  if (value && typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
};

const computeLineageHash = (execution) => {
  const lineage = execution.trace_lineage || {};
  const fingerprint = {
    execution_id: execution.execution_id,
    trace_id: execution.trace_id,
    tenant_id: execution.tenant_id,
    root_trace_id: lineage.root_trace_id || execution.trace_id,
    parent_trace_id: lineage.parent_trace_id || null,
    parent_execution_id: lineage.parent_execution_id || null
  };
  return crypto.createHash('sha256').update(stableStringify(fingerprint)).digest('hex');
};

const createInMemoryLineageStore = () => {
  const byExecutionId = new Map();

  return {
    getByExecutionId: (executionId) => byExecutionId.get(executionId) || null,
    set: (record) => {
      byExecutionId.set(record.execution_id, record);
      return record;
    },
    list: () => Array.from(byExecutionId.values())
  };
};

const defaultExtractExecution = (req) => {
  if (req?.body?.execution) {
    return req.body.execution;
  }
  if (req?.body?.execution_contract) {
    return req.body.execution_contract;
  }
  return req?.body;
};

const buildRejectPayload = (code, message, details) => ({
  success: false,
  error: code,
  message,
  details
});

export const createTraceContinuityValidator = (options = {}) => {
  const {
    extractExecution = defaultExtractExecution,
    lineageStore = createInMemoryLineageStore(),
    logger = console,
    requiredFields = REQUIRED_FIELDS,
    attachResponseHeaders = true
  } = options;

  return (req, res, next) => {
    let execution;
    try {
      execution = extractExecution(req);
    } catch (error) {
      const payload = buildRejectPayload(
        'execution_extraction_failed',
        'Unable to extract execution contract',
        { error: error?.message || 'unknown' }
      );
      logger.warn(payload);
      return res.status(400).json(payload);
    }

    if (!execution || typeof execution !== 'object') {
      const payload = buildRejectPayload('execution_missing', 'Execution contract is required', {
        received_type: typeof execution
      });
      logger.warn(payload);
      return res.status(400).json(payload);
    }

    const missing = requiredFields.filter((field) => execution[field] === undefined || execution[field] === null);
    if (missing.length > 0) {
      const payload = buildRejectPayload(
        'execution_missing_fields',
        'Execution contract missing required fields',
        { missing_fields: missing }
      );
      logger.warn(payload);
      return res.status(400).json(payload);
    }

    const { execution_id, trace_id, tenant_id, trace_lineage = {} } = execution;

    const existing = lineageStore.getByExecutionId(execution_id);
    if (existing && existing.trace_id !== trace_id) {
      const payload = buildRejectPayload('trace_id_regenerated', 'Trace ID regeneration detected', {
        execution_id,
        expected_trace_id: existing.trace_id,
        received_trace_id: trace_id
      });
      logger.warn(payload);
      return res.status(409).json(payload);
    }

    if (trace_lineage.root_trace_id && trace_lineage.root_trace_id !== trace_id) {
      const payload = buildRejectPayload('trace_root_mismatch', 'Root trace ID mismatch', {
        execution_id,
        root_trace_id: trace_lineage.root_trace_id,
        trace_id
      });
      logger.warn(payload);
      return res.status(409).json(payload);
    }

    if (trace_lineage.parent_execution_id) {
      const parent = lineageStore.getByExecutionId(trace_lineage.parent_execution_id);
      if (parent) {
        if (parent.trace_id !== trace_id) {
          const payload = buildRejectPayload('trace_lineage_mutated', 'Parent trace mismatch in lineage', {
            execution_id,
            parent_execution_id: trace_lineage.parent_execution_id,
            parent_trace_id: parent.trace_id,
            trace_id
          });
          logger.warn(payload);
          return res.status(409).json(payload);
        }
        if (parent.tenant_id !== tenant_id) {
          const payload = buildRejectPayload('tenant_lineage_violation', 'Tenant lineage mismatch', {
            execution_id,
            parent_execution_id: trace_lineage.parent_execution_id,
            expected_tenant_id: parent.tenant_id,
            received_tenant_id: tenant_id
          });
          logger.warn(payload);
          return res.status(409).json(payload);
        }
      }
    }

    const computedLineageHash = computeLineageHash(execution);
    if (trace_lineage.lineage_hash && trace_lineage.lineage_hash !== computedLineageHash) {
      const payload = buildRejectPayload('lineage_hash_mismatch', 'Lineage hash mismatch', {
        execution_id,
        expected_hash: computedLineageHash,
        received_hash: trace_lineage.lineage_hash
      });
      logger.warn(payload);
      return res.status(409).json(payload);
    }

    const record = {
      execution_id,
      trace_id,
      tenant_id,
      root_trace_id: trace_lineage.root_trace_id || trace_id,
      parent_execution_id: trace_lineage.parent_execution_id || null,
      lineage_hash: trace_lineage.lineage_hash || computedLineageHash,
      seen_at: new Date().toISOString()
    };

    lineageStore.set(record);

    req.setuTraceContext = {
      execution_id,
      trace_id,
      tenant_id,
      lineage_hash: record.lineage_hash,
      root_trace_id: record.root_trace_id
    };
    req.getSetuTraceHeaders = () => ({
      'x-setu-execution-id': execution_id,
      'x-setu-trace-id': trace_id,
      'x-setu-tenant-id': tenant_id,
      'x-setu-lineage-hash': record.lineage_hash
    });

    if (attachResponseHeaders) {
      res.setHeader('X-SETU-Execution-Id', execution_id);
      res.setHeader('X-SETU-Trace-Id', trace_id);
      res.setHeader('X-SETU-Tenant-Id', tenant_id);
      res.setHeader('X-SETU-Lineage-Hash', record.lineage_hash);
    }

    logger.info({
      event: 'trace_continuity_ok',
      execution_id,
      trace_id,
      tenant_id,
      lineage_hash: record.lineage_hash
    });

    return next();
  };
};

export { createInMemoryLineageStore, computeLineageHash };
