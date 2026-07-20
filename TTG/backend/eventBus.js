// eventBus.js
const EventEmitter = require('events');

class EventBus extends EventEmitter {
  constructor() {
    super();
    // keep a small in-memory log for quick inspection (capped)
    this.log = [];
    this.maxLog = 200;
  }

  publish(action) {
    if (
      !action ||
      !action.type ||
      !action.userId ||
      !action.sessionId ||
      !action.clientTs
    ) {
      return;
    }
  
    const enriched = {
      ...action,
      serverTs: Date.now()
    };
  
    this.log.push(enriched);
    if (this.log.length > this.maxLog) this.log.shift();
  
    this.emit("action", enriched);
  }
  
  getLog() {
    return this.log.slice().reverse(); // newest first
  }
}

module.exports = new EventBus();
