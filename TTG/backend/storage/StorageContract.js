// StorageContract.js - Abstract storage interface for artifact persistence
class StorageContract {
  async writeExecutionSchema(execution_id, trace_id, executionSchema, timestamp) {
    throw new Error('writeExecutionSchema not implemented');
  }
  
  async writeExecutionStart(execution_id, trace_id, startTimestamp) {
    throw new Error('writeExecutionStart not implemented');
  }
  
  async writeExecutionCompletion(execution_id, trace_id, completionTimestamp, status, duration) {
    throw new Error('writeExecutionCompletion not implemented');
  }
  
  async appendExecutionLog(execution_id, trace_id, event, data) {
    throw new Error('appendExecutionLog not implemented');
  }
  
  async writeExecutionArtifact(execution) {
    throw new Error('writeExecutionArtifact not implemented');
  }
  
  async readExecutionArtifacts(execution_id) {
    throw new Error('readExecutionArtifacts not implemented');
  }
  
  async listExecutions() {
    throw new Error('listExecutions not implemented');
  }
}

module.exports = StorageContract;
