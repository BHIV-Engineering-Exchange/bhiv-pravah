/**
 * circuitBreaker.service.js
 *
 * Circuit breaker pattern for fail-safe runtime behaviour.
 * Prevents cascading failures by tracking dependency health
 * and circuiting (blocking) requests to failed dependencies.
 *
 * States: CLOSED (normal) -> OPEN (failing, blocked) -> HALF_OPEN (testing)
 */

import logger from '../config/logger.js';

const STATES = { CLOSED: 'CLOSED', OPEN: 'OPEN', HALF_OPEN: 'HALF_OPEN' };

class CircuitBreakerEntry {
  constructor(name, options = {}) {
    this.name = name;
    this.state = STATES.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    this.lastFailureTime = null;
    this.lastStateChange = new Date();
    this.options = {
      failureThreshold: options.failureThreshold || 5,
      recoveryTimeMs: options.recoveryTimeMs || 60000,
      halfOpenMaxAttempts: options.halfOpenMaxAttempts || 3,
      monitoringWindowMs: options.monitoringWindowMs || 300000,
    };
    this.halfOpenAttempts = 0;
  }

  canExecute() {
    if (this.state === STATES.CLOSED) return true;
    if (this.state === STATES.OPEN) {
      const elapsed = Date.now() - this.lastStateChange.getTime();
      if (elapsed >= this.options.recoveryTimeMs) {
        this.state = STATES.HALF_OPEN;
        this.halfOpenAttempts = 0;
        this.lastStateChange = new Date();
        logger.info(`[CIRCUIT_BREAKER] ${this.name}: OPEN -> HALF_OPEN (recovery window elapsed)`);
        return true;
      }
      return false;
    }
    if (this.state === STATES.HALF_OPEN) {
      return this.halfOpenAttempts < this.options.halfOpenMaxAttempts;
    }
    return false;
  }

  recordSuccess() {
    if (this.state === STATES.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= this.options.halfOpenMaxAttempts) {
        this.state = STATES.CLOSED;
        this.failureCount = 0;
        this.successCount = 0;
        this.halfOpenAttempts = 0;
        this.lastStateChange = new Date();
        logger.info(`[CIRCUIT_BREAKER] ${this.name}: HALF_OPEN -> CLOSED (recovery confirmed)`);
      }
    } else {
      this.failureCount = 0;
    }
  }

  recordFailure() {
    this.failureCount++;
    this.lastFailureTime = new Date();

    if (this.state === STATES.HALF_OPEN) {
      this.state = STATES.OPEN;
      this.halfOpenAttempts = 0;
      this.lastStateChange = new Date();
      logger.warn(`[CIRCUIT_BREAKER] ${this.name}: HALF_OPEN -> OPEN (recovery failed)`);
    } else if (this.failureCount >= this.options.failureThreshold) {
      this.state = STATES.OPEN;
      this.lastStateChange = new Date();
      logger.warn(
        `[CIRCUIT_BREAKER] ${this.name}: CLOSED -> OPEN ` +
        `(failures=${this.failureCount} threshold=${this.options.failureThreshold})`
      );
    }
  }

  getStatus() {
    return {
      name: this.name,
      state: this.state,
      failure_count: this.failureCount,
      success_count: this.successCount,
      last_failure: this.lastFailureTime,
      last_state_change: this.lastStateChange,
      options: this.options,
    };
  }
}

class CircuitBreakerService {
  constructor() {
    this.breakers = new Map();
    this._registerDefaults();
  }

  _registerDefaults() {
    this.register('mongodb', { failureThreshold: 3, recoveryTimeMs: 30000 });
    this.register('redis', { failureThreshold: 3, recoveryTimeMs: 30000 });
    this.register('setu_api', { failureThreshold: 3, recoveryTimeMs: 120000 });
    this.register('tantra_runtime', { failureThreshold: 5, recoveryTimeMs: 60000 });
    this.register('ocr_service', { failureThreshold: 3, recoveryTimeMs: 60000 });
    this.register('evidence_pipeline', { failureThreshold: 5, recoveryTimeMs: 30000 });
  }

  register(name, options = {}) {
    if (!this.breakers.has(name)) {
      this.breakers.set(name, new CircuitBreakerEntry(name, options));
      logger.debug(`[CIRCUIT_BREAKER] Registered: ${name}`);
    }
  }

  canExecute(name) {
    const breaker = this.breakers.get(name);
    if (!breaker) return true;
    return breaker.canExecute();
  }

  recordSuccess(name) {
    const breaker = this.breakers.get(name);
    if (breaker) breaker.recordSuccess();
  }

  recordFailure(name) {
    const breaker = this.breakers.get(name);
    if (breaker) breaker.recordFailure();
  }

  getStatus() {
    const status = {};
    for (const [name, breaker] of this.breakers) {
      status[name] = breaker.getStatus();
    }
    return status;
  }

  getOpenCircuits() {
    const open = [];
    for (const [name, breaker] of this.breakers) {
      if (breaker.state === STATES.OPEN) open.push(name);
    }
    return open;
  }

  forceReset(name) {
    const breaker = this.breakers.get(name);
    if (breaker) {
      breaker.state = STATES.CLOSED;
      breaker.failureCount = 0;
      breaker.successCount = 0;
      breaker.halfOpenAttempts = 0;
      breaker.lastStateChange = new Date();
      logger.info(`[CIRCUIT_BREAKER] ${name}: Force reset to CLOSED`);
    }
  }

  resetAll() {
    for (const name of this.breakers.keys()) {
      this.forceReset(name);
    }
  }
}

const circuitBreaker = new CircuitBreakerService();
export default circuitBreaker;
export { STATES };
