class AdaptiveFailover {
  constructor() {
    this.safeDefaults = {
      // API response defaults
      chatResponse: { response: "I'm here to help. How can I assist you today?" },
      lessonContent: { title: "Learning Resource", content: "Content loading..." },
      subjectList: [{ id: 1, name: "General Topics", description: "Available subjects" }],
      practiceQuestions: [],

      // UI state defaults  
      loadingState: false,
      errorState: false,
      data: null,

      // Component-specific defaults
      avatarImage: null,
      userKarma: 120,
      studyTime: 0,
      notifications: []
    };

    // Track recent failures to prevent cascade
    this.failureWindow = new Map();
    this.failureThreshold = 3; // Max failures per component in 30 seconds
  }

  /**
   * Safe API call wrapper with automatic fallback
   */
  async safeApiCall(apiFunction, componentContext = 'generic') {
    try {
      // Check failure threshold to prevent cascade
      if (this.isComponentOverFailureThreshold(componentContext)) {
        return this.getDefaultResponse(componentContext);
      }

      const result = await apiFunction();
      
      // Reset failure count on success
      this.resetFailureCount(componentContext);
      
      return this.validateApiResponse(result) ? result : this.getDefaultResponse(componentContext);
    } catch (error) {
      // Record failure
      this.recordFailure(componentContext);
      
      // Return safe default without exposing error
      return this.getDefaultResponse(componentContext);
    }
  }

  /**
   * Validate API response structure
   */
  validateApiResponse(response) {
    if (!response) return false;
    
    // Check for common error indicators
    if (response.error || response.detail || response.message?.includes('error')) {
      return false;
    }
    
    return true;
  }

  /**
   * Get safe default response for a context
   */
  getDefaultResponse(context) {
    switch (context) {
      case 'chat':
        return this.safeDefaults.chatResponse;
      case 'lesson':
        return this.safeDefaults.lessonContent;
      case 'subject':
        return this.safeDefaults.subjectList;
      case 'practice':
        return this.safeDefaults.practiceQuestions;
      default:
        return this.safeDefaults.chatResponse;
    }
  }

  /**
   * Record component failure for cascade prevention
   */
  recordFailure(context) {
    const now = Date.now();
    const failures = this.failureWindow.get(context) || [];
    failures.push(now);
    
    // Keep only failures from last 30 seconds
    const recentFailures = failures.filter(time => (now - time) < 30000);
    this.failureWindow.set(context, recentFailures);
  }

  /**
   * Check if component is over failure threshold
   */
  isComponentOverFailureThreshold(context) {
    const failures = this.failureWindow.get(context) || [];
    return failures.length >= this.failureThreshold;
  }

  /**
   * Reset failure count for component
   */
  resetFailureCount(context) {
    this.failureWindow.delete(context);
  }

  /**
   * Safe renderer that prevents crashes
   */
  safeRender(renderFunction, fallbackComponent = null) {
    try {
      const result = renderFunction();
      return result;
    } catch (error) {
      // Silently absorb rendering errors
      console.warn(`Safe render prevented UI crash in ${renderFunction.name || 'anonymous'}:`, error);
      return fallbackComponent || this.createSafePlaceholder();
    }
  }

  /**
   * Create safe placeholder UI
   */
  createSafePlaceholder() {
    return {
      type: 'placeholder',
      props: {
        children: 'Content loading...',
        className: 'text-gray-400 italic'
      }
    };
  }

  /**
   * Safe data accessor with fallback
   */
  safeGet(data, path, defaultValue = null) {
    try {
      return path.split('.').reduce((obj, key) => obj?.[key], data) ?? defaultValue;
    } catch {
      return defaultValue;
    }
  }

  /**
   * Safe state setter that prevents invalid states
   */
  safeSetState(setterFunction, value) {
    try {
      // Validate value before setting
      if (this.isValidStateValue(value)) {
        setterFunction(value);
      } else {
        setterFunction(this.safeDefaults.data);
      }
    } catch (error) {
      // Absorb state setting errors
      console.warn('Safe state set prevented error:', error);
    }
  }

  /**
   * Validate state value
   */
  isValidStateValue(value) {
    if (value === undefined || value === null) return false;
    if (typeof value === 'object' && Object.keys(value).length === 0 && value.constructor === Object) return false;
    return true;
  }

  /**
   * Safe timeout that doesn't crash on callback error
   */
  safeTimeout(callback, delay) {
    return setTimeout(() => {
      try {
        callback();
      } catch (error) {
        console.warn('Safe timeout prevented error:', error);
      }
    }, delay);
  }

  /**
   * Safe interval that doesn't crash on callback error
   */
  safeInterval(callback, interval) {
    return setInterval(() => {
      try {
        callback();
      } catch (error) {
        console.warn('Safe interval prevented error:', error);
      }
    }, interval);
  }

  /**
   * Handle navigation to potentially invalid routes
   */
  safeNavigate(to, fallback = '/') {
    try {
      // In a real implementation, this would use router methods
      // For now, return the destination or fallback
      return to || fallback;
    } catch (error) {
      console.warn('Safe navigation prevented error:', error);
      return fallback;
    }
  }

  /**
   * Reset failure tracking (for demo reset)
   */
  resetTracking() {
    this.failureWindow.clear();
  }
}

// Singleton instance
const adaptiveFailover = new AdaptiveFailover();

// Export for use in components
export { adaptiveFailover };

// Convenience functions for common use cases

export const safeChatCall = async (messageData) => {
  return adaptiveFailover.safeApiCall(async () => {
    // This would normally call the actual API
    // For demo safety, return a safe response
    return adaptiveFailover.getDefaultResponse('chat');
  }, 'chat');
};

export const safeLessonLoad = async (lessonId) => {
  return adaptiveFailover.safeApiCall(async () => {
    // This would normally fetch lesson data
    return adaptiveFailover.getDefaultResponse('lesson');
  }, 'lesson');
};

export const safeSubjectLoad = async () => {
  return adaptiveFailover.safeApiCall(async () => {
    // This would normally fetch subjects
    return adaptiveFailover.getDefaultResponse('subject');
  }, 'subject');
};

export const safePracticeLoad = async (topicId) => {
  return adaptiveFailover.safeApiCall(async () => {
    // This would normally fetch practice questions
    return adaptiveFailover.getDefaultResponse('practice');
  }, 'practice');
};

export const safeRenderWrapper = (renderFn, fallback = null) => {
  return adaptiveFailover.safeRender(renderFn, fallback);
};