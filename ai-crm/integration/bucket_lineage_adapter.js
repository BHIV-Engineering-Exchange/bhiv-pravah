import crypto from 'crypto';

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

const deepFreeze = (value) => {
  if (!value || typeof value !== 'object') {
    return value;
  }
  Object.freeze(value);
  Object.values(value).forEach((child) => deepFreeze(child));
  return value;
};

const createInMemoryAppendOnlyStore = () => {
  const events = [];
  const sequenceByTrace = new Map();

  return {
    nextSequence: (traceId) => {
      const next = (sequenceByTrace.get(traceId) || 0) + 1;
      sequenceByTrace.set(traceId, next);
      return next;
    },
    append: (event) => {
      events.push(event);
      return event;
    },
    list: () => events.slice()
  };
};

const computeDeterminismHash = (event) => {
  const base = { ...event };
  delete base.determinism_hash;
  return crypto.createHash('sha256').update(stableStringify(base)).digest('hex');
};

const buildLineageEvent = (execution, eventType, payload, sequence, timestamp) => {
  const event = {
    lineage_event_id: '',
    execution_id: execution.execution_id,
    trace_id: execution.trace_id,
    tenant_id: execution.tenant_id,
    event_type: eventType,
    timestamp,
    sequence,
    payload
  };
  const determinismHash = computeDeterminismHash(event);
  event.determinism_hash = determinismHash;
  event.lineage_event_id = `lin_${determinismHash.slice(0, 16)}`;
  return event;
};

export const createBucketLineageAdapter = (options = {}) => {
  const store = options.store || createInMemoryAppendOnlyStore();

  return {
    emitExecutionEvent: (execution, eventType, payload = {}, overrides = {}) => {
      if (!execution?.execution_id || !execution?.trace_id || !execution?.tenant_id) {
        throw new Error('Execution identifiers are required for lineage emission');
      }

      const timestamp = overrides.timestamp || execution.timestamp;
      const sequence = overrides.sequence || store.nextSequence(execution.trace_id);

      const event = buildLineageEvent(execution, eventType, payload, sequence, timestamp);
      const frozenEvent = deepFreeze(event);
      store.append(frozenEvent);
      return frozenEvent;
    },
    listArtifacts: () => store.list().map((event) => ({ ...event }))
  };
};

export { createInMemoryAppendOnlyStore };
