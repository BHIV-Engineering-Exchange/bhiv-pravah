// LocalStorage.js - Local filesystem implementation of StorageContract
const StorageContract = require('./StorageContract');
const fs = require('fs').promises;
const path = require('path');

class LocalStorage extends StorageContract {
  constructor(bucketDir = path.join(__dirname, '../bucket_artifacts')) {
    super();
    this.bucketDir = bucketDir;
  }
  
  async ensureDir() {
    await fs.mkdir(this.bucketDir, { recursive: true });
  }
  
  async writeExecutionSchema(execution_id, trace_id, executionSchema, timestamp) {
    try {
      await this.ensureDir();
      
      const artifact = {
        artifact_type: 'execution_schema',
        execution_id,
        trace_id,
        executionSchema,
        timestamp: timestamp || Date.now(),
        written_at: Date.now()
      };
      
      const filename = `execution_${execution_id}_schema.json`;
      const filepath = path.join(this.bucketDir, filename);
      
      await fs.writeFile(filepath, JSON.stringify(artifact, null, 2));
      console.log(`[LOCAL] Wrote execution schema: ${filename}`);
      
      return { success: true, filepath, artifact_type: 'execution_schema' };
    } catch (error) {
      console.error('[LOCAL] Failed to write execution schema:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async writeExecutionStart(execution_id, trace_id, startTimestamp) {
    try {
      await this.ensureDir();
      
      const artifact = {
        artifact_type: 'execution_start',
        execution_id,
        trace_id,
        start_timestamp: startTimestamp || Date.now(),
        written_at: Date.now()
      };
      
      const filename = `execution_${execution_id}_start.json`;
      const filepath = path.join(this.bucketDir, filename);
      
      await fs.writeFile(filepath, JSON.stringify(artifact, null, 2));
      console.log(`[LOCAL] Wrote execution start: ${filename}`);
      
      return { success: true, filepath, artifact_type: 'execution_start' };
    } catch (error) {
      console.error('[LOCAL] Failed to write execution start:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async writeExecutionCompletion(execution_id, trace_id, completionTimestamp, status, duration) {
    try {
      await this.ensureDir();
      
      const artifact = {
        artifact_type: 'execution_completion',
        execution_id,
        trace_id,
        completion_timestamp: completionTimestamp || Date.now(),
        status: status || 'completed',
        duration: duration || null,
        written_at: Date.now()
      };
      
      const filename = `execution_${execution_id}_completion.json`;
      const filepath = path.join(this.bucketDir, filename);
      
      await fs.writeFile(filepath, JSON.stringify(artifact, null, 2));
      console.log(`[LOCAL] Wrote execution completion: ${filename}`);
      
      return { success: true, filepath, artifact_type: 'execution_completion' };
    } catch (error) {
      console.error('[LOCAL] Failed to write execution completion:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async appendExecutionLog(execution_id, trace_id, event, data) {
    try {
      await this.ensureDir();
      
      const logEntry = {
        execution_id,
        trace_id,
        event,
        data,
        timestamp: Date.now()
      };
      
      const filename = `execution_${execution_id}_log.jsonl`;
      const filepath = path.join(this.bucketDir, filename);
      
      await fs.appendFile(filepath, JSON.stringify(logEntry) + '\n');
      console.log(`[LOCAL] Appended execution log: ${event}`);
      
      return { success: true, filepath, artifact_type: 'execution_log' };
    } catch (error) {
      console.error('[LOCAL] Failed to append execution log:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async writeExecutionArtifact(execution) {
    try {
      await this.ensureDir();
      
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
      
      const filename = `execution_${execution.execution_id}_complete.json`;
      const filepath = path.join(this.bucketDir, filename);
      
      await fs.writeFile(filepath, JSON.stringify(artifact, null, 2));
      console.log(`[LOCAL] Wrote complete execution artifact: ${filename}`);
      
      return { success: true, filepath, artifact_type: 'execution_complete' };
    } catch (error) {
      console.error('[LOCAL] Failed to write execution artifact:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async readExecutionArtifacts(execution_id) {
    try {
      const files = await fs.readdir(this.bucketDir);
      const executionFiles = files.filter(f => f.startsWith(`execution_${execution_id}`));
      
      const artifacts = [];
      for (const file of executionFiles) {
        const filepath = path.join(this.bucketDir, file);
        const content = await fs.readFile(filepath, 'utf8');
        
        if (file.endsWith('.jsonl')) {
          const lines = content.trim().split('\n').filter(l => l);
          artifacts.push({ file, type: 'log', entries: lines.map(l => JSON.parse(l)) });
        } else {
          artifacts.push({ file, type: 'artifact', data: JSON.parse(content) });
        }
      }
      
      return { success: true, artifacts };
    } catch (error) {
      console.error('[LOCAL] Failed to read execution artifacts:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async listExecutions() {
    try {
      await this.ensureDir();
      const files = await fs.readdir(this.bucketDir);
      
      const executionIds = new Set();
      files.forEach(file => {
        const match = file.match(/^execution_([^_]+)_/);
        if (match) executionIds.add(match[1]);
      });
      
      return { success: true, executions: Array.from(executionIds) };
    } catch (error) {
      console.error('[LOCAL] Failed to list executions:', error.message);
      return { success: false, error: error.message };
    }
  }
}

module.exports = LocalStorage;
