class SafetyGovernorV2 {
  constructor() {
    // Central state lock - only one state can be active
    this.activeState = null;
    this.stateStartTime = null;
    
    // Cooldown tracking per state (milliseconds)
    this.cooldowns = {
      'avatar_drag': 500,
      'avatar_chat': 300,
      'karma_notification': 1000,
      'navigation_sidebar': 200,
      'navigation_language': 200,
      'timer_active': 100,
      'chat_loading': 500
    };
    
    // Last execution timestamps
    this.lastExecuted = {};
    
    // Cleanup registry
    this.cleanupRegistry = new Map();
    
    // Signal drop counter
    this.droppedSignals = 0;
  }

  /**
   * Request to activate an adaptive state
   * @param {string} stateId - Unique identifier for the state
   * @param {Function} enterFn - Function to execute when entering state
   * @param {Function} exitFn - Function to execute when exiting state  
   * @param {Object} cleanupItems - Items that need cleanup (timers, listeners, etc.)
   * @returns {boolean} - Whether state was activated
   */
  requestState(stateId, enterFn, exitFn, cleanupItems = {}) {
    // Safety check: if state is unknown, ignore
    if (!this.isValidState(stateId)) {
      this.droppedSignals++;
      return false;
    }

    // Block if same state is already active (re-entry prevention)
    if (this.activeState === stateId) {
      return false;
    }

    // Block if cooldown period hasn't elapsed
    if (this.isInCooldown(stateId)) {
      this.droppedSignals++;
      return false;
    }

    // Force cleanup of current state before switching
    if (this.activeState) {
      this.forceCleanup();
    }

    // Activate new state
    try {
      this.activeState = stateId;
      this.stateStartTime = Date.now();
      this.lastExecuted[stateId] = Date.now();
      
      // Register cleanup items
      this.registerCleanup(stateId, cleanupItems);
      
      // Execute enter function
      if (typeof enterFn === 'function') {
        enterFn();
      }
      
      return true;
    } catch (error) {
      // If activation fails, hard reset to neutral
      this.hardReset();
      return false;
    }
  }

  /**
   * Safely exit current state
   */
  exitState() {
    if (!this.activeState) return;

    try {
      // Execute registered cleanup
      this.executeCleanup(this.activeState);
      
      // Clear state
      this.activeState = null;
      this.stateStartTime = null;
    } catch (error) {
      // Hard reset if cleanup fails
      this.hardReset();
    }
  }

  /**
   * Force immediate cleanup of current state
   */
  forceCleanup() {
    if (this.activeState) {
      this.executeCleanup(this.activeState);
      this.activeState = null;
      this.stateStartTime = null;
    }
  }

  /**
   * Register cleanup items for a state
   */
  registerCleanup(stateId, items) {
    this.cleanupRegistry.set(stateId, {
      timers: items.timers || [],
      listeners: items.listeners || [],
      observers: items.observers || [],
      cssClasses: items.cssClasses || [],
      intervals: items.intervals || []
    });
  }

  /**
   * Execute cleanup for a specific state
   */
  executeCleanup(stateId) {
    const cleanupItems = this.cleanupRegistry.get(stateId);
    if (!cleanupItems) return;

    // Clear all timers
    cleanupItems.timers.forEach(timer => {
      if (timer && typeof timer === 'number') {
        clearTimeout(timer);
      }
    });

    // Remove event listeners
    cleanupItems.listeners.forEach(({element, event, handler}) => {
      if (element && element.removeEventListener) {
        element.removeEventListener(event, handler);
      }
    });

    // Disconnect observers
    cleanupItems.observers.forEach(observer => {
      if (observer && observer.disconnect) {
        observer.disconnect();
      }
    });

    // Clear intervals
    cleanupItems.intervals.forEach(interval => {
      if (interval && typeof interval === 'number') {
        clearInterval(interval);
      }
    });

    // Remove cleanup registration
    this.cleanupRegistry.delete(stateId);
  }

  /**
   * Hard reset to neutral state
   */
  hardReset() {
    // Force cleanup of everything
    this.cleanupRegistry.forEach((_, stateId) => {
      this.executeCleanup(stateId);
    });
    
    this.cleanupRegistry.clear();
    this.activeState = null;
    this.stateStartTime = null;
    this.droppedSignals = 0;
  }

  /**
   * Check if state is in cooldown period
   */
  isInCooldown(stateId) {
    const lastTime = this.lastExecuted[stateId];
    if (!lastTime) return false;
    
    const cooldownPeriod = this.cooldowns[stateId] || 0;
    return (Date.now() - lastTime) < cooldownPeriod;
  }

  /**
   * Validate state identifier
   */
  isValidState(stateId) {
    const validStates = [
      'avatar_drag', 'avatar_chat', 'karma_notification',
      'navigation_sidebar', 'navigation_language', 
      'timer_active', 'chat_loading'
    ];
    return validStates.includes(stateId);
  }

  /**
   * Get current system status
   */
  getStatus() {
    return {
      activeState: this.activeState,
      activeDuration: this.activeState ? Date.now() - this.stateStartTime : 0,
      droppedSignals: this.droppedSignals,
      statesInCooldown: this.getStatesInCooldown()
    };
  }

  /**
   * Get list of states currently in cooldown
   */
  getStatesInCooldown() {
    const now = Date.now();
    return Object.keys(this.cooldowns).filter(stateId => {
      const lastTime = this.lastExecuted[stateId];
      if (!lastTime) return false;
      return (now - lastTime) < this.cooldowns[stateId];
    });
  }

  /**
   * Drop strategy for excess signals
   * Always drops - never queues
   */
  handleExcessSignal() {
    this.droppedSignals++;
    return false;
  }
}

// Singleton instance
const safetyGovernor = new SafetyGovernorV2();

// Export for use in components
export { safetyGovernor };

// Convenience wrappers for common adaptive states

export const avatarDragGovernor = {
  start: (cleanupItems) => safetyGovernor.requestState(
    'avatar_drag',
    () => { /* Drag started */ },
    () => { /* Drag ended */ },
    cleanupItems
  ),
  stop: () => safetyGovernor.exitState()
};

export const avatarChatGovernor = {
  open: (cleanupItems) => safetyGovernor.requestState(
    'avatar_chat',
    () => { /* Chat opened */ },
    () => { /* Chat closed */ },
    cleanupItems
  ),
  close: () => safetyGovernor.exitState()
};

export const karmaNotificationGovernor = {
  show: (cleanupItems) => safetyGovernor.requestState(
    'karma_notification',
    () => { /* Notification shown */ },
    () => { /* Notification hidden */ },
    cleanupItems
  )
};

export const navigationGovernor = {
  sidebar: {
    open: (cleanupItems) => safetyGovernor.requestState(
      'navigation_sidebar',
      () => { /* Sidebar opened */ },
      () => { /* Sidebar closed */ },
      cleanupItems
    ),
    close: () => safetyGovernor.exitState()
  },
  language: {
    open: (cleanupItems) => safetyGovernor.requestState(
      'navigation_language',
      () => { /* Language menu opened */ },
      () => { /* Language menu closed */ },
      cleanupItems
    ),
    close: () => safetyGovernor.exitState()
  }
};

export const timerGovernor = {
  activate: (cleanupItems) => safetyGovernor.requestState(
    'timer_active',
    () => { /* Timer activated */ },
    () => { /* Timer deactivated */ },
    cleanupItems
  )
};

export const chatLoadingGovernor = {
  start: (cleanupItems) => safetyGovernor.requestState(
    'chat_loading',
    () => { /* Loading started */ },
    () => { /* Loading ended */ },
    cleanupItems
  ),
  stop: () => safetyGovernor.exitState()
};