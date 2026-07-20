const EventEmitter = require('events');

class EngineMonitor extends EventEmitter {
  constructor() {
    super();
    this.connected = false;
    this.lastHeartbeat = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.lastTelemetry = null;
  }

  setConnected(status) {
    const changed = this.connected !== status;
    this.connected = status;
    
    if (status) {
      this.reconnectAttempts = 0;
      this.lastHeartbeat = Date.now();
    }
    
    if (changed) {
      this.emit('status_change', {
        connected: status,
        timestamp: Date.now(),
        reconnectAttempts: this.reconnectAttempts,
        healthy: status
      });
    }
  }

  recordHeartbeat() {
    this.lastHeartbeat = Date.now();
  }

  recordTelemetry(event) {
    if (!event || typeof event !== 'object') {
      console.warn('[ENGINE MONITOR] Malformed telemetry rejected');
      return false;
    }
    
    this.lastTelemetry = {
      event: event.event,
      timestamp: Date.now()
    };
    
    this.emit('telemetry', this.lastTelemetry);
    return true;
  }

  getStatus() {
    return {
      connected: this.connected,
      lastHeartbeat: this.lastHeartbeat,
      lastTelemetry: this.lastTelemetry,
      reconnectAttempts: this.reconnectAttempts,
      healthy: this.connected && (Date.now() - (this.lastHeartbeat || 0) < 10000)
    };
  }

  handleDisconnect() {
    this.setConnected(false);
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`[ENGINE] Reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      this.emit('reconnect_attempt', this.reconnectAttempts);
    } else {
      console.error('[ENGINE] Max reconnect attempts reached');
      this.emit('reconnect_failed');
    }
  }
}

const engineMonitor = new EngineMonitor();
module.exports = { engineMonitor };
