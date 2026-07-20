import runtimeProofService from '../services/runtimeProof.service.js';
import logger from '../config/logger.js';

/**
 * Runtime Proof Capture Middleware
 * 
 * Automatically captures API responses as runtime proof
 * Attaches to critical endpoints for verification
 */

/**
 * Capture response body middleware
 */
export const captureResponseBody = (req, res, next) => {
  // Store original json method
  const originalJson = res.json;
  
  // Override json method to capture response
  res.json = function(data) {
    // Store response body in res.locals for proof capture
    res.locals.responseBody = data;
    
    // Call original json method
    return originalJson.call(this, data);
  };
  
  next();
};

/**
 * Proof capture middleware (for specific endpoints)
 */
export const captureProof = async (req, res, next) => {
  const startTime = Date.now();
  
  // Store original end method
  const originalEnd = res.end;
  
  // Override end method to capture after response is sent
  res.end = async function(...args) {
    // Call original end
    originalEnd.apply(res, args);
    
    // Capture proof asynchronously (don't block response)
    setImmediate(async () => {
      try {
        const latency_ms = Date.now() - startTime;
        const trace_id = req.headers['x-trace-id'] || res.locals.trace_id;
        
        // Only capture if trace_id exists and response was successful
        if (trace_id && res.statusCode < 400) {
          await runtimeProofService.captureAPIResponse({
            trace_id,
            endpoint: req.path,
            method: req.method,
            req,
            res,
            latency_ms,
          });
        }
      } catch (error) {
        // Log but don't throw - proof capture failure shouldn't break app
        logger.error('Proof capture error:', error);
      }
    });
  };
  
  next();
};

/**
 * Proof-enabled endpoint wrapper
 * Use this for critical endpoints that require runtime proof
 */
export const withProof = (handler) => {
  return async (req, res, next) => {
    const startTime = Date.now();
    
    try {
      // Execute handler
      await handler(req, res, next);
      
      // If handler completed successfully and trace_id exists
      const trace_id = req.headers['x-trace-id'] || res.locals.trace_id;
      if (trace_id && res.statusCode < 400) {
        const latency_ms = Date.now() - startTime;
        
        // Capture proof asynchronously
        setImmediate(async () => {
          try {
            await runtimeProofService.captureAPIResponse({
              trace_id,
              endpoint: req.path,
              method: req.method,
              req,
              res,
              latency_ms,
            });
          } catch (error) {
            logger.error('Proof capture error:', error);
          }
        });
      }
    } catch (error) {
      next(error);
    }
  };
};

/**
 * Database state capture wrapper
 * Captures before/after state for data mutations
 */
export const captureDBState = (trace_id) => {
  return {
    before: null,
    after: null,
    queries: [],
    
    async capture(beforeState, afterState, queries = []) {
      this.before = beforeState;
      this.after = afterState;
      this.queries = queries;
      
      try {
        await runtimeProofService.captureDatabaseState({
          trace_id,
          before: this.before,
          after: this.after,
          queries: this.queries,
        });
      } catch (error) {
        logger.error('DB state capture error:', error);
      }
    },
  };
};

export default {
  captureResponseBody,
  captureProof,
  withProof,
  captureDBState,
};
