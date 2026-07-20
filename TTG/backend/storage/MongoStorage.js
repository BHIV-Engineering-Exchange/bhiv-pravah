// MongoStorage.js - MongoDB implementation of StorageContract
const StorageContract = require('./StorageContract');
const { MongoClient } = require('mongodb');

class MongoStorage extends StorageContract {
  constructor() {
    super();
    this.client = null;
    this.db = null;
    this.collections = {};
  }
  
  async connect() {
    if (this.client) return;
    
    // Use separate bucket URI if provided, otherwise fall back to main MONGO_URI
    const uri = process.env.BUCKET_MONGO_URI || process.env.MONGO_URI || process.env.MONGODB_URI || 'mongodb://localhost:27017';
    const dbName = process.env.BUCKET_DB_NAME || process.env.MONGODB_DB_NAME || 'execution_artifacts';
    
    this.client = new MongoClient(uri);
    await this.client.connect();
    this.db = this.client.db(dbName);
    
    this.collections = {
      schemas: this.db.collection('execution_schemas'),
      starts: this.db.collection('execution_starts'),
      completions: this.db.collection('execution_completions'),
      logs: this.db.collection('execution_logs'),
      artifacts: this.db.collection('execution_artifacts')
    };
    
    // Create indexes
    await this.collections.schemas.createIndex({ execution_id: 1 });
    await this.collections.logs.createIndex({ execution_id: 1, timestamp: 1 });
    await this.collections.artifacts.createIndex({ execution_id: 1 });
    
    console.log(`[MONGO] Connected to bucket storage: ${dbName}`);
  }
  
  async writeExecutionSchema(execution_id, trace_id, executionSchema, timestamp) {
    try {
      await this.connect();
      
      const artifact = {
        artifact_type: 'execution_schema',
        execution_id,
        trace_id,
        executionSchema,
        timestamp: timestamp || Date.now(),
        written_at: Date.now()
      };
      
      await this.collections.schemas.insertOne(artifact);
      console.log(`[MONGO] Wrote execution schema: ${execution_id}`);
      
      return { success: true, artifact_type: 'execution_schema' };
    } catch (error) {
      console.error('[MONGO] Failed to write execution schema:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async writeExecutionStart(execution_id, trace_id, startTimestamp) {
    try {
      await this.connect();
      
      const artifact = {
        artifact_type: 'execution_start',
        execution_id,
        trace_id,
        start_timestamp: startTimestamp || Date.now(),
        written_at: Date.now()
      };
      
      await this.collections.starts.insertOne(artifact);
      console.log(`[MONGO] Wrote execution start: ${execution_id}`);
      
      return { success: true, artifact_type: 'execution_start' };
    } catch (error) {
      console.error('[MONGO] Failed to write execution start:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async writeExecutionCompletion(execution_id, trace_id, completionTimestamp, status, duration) {
    try {
      await this.connect();
      
      const artifact = {
        artifact_type: 'execution_completion',
        execution_id,
        trace_id,
        completion_timestamp: completionTimestamp || Date.now(),
        status: status || 'completed',
        duration: duration || null,
        written_at: Date.now()
      };
      
      await this.collections.completions.insertOne(artifact);
      console.log(`[MONGO] Wrote execution completion: ${execution_id}`);
      
      return { success: true, artifact_type: 'execution_completion' };
    } catch (error) {
      console.error('[MONGO] Failed to write execution completion:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async appendExecutionLog(execution_id, trace_id, event, data) {
    try {
      await this.connect();
      
      const logEntry = {
        execution_id,
        trace_id,
        event,
        data,
        timestamp: Date.now()
      };
      
      await this.collections.logs.insertOne(logEntry);
      console.log(`[MONGO] Appended execution log: ${event}`);
      
      return { success: true, artifact_type: 'execution_log' };
    } catch (error) {
      console.error('[MONGO] Failed to append execution log:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async writeExecutionArtifact(execution) {
    try {
      await this.connect();
      
      const artifact = {
        artifact_type: 'execution_complete',
        execution_id: execution.execution_id,
        trace_id: execution.trace_id,
        user_id: execution.user_id,
        executionSchema: execution.executionSchema,
        status: execution.status,
        jobs: execution.jobs,
        receivedAt: execution.receivedAt,
        startedAt: execution.startedAt,
        completedAt: execution.completedAt,
        duration: execution.completedAt ? execution.completedAt - execution.startedAt : null,
        error: execution.error,
        written_at: Date.now()
      };
      
      await this.collections.artifacts.insertOne(artifact);
      console.log(`[MONGO] Wrote complete execution artifact: ${execution.execution_id}`);
      
      return { success: true, artifact_type: 'execution_complete' };
    } catch (error) {
      console.error('[MONGO] Failed to write execution artifact:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async readExecutionArtifacts(execution_id) {
    try {
      await this.connect();
      
      const artifacts = [];
      
      const schema = await this.collections.schemas.findOne({ execution_id });
      if (schema) artifacts.push({ type: 'schema', data: schema });
      
      const start = await this.collections.starts.findOne({ execution_id });
      if (start) artifacts.push({ type: 'start', data: start });
      
      const completion = await this.collections.completions.findOne({ execution_id });
      if (completion) artifacts.push({ type: 'completion', data: completion });
      
      const logs = await this.collections.logs.find({ execution_id }).sort({ timestamp: 1 }).toArray();
      if (logs.length) artifacts.push({ type: 'logs', entries: logs });
      
      const complete = await this.collections.artifacts.findOne({ execution_id });
      if (complete) artifacts.push({ type: 'complete', data: complete });
      
      return { success: true, artifacts };
    } catch (error) {
      console.error('[MONGO] Failed to read execution artifacts:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async listExecutions() {
    try {
      await this.connect();
      
      const executions = await this.collections.artifacts
        .find({})
        .project({ execution_id: 1, trace_id: 1, status: 1, written_at: 1 })
        .sort({ written_at: -1 })
        .toArray();
      
      return { success: true, executions };
    } catch (error) {
      console.error('[MONGO] Failed to list executions:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async close() {
    if (this.client) {
      await this.client.close();
      console.log('[MONGO] Closed MongoDB connection');
    }
  }
}

module.exports = MongoStorage;
