# Storage Contract System

## Overview

Pluggable artifact storage system with support for multiple backends:
- **MongoDB** - Cloud database storage
- **Local** - Filesystem storage
- **S3** - AWS cloud storage

## Architecture

```
bucketWriter.js (Adapter)
    ↓
storage/index.js (Factory)
    ↓
StorageContract (Interface)
    ↓
├── MongoStorage
├── LocalStorage
└── S3Storage
```

## Configuration

Set `STORAGE_PROVIDER` in `.env`:

```env
# Use MongoDB (default)
STORAGE_PROVIDER=mongodb
MONGODB_DB_NAME=execution_artifacts

# Use Local filesystem
STORAGE_PROVIDER=local

# Use AWS S3
STORAGE_PROVIDER=s3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your-bucket
```

## MongoDB Setup

Already configured! Uses existing MongoDB connection:
```env
MONGO_URI=mongodb+srv://...
MONGODB_DB_NAME=execution_artifacts
```

Collections created automatically:
- `execution_schemas`
- `execution_starts`
- `execution_completions`
- `execution_logs`
- `execution_artifacts`

## Usage

No code changes needed! Existing code works with any provider:

```javascript
const bucketWriter = require('./bucketWriter');

// Write artifacts (works with any storage backend)
await bucketWriter.writeExecutionSchema(exec_id, trace_id, schema);
await bucketWriter.appendExecutionLog(exec_id, trace_id, 'event', data);
await bucketWriter.writeExecutionArtifact(execution);

// Read artifacts
const result = await bucketWriter.readExecutionArtifacts(exec_id);
```

## Storage Contract Methods

All implementations must provide:

- `writeExecutionSchema(execution_id, trace_id, executionSchema, timestamp)`
- `writeExecutionStart(execution_id, trace_id, startTimestamp)`
- `writeExecutionCompletion(execution_id, trace_id, completionTimestamp, status, duration)`
- `appendExecutionLog(execution_id, trace_id, event, data)`
- `writeExecutionArtifact(execution)`
- `readExecutionArtifacts(execution_id)`
- `listExecutions()`

## Switching Providers

Change one line in `.env`:

```env
STORAGE_PROVIDER=mongodb  # MongoDB
STORAGE_PROVIDER=local    # Filesystem
STORAGE_PROVIDER=s3       # AWS S3
```

Restart server. Done!

## Adding New Storage Provider

1. Create `storage/NewStorage.js` extending `StorageContract`
2. Implement all required methods
3. Add to `storage/index.js` factory
4. Update `.env` with new provider name

## Testing

```bash
# Test with MongoDB
STORAGE_PROVIDER=mongodb node test_bucket.js

# Test with Local
STORAGE_PROVIDER=local node test_bucket.js

# Test with S3
STORAGE_PROVIDER=s3 node test_bucket.js
```
