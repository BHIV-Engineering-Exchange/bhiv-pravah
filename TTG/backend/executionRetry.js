// executionRetry.js - Execution failure recovery with retry logic
const bucketWriter = require('./bucketWriter');
const EventEmitter = require('events');

const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 2000; // 2 seconds between retries

class ExecutionRetry extends EventEmitter {
  constructor() {
    super();
    this.retryState = new Map(); // execution_id -> { attempts, lastError }
  }

  async executeWithRetry(execution_id, trace_id, executionFn, context = {}) {
    const retryKey = execution_id;
    
    if (!this.retryState.has(retryKey)) {
      this.retryState.set(retryKey, { attempts: 0, lastError: null });
    }

    const state = this.retryState.get(retryKey);
    
    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
      state.attempts = attempt + 1;
      
      try {
        console.log(`[RETRY] Execution ${execution_id} - Attempt ${attempt + 1}/${MAX_RETRIES + 1}`);
        
        // Log retry attempt
        await bucketWriter.appendExecutionLog(
          execution_id,
          trace_id,
          'execution_attempt',
          { attempt: attempt + 1, max_retries: MAX_RETRIES + 1 }
        );

        // Execute the function
        const result = await executionFn();
        
        // Success - log and cleanup
        console.log(`[RETRY] Execution ${execution_id} succeeded on attempt ${attempt + 1}`);
        await bucketWriter.appendExecutionLog(
          execution_id,
          trace_id,
          'execution_success',
          { attempt: attempt + 1, result }
        );
        
        this.retryState.delete(retryKey);
        return { success: true, result, attempts: attempt + 1 };

      } catch (error) {
        state.lastError = error.message;
        
        console.error(`[RETRY] Execution ${execution_id} failed on attempt ${attempt + 1}:`, error.message);
        
        // Log failure
        await bucketWriter.appendExecutionLog(
          execution_id,
          trace_id,
          'execution_failure',
          {
            attempt: attempt + 1,
            error: error.message,
            stack: error.stack,
            willRetry: attempt < MAX_RETRIES
          }
        );
        
        // Emit retry event
        if (attempt < MAX_RETRIES) {
          this.emit('execution:retry', {
            execution_id,
            trace_id,
            attempt: attempt + 1,
            error: error.message
          });
        }

        // If max retries reached, give up
        if (attempt >= MAX_RETRIES) {
          console.error(`[RETRY] Execution ${execution_id} failed after ${MAX_RETRIES + 1} attempts`);
          
          await bucketWriter.appendExecutionLog(
            execution_id,
            trace_id,
            'execution_failed_final',
            {
              total_attempts: MAX_RETRIES + 1,
              final_error: error.message,
              all_errors: state.lastError
            }
          );
          
          this.retryState.delete(retryKey);
          return {
            success: false,
            error: error.message,
            attempts: MAX_RETRIES + 1,
            finalFailure: true
          };
        }

        // Wait before retry
        console.log(`[RETRY] Waiting ${RETRY_DELAY_MS}ms before retry...`);
        await this.delay(RETRY_DELAY_MS);
      }
    }
  }

  async retryExecution(execution, executionFn) {
    const { execution_id, trace_id } = execution;
    
    return await this.executeWithRetry(
      execution_id,
      trace_id,
      executionFn,
      { execution }
    );
  }

  getRetryState(execution_id) {
    return this.retryState.get(execution_id) || null;
  }

  clearRetryState(execution_id) {
    this.retryState.delete(execution_id);
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Singleton instance
const executionRetry = new ExecutionRetry();

module.exports = executionRetry;
