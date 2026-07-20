import mongoose from 'mongoose';
import { getRedisClient } from '../config/redis.js';
import logger from '../config/logger.js';
import UnifiedTrace from '../models/UnifiedTrace.js';
import RuntimeProof from '../models/RuntimeProof.js';
import ComplianceSignal from '../models/ComplianceSignal.js';
import JournalEntry from '../models/JournalEntry.js';
import LedgerEntry from '../models/LedgerEntry.js';
import Payment from '../models/Payment.js';
import AuditEvent from '../models/AuditEvent.js';

class ObservabilityService {
  constructor() {
    this.metrics = {
      requestCount: 0,
      errorCount: 0,
      responseTimes: [],
      startTime: Date.now(),
    };
  }

  // Comprehensive system health
  async getSystemHealth() {
    const [database, redis, traces, proofs, signals, journals, payments, auditEvents] = await Promise.all([
      this.checkDatabase(),
      this.checkRedis(),
      this.getTraceHealth(),
      this.getProofHealth(),
      this.getSignalHealth(),
      this.getJournalHealth(),
      this.getPaymentHealth(),
      this.getAuditHealth(),
    ]);

    const components = {
      database, redis, traces, proofs, signals, journals, payments, auditEvents,
    };

    const unhealthyCount = Object.values(components).filter(c => c.status === 'unhealthy').length;
    const warningCount = Object.values(components).filter(c => c.status === 'warning').length;

    let overallStatus = 'healthy';
    if (unhealthyCount > 0) overallStatus = 'unhealthy';
    else if (warningCount > 0) overallStatus = 'degraded';

    return {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      version: '0.1.0',
      environment: process.env.NODE_ENV,
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      components,
      metrics: this.getMetrics(),
    };
  }

  async checkDatabase() {
    try {
      const state = mongoose.connection.readyState;
      const isHealthy = state === 1;

      // Check replica set
      let replicaSet = 'unknown';
      try {
        const admin = mongoose.connection.db.admin();
        const status = await admin.serverStatus();
        replicaSet = status.replicaset?.name || 'standalone';
      } catch { replicaSet = 'standalone'; }

      return {
        status: isHealthy ? 'healthy' : 'unhealthy',
        state: ['disconnected', 'connected', 'connecting', 'disconnecting'][state],
        host: mongoose.connection.host,
        name: mongoose.connection.name,
        replicaSet,
      };
    } catch (err) {
      return { status: 'unhealthy', error: err.message };
    }
  }

  async checkRedis() {
    try {
      const redisClient = getRedisClient();
      if (!redisClient) return { status: 'disabled', message: 'Redis not configured' };

      const start = Date.now();
      await redisClient.ping();
      const latency = Date.now() - start;

      return { status: 'healthy', latencyMs: latency };
    } catch (err) {
      return { status: 'unhealthy', error: err.message };
    }
  }

  async getTraceHealth() {
    try {
      const [active, completed, failed, total] = await Promise.all([
        UnifiedTrace.countDocuments({ status: 'IN_PROGRESS' }),
        UnifiedTrace.countDocuments({ status: 'COMPLETED' }),
        UnifiedTrace.countDocuments({ status: 'FAILED' }),
        UnifiedTrace.countDocuments({}),
      ]);

      const stuckTraces = await UnifiedTrace.countDocuments({
        status: 'IN_PROGRESS',
        initiatedAt: { $lt: new Date(Date.now() - 3600000) }, // > 1 hour
      });

      return {
        status: stuckTraces > 0 ? 'warning' : 'healthy',
        active, completed, failed, total, stuckTraces,
      };
    } catch (err) {
      return { status: 'unhealthy', error: err.message };
    }
  }

  async getProofHealth() {
    try {
      const [total, verified, unverified] = await Promise.all([
        RuntimeProof.countDocuments({}),
        RuntimeProof.countDocuments({ verified: true }),
        RuntimeProof.countDocuments({ verified: false }),
      ]);

      return { status: 'healthy', total, verified, unverified };
    } catch (err) {
      return { status: 'unhealthy', error: err.message };
    }
  }

  async getSignalHealth() {
    try {
      const [active, critical, warning, info] = await Promise.all([
        ComplianceSignal.countDocuments({ status: { $ne: 'resolved' } }),
        ComplianceSignal.countDocuments({ severity: 'critical', status: { $ne: 'resolved' } }),
        ComplianceSignal.countDocuments({ severity: 'warning', status: { $ne: 'resolved' } }),
        ComplianceSignal.countDocuments({ severity: 'info', status: { $ne: 'resolved' } }),
      ]);

      return {
        status: critical > 0 ? 'warning' : 'healthy',
        active, critical, warning, info,
      };
    } catch (err) {
      return { status: 'unhealthy', error: err.message };
    }
  }

  async getJournalHealth() {
    try {
      const [total, posted, draft, voided] = await Promise.all([
        JournalEntry.countDocuments({}),
        JournalEntry.countDocuments({ status: { $in: ['POSTED', 'posted'] } }),
        JournalEntry.countDocuments({ status: { $in: ['DRAFT', 'draft'] } }),
        JournalEntry.countDocuments({ status: { $in: ['VOIDED', 'voided'] } }),
      ]);

      return { status: 'healthy', total, posted, draft, voided };
    } catch (err) {
      return { status: 'unhealthy', error: err.message };
    }
  }

  async getPaymentHealth() {
    try {
      const [total, completed, failed, pending] = await Promise.all([
        Payment.countDocuments({}),
        Payment.countDocuments({ status: 'completed' }),
        Payment.countDocuments({ status: 'failed' }),
        Payment.countDocuments({ status: { $in: ['initiated', 'processing'] } }),
      ]);

      return { status: 'healthy', total, completed, failed, pending };
    } catch (err) {
      return { status: 'unhealthy', error: err.message };
    }
  }

  async getAuditHealth() {
    try {
      const [total, todayCount, chainIntegrity] = await Promise.all([
        AuditEvent.countDocuments({}),
        AuditEvent.countDocuments({
          createdAt: { $gte: new Date(new Date().setHours(0, 0, 0, 0)) },
        }),
        this.verifyAuditChain(),
      ]);

      return {
        status: chainIntegrity.isValid ? 'healthy' : 'unhealthy',
        total, todayCount, chainIntegrity,
      };
    } catch (err) {
      return { status: 'unhealthy', error: err.message };
    }
  }

  async verifyAuditChain() {
    try {
      const events = await AuditEvent.find({}).sort({ chainPosition: 1 }).limit(100);
      if (events.length === 0) return { isValid: true, checked: 0 };

      let isValid = true;
      let checked = 0;

      for (let i = 1; i < events.length; i++) {
        checked++;
        if (events[i].previousHash !== events[i - 1].hash) {
          isValid = false;
          break;
        }
      }

      return { isValid, checked, chainLength: events.length };
    } catch {
      return { isValid: false, checked: 0, error: 'Chain verification failed' };
    }
  }

  // Runtime metrics (Prometheus-compatible)
  getMetrics() {
    const uptime = (Date.now() - this.metrics.startTime) / 1000;
    const avgResponseTime = this.metrics.responseTimes.length > 0
      ? this.metrics.responseTimes.reduce((a, b) => a + b, 0) / this.metrics.responseTimes.length
      : 0;

    return {
      uptime_seconds: uptime,
      http_requests_total: this.metrics.requestCount,
      http_errors_total: this.metrics.errorCount,
      http_request_duration_ms_avg: avgResponseTime,
      memory_heap_used_bytes: process.memoryUsage().heapUsed,
      memory_heap_total_bytes: process.memoryUsage().heapTotal,
      memory_rss_bytes: process.memoryUsage().rss,
      gc_runs: process.gc ? 'available' : 'not_available',
    };
  }

  // Record request metrics
  recordRequest(durationMs, isError = false) {
    this.metrics.requestCount++;
    if (isError) this.metrics.errorCount++;
    this.metrics.responseTimes.push(durationMs);
    if (this.metrics.responseTimes.length > 1000) {
      this.metrics.responseTimes = this.metrics.responseTimes.slice(-500);
    }
  }

  // Get Grafana-compatible dashboard data
  async getDashboardData() {
    const [traceHealth, signalHealth, paymentHealth, auditHealth] = await Promise.all([
      this.getTraceHealth(),
      this.getSignalHealth(),
      this.getPaymentHealth(),
      this.getAuditHealth(),
    ]);

    return {
      traces: traceHealth,
      signals: signalHealth,
      payments: paymentHealth,
      audit: auditHealth,
      metrics: this.getMetrics(),
    };
  }
}

export default new ObservabilityService();
