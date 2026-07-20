const TELEMETRY_TYPES = [
  'execution_started',
  'execution_failed',
  'execution_completed',
  'execution_blocked',
  'governance_rejection',
  'dependency_blocked',
  'tenant_rejection'
];

const createInMemoryTelemetrySink = () => {
  const events = [];
  return {
    append: (event) => {
      events.push(event);
      return event;
    },
    list: () => events.slice()
  };
};

const validateTelemetry = (event) => {
  const missing = ['execution_id', 'trace_id', 'tenant_id', 'timestamp', 'event_type']
    .filter((field) => event?.[field] === undefined || event?.[field] === null);
  if (missing.length > 0) {
    throw new Error(`Telemetry missing required fields: ${missing.join(', ')}`);
  }
  if (!TELEMETRY_TYPES.includes(event.event_type)) {
    throw new Error(`Unsupported telemetry type: ${event.event_type}`);
  }
};

const buildEvent = (type, execution, details, overrides, now) => ({
  event_type: type,
  execution_id: execution.execution_id,
  trace_id: execution.trace_id,
  tenant_id: execution.tenant_id,
  timestamp: overrides.timestamp || execution.timestamp || now(),
  details: details || {},
  source_system: execution.source_system || 'setu'
});

export const createTelemetryLayer = (options = {}) => {
  const sink = options.sink || createInMemoryTelemetrySink();
  const now = options.now || (() => new Date().toISOString());

  const emit = (event) => {
    validateTelemetry(event);
    return sink.append(event);
  };

  return {
    emit,
    emitExecutionStarted: (execution, details = {}, overrides = {}) =>
      emit(buildEvent('execution_started', execution, details, overrides, now)),
    emitExecutionFailed: (execution, details = {}, overrides = {}) =>
      emit(buildEvent('execution_failed', execution, details, overrides, now)),
    emitExecutionCompleted: (execution, details = {}, overrides = {}) =>
      emit(buildEvent('execution_completed', execution, details, overrides, now)),
    emitExecutionBlocked: (execution, details = {}, overrides = {}) =>
      emit(buildEvent('execution_blocked', execution, details, overrides, now)),
    emitGovernanceRejection: (execution, details = {}, overrides = {}) =>
      emit(buildEvent('governance_rejection', execution, details, overrides, now)),
    emitDependencyBlocked: (execution, details = {}, overrides = {}) =>
      emit(buildEvent('dependency_blocked', execution, details, overrides, now)),
    emitTenantRejection: (execution, details = {}, overrides = {}) =>
      emit(buildEvent('tenant_rejection', execution, details, overrides, now)),
    list: () => sink.list().map((event) => ({ ...event }))
  };
};

export { TELEMETRY_TYPES };
