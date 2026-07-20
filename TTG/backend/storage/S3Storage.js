// S3Storage.js - AWS S3 implementation of StorageContract
const StorageContract = require('./StorageContract');
const { S3Client, PutObjectCommand, GetObjectCommand, ListObjectsV2Command } = require('@aws-sdk/client-s3');

class S3Storage extends StorageContract {
  constructor() {
    super();
    this.s3 = new S3Client({
      region: process.env.AWS_REGION || 'us-east-1',
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
      }
    });
    this.bucket = process.env.S3_BUCKET_NAME;
  }
  
  async writeExecutionSchema(execution_id, trace_id, executionSchema, timestamp) {
    try {
      const artifact = {
        artifact_type: 'execution_schema',
        execution_id,
        trace_id,
        executionSchema,
        timestamp: timestamp || Date.now(),
        written_at: Date.now()
      };
      
      const key = `executions/${execution_id}/schema.json`;
      
      await this.s3.send(new PutObjectCommand({
        Bucket: this.bucket,
        Key: key,
        Body: JSON.stringify(artifact, null, 2),
        ContentType: 'application/json'
      }));
      
      console.log(`[S3] Wrote execution schema: ${key}`);
      return { success: true, key, artifact_type: 'execution_schema' };
    } catch (error) {
      console.error('[S3] Failed to write execution schema:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async writeExecutionStart(execution_id, trace_id, startTimestamp) {
    try {
      const artifact = {
        artifact_type: 'execution_start',
        execution_id,
        trace_id,
        start_timestamp: startTimestamp || Date.now(),
        written_at: Date.now()
      };
      
      const key = `executions/${execution_id}/start.json`;
      
      await this.s3.send(new PutObjectCommand({
        Bucket: this.bucket,
        Key: key,
        Body: JSON.stringify(artifact, null, 2),
        ContentType: 'application/json'
      }));
      
      console.log(`[S3] Wrote execution start: ${key}`);
      return { success: true, key, artifact_type: 'execution_start' };
    } catch (error) {
      console.error('[S3] Failed to write execution start:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async writeExecutionCompletion(execution_id, trace_id, completionTimestamp, status, duration) {
    try {
      const artifact = {
        artifact_type: 'execution_completion',
        execution_id,
        trace_id,
        completion_timestamp: completionTimestamp || Date.now(),
        status: status || 'completed',
        duration: duration || null,
        written_at: Date.now()
      };
      
      const key = `executions/${execution_id}/completion.json`;
      
      await this.s3.send(new PutObjectCommand({
        Bucket: this.bucket,
        Key: key,
        Body: JSON.stringify(artifact, null, 2),
        ContentType: 'application/json'
      }));
      
      console.log(`[S3] Wrote execution completion: ${key}`);
      return { success: true, key, artifact_type: 'execution_completion' };
    } catch (error) {
      console.error('[S3] Failed to write execution completion:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async appendExecutionLog(execution_id, trace_id, event, data) {
    try {
      const logEntry = {
        execution_id,
        trace_id,
        event,
        data,
        timestamp: Date.now()
      };
      
      // S3 doesn't support append, so create individual event files
      const key = `executions/${execution_id}/events/${Date.now()}_${event}.json`;
      
      await this.s3.send(new PutObjectCommand({
        Bucket: this.bucket,
        Key: key,
        Body: JSON.stringify(logEntry),
        ContentType: 'application/json'
      }));
      
      console.log(`[S3] Appended execution log: ${event}`);
      return { success: true, key, artifact_type: 'execution_log' };
    } catch (error) {
      console.error('[S3] Failed to append execution log:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async writeExecutionArtifact(execution) {
    try {
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
      
      const key = `executions/${execution.execution_id}/complete.json`;
      
      await this.s3.send(new PutObjectCommand({
        Bucket: this.bucket,
        Key: key,
        Body: JSON.stringify(artifact, null, 2),
        ContentType: 'application/json'
      }));
      
      console.log(`[S3] Wrote complete execution artifact: ${key}`);
      return { success: true, key, artifact_type: 'execution_complete' };
    } catch (error) {
      console.error('[S3] Failed to write execution artifact:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async readExecutionArtifacts(execution_id) {
    try {
      const prefix = `executions/${execution_id}/`;
      const listCommand = new ListObjectsV2Command({
        Bucket: this.bucket,
        Prefix: prefix
      });
      
      const { Contents } = await this.s3.send(listCommand);
      if (!Contents) return { success: true, artifacts: [] };
      
      const artifacts = [];
      for (const item of Contents) {
        const getCommand = new GetObjectCommand({
          Bucket: this.bucket,
          Key: item.Key
        });
        
        const response = await this.s3.send(getCommand);
        const content = await response.Body.transformToString();
        
        artifacts.push({
          key: item.Key,
          type: 'artifact',
          data: JSON.parse(content)
        });
      }
      
      return { success: true, artifacts };
    } catch (error) {
      console.error('[S3] Failed to read execution artifacts:', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async listExecutions() {
    try {
      const listCommand = new ListObjectsV2Command({
        Bucket: this.bucket,
        Prefix: 'executions/',
        Delimiter: '/'
      });
      
      const { CommonPrefixes } = await this.s3.send(listCommand);
      if (!CommonPrefixes) return { success: true, executions: [] };
      
      const executions = CommonPrefixes.map(prefix => {
        const match = prefix.Prefix.match(/executions\/([^\/]+)\//);
        return match ? match[1] : null;
      }).filter(Boolean);
      
      return { success: true, executions };
    } catch (error) {
      console.error('[S3] Failed to list executions:', error.message);
      return { success: false, error: error.message };
    }
  }
}

module.exports = S3Storage;
