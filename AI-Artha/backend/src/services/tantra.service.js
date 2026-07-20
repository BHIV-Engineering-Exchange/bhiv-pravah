import crypto, { randomUUID } from 'crypto';
import axios from 'axios';
import logger from '../config/logger.js';
import UnifiedTrace from '../models/UnifiedTrace.js';
import RuntimeProof from '../models/RuntimeProof.js';
import ComplianceSignal from '../models/ComplianceSignal.js';

class TantraIntegrationService {
  constructor() {
    this.participationId = null;
    this.healthStatus = 'initializing';
    this.registrationTime = null;
    this.lastHeartbeat = null;
    this.eventQueue = [];
  }

  // Register with TANTRA runtime
  async register(participationData) {
    const { appId, version, capabilities, endpoints } = participationData;

    this.participationId = `TANTRA-${randomUUID().slice(0, 8)}`;
    this.registrationTime = new Date();
    this.healthStatus = 'registered';

    const registration = {
      participationId: this.participationId,
      appId: appId || 'ARTHA',
      version: version || '0.1.0',
      status: 'registered',
      capabilities: capabilities || [
        'ledger', 'invoices', 'expenses', 'gst', 'tds',
        'compliance', 'banking', 'audit', 'reports',
      ],
      endpoints: endpoints || {
        health: '/health/detailed',
        metrics: '/metrics',
        signals: '/api/v1/signals',
        trace: '/api/v1/trace',
        compliance: '/api/v1/compliance',
      },
      registeredAt: this.registrationTime,
      metadata: {
        nodeEnv: process.env.NODE_ENV,
        uptime: process.uptime(),
        memoryUsage: process.memoryUsage(),
      },
    };

    logger.info(`TANTRA registration: ${this.participationId}`);
    return registration;
  }

  // Send heartbeat
  async heartbeat() {
    this.lastHeartbeat = new Date();

    return {
      participationId: this.participationId,
      status: this.healthStatus,
      timestamp: this.lastHeartbeat,
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      eventQueueSize: this.eventQueue.length,
    };
  }

  // Emit runtime event to TANTRA
  async emitEvent(eventData) {
    const event = {
      eventId: `EVT-${randomUUID()}`,
      participationId: this.participationId,
      timestamp: new Date(),
      ...eventData,
    };

    this.eventQueue.push(event);

    // Process queue if > 10 events
    if (this.eventQueue.length > 10) {
      await this.flushEventQueue();
    }

    // Report observation to Pravah if traceId is available
    const traceId = eventData.traceId || eventData.trace_id;
    if (traceId) {
      try {
        const state = (eventData.status === 'FAILED' || eventData.severity === 'critical') ? 'degraded' : 'running';
        const latencyMs = eventData.metadata?.durationMs || eventData.duration || 50;
        const errors = (eventData.status === 'FAILED' || eventData.severity === 'critical') ? 1 : 0;
        this.sendTelemetryToPravah(traceId, state, latencyMs, errors);
      } catch (err) {
        logger.warn(`[PRAVAH_OBSERVER] Telemetry trigger error: ${err.message}`);
      }
    }

    return event;
  }

  async flushEventQueue() {
    const events = [...this.eventQueue];
    this.eventQueue = [];

    logger.info(`Flushed ${events.length} events to TANTRA`);
    return { flushed: events.length, events };
  }

  // Get operational metadata for TANTRA
  async getOperationalMetadata() {
    return {
      participationId: this.participationId,
      healthStatus: this.healthStatus,
      registrationTime: this.registrationTime,
      lastHeartbeat: this.lastHeartbeat,
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      eventQueueSize: this.eventQueue.length,
      capabilities: [
        'ledger', 'invoices', 'expenses', 'gst', 'tds',
        'compliance', 'banking', 'audit', 'reports',
      ],
      runtimeState: {
        databaseConnected: true,
        redisConnected: false,
        activeTraces: await UnifiedTrace.countDocuments({ status: 'IN_PROGRESS' }),
        totalTraces: await UnifiedTrace.countDocuments({}),
        totalProofs: await RuntimeProof.countDocuments({}),
        activeSignals: await ComplianceSignal.countDocuments({ status: { $ne: 'resolved' } }),
      },
    };
  }

  // Report lifecycle event
  async reportLifecycle(eventType, data) {
    return this.emitEvent({
      type: 'LIFECYCLE',
      eventType,
      data,
      severity: eventType === 'ERROR' ? 'critical' : 'info',
    });
  }

  // Helper to send signed telemetry to Pravah observation endpoint
  async sendTelemetryToPravah(traceId, state = 'running', latencyMs = 50, errorsLastMin = 0) {
    try {
      const payload = {
        app: 'artha-backend',
        env: process.env.NODE_ENV === 'production' ? 'prod' : 'dev',
        state: state,
        latency_ms: Number(latencyMs) || 50,
        errors_last_min: Number(errorsLastMin) || 0,
        workers: 1
      };

      const secretKey = process.env.SSPL_SECRET_KEY || 'default-secret-key-change-in-prod';
      
      // Sorted keys for canonical JSON
      const sortedKeys = Object.keys(payload).sort();
      const sortedObj = {};
      for (const key of sortedKeys) {
        sortedObj[key] = payload[key];
      }
      const canonical = JSON.stringify(sortedObj);
      
      // Calculate body hash
      const bodyHash = crypto.createHash('sha256').update(canonical).digest('hex');
      const timestamp = Math.floor(Date.now() / 1000).toString();
      
      // Sign trace
      const tracePayload = `${traceId}:${timestamp}:${bodyHash}`;
      const signature = crypto.createHmac('sha256', secretKey).update(tracePayload).digest('hex');
      
      // Post observation to Pravah
      const response = await axios.post('http://localhost:7000/api/runtime', payload, {
        headers: {
          'X-Trace-Id': traceId,
          'X-Timestamp': timestamp,
          'X-Trace-Signature': signature,
          'Content-Type': 'application/json'
        },
        timeout: 5000
      });
      logger.info(`[PRAVAH_OBSERVER] Observed execution for trace ${traceId}: status=${response.data?.status}`);
    } catch (err) {
      logger.warn(`[PRAVAH_OBSERVER] Failed to send telemetry for trace ${traceId} to Pravah: ${err.message}`);
    }
  }

  // Report transaction lifecycle
  async reportTransactionLifecycle(traceId, stage, status, metadata) {
    const event = await this.emitEvent({
      type: 'TRANSACTION',
      eventType: stage,
      traceId,
      status,
      metadata,
    });

    return event;
  }

  // Report compliance event
  async reportComplianceEvent(filingType, status, traceId) {
    return this.emitEvent({
      type: 'COMPLIANCE',
      eventType: `FILING_${status}`,
      filingType,
      traceId,
      severity: status === 'FILED' ? 'info' : 'warning',
    });
  }

  // Set health status
  setHealthStatus(status) {
    this.healthStatus = status;
  }
}

export default new TantraIntegrationService();
