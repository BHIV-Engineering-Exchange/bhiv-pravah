# Integration Guide

## Overview

This guide explains how to integrate with the ARTHA governance system as a BHIV ecosystem participant.

## Prerequisites

- Node.js 18+
- MongoDB 7+
- Redis 7+ (optional, for caching)
- Docker & Docker Compose (for production)

## Quick Start

### 1. Clone and Install

```bash
git clone <repo-url>
cd AI-Artha-main
cd backend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required variables:
- `MONGODB_URI` — MongoDB connection string
- `JWT_SECRET` — JWT signing secret
- `HMAC_SECRET` — HMAC signing secret for hash chain

### 3. Start Development Server

```bash
npm run dev
```

The server starts on port 5000 with all governance services initialized.

### 4. Verify Governance Status

```bash
# Login first
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'

# Check governance status
curl http://localhost:5000/api/v1/governance/status \
  -H "Authorization: Bearer <token>"
```

## API Integration

### Authentication

All governance endpoints require JWT authentication:

```bash
Authorization: Bearer <jwt_token>
```

### Capability Registry

```bash
# List all capabilities
GET /api/v1/governance/capabilities

# Get specific capability
GET /api/v1/governance/capabilities/ARTHA-LEDGER-001

# Verify all contracts
GET /api/v1/governance/capabilities/verify

# Resolve route to capability
GET /api/v1/governance/capabilities/resolve?method=GET&path=/api/v1/ledger/entries
```

### Provenance Chain

```bash
# Get provenance status
GET /api/v1/governance/provenance/status

# Verify provenance integrity
GET /api/v1/governance/provenance/verify
```

### Deterministic Replay

```bash
# Get replay statistics
GET /api/v1/governance/replay/statistics

# Get replay data
GET /api/v1/governance/replay/:replayId

# Generate replay proof
GET /api/v1/governance/replay/:replayId/proof

# Verify replay determinism
POST /api/v1/governance/replay/:replayId/verify
Body: { "actualOutput": {...} }
```

### Circuit Breakers

```bash
# Get circuit breaker status
GET /api/v1/governance/circuit-breakers

# Reset circuit breaker
POST /api/v1/governance/circuit-breakers/:name/reset
```

### Verification

```bash
# Run verification suite
GET /api/v1/governance/verification/run

# Get verification history
GET /api/v1/governance/verification/history
```

### Adversarial Testing

```bash
# Run adversarial suite
GET /api/v1/governance/adversarial/run

# Get adversarial history
GET /api/v1/governance/adversarial/history
```

### Deployment Evidence

```bash
# Get evidence manifest
GET /api/v1/governance/evidence/manifest

# Get evidence by category
GET /api/v1/governance/evidence/:category
```

## Integration Patterns

### Pattern 1: Capability-Aware Service

```javascript
import capabilityRegistry from '../services/capabilityRegistry.service.js';

class MyService {
  async processData(data, req) {
    // Check capability authorization
    const capability = capabilityRegistry.getCapability(req.capability);
    if (!capability) {
      throw new Error('No capability context');
    }

    // Validate input against contract
    const validation = capabilityRegistry.validateInput(
      req.capability,
      'process_data',
      data
    );
    if (!validation.valid) {
      throw new Error(`Input validation failed: ${validation.error}`);
    }

    // Process data...
  }
}
```

### Pattern 2: Provenance-Aware Operation

```javascript
import provenanceChain from '../services/provenanceChain.service.js';

class MyService {
  async performOperation(operation) {
    // Record the operation
    provenanceChain.append({
      type: 'OPERATION_PERFORMED',
      operation: operation.name,
      details: operation.details,
    });

    // Perform operation...

    // Record result
    provenanceChain.append({
      type: 'OPERATION_COMPLETED',
      operation: operation.name,
      result: 'success',
    });
  }
}
```

### Pattern 3: Circuit Breaker Protection

```javascript
import circuitBreaker from '../services/circuitBreaker.service.js';

class ExternalService {
  async callExternalAPI(data) {
    if (!circuitBreaker.canExecute('external_api')) {
      throw new Error('Circuit breaker OPEN — external API unavailable');
    }

    try {
      const result = await this._callAPI(data);
      circuitBreaker.recordSuccess('external_api');
      return result;
    } catch (err) {
      circuitBreaker.recordFailure('external_api');
      throw err;
    }
  }
}
```

### Pattern 4: Replay Recording

```javascript
import deterministicReplay from '../services/deterministicReplay.service.js';

class MyService {
  async executeWithReplay(req, res) {
    const startTime = Date.now();

    try {
      // Execute operation
      const result = await this._execute(req);

      // Record execution for replay
      deterministicReplay.recordExecution({
        trace_id: req.trace_id,
        operation: 'my_operation',
        method: req.method,
        path: req.path,
        body: req.body,
        user_id: req.user?._id,
        capability: req.capability,
        status_code: 200,
        response: result,
      });

      return result;
    } catch (err) {
      // Record failed execution
      deterministicReplay.recordExecution({
        trace_id: req.trace_id,
        operation: 'my_operation',
        method: req.method,
        path: req.path,
        body: req.body,
        user_id: req.user?._id,
        capability: req.capability,
        status_code: err.statusCode || 500,
        error: err.message,
      });

      throw err;
    }
  }
}
```

## Testing Integration

### Run Verification Suite

```bash
# Login and get token
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@artha.com","password":"password"}' | jq -r '.data.token')

# Run verification
curl http://localhost:5000/api/v1/governance/verification/run \
  -H "Authorization: Bearer $TOKEN"
```

### Run Adversarial Suite

```bash
curl http://localhost:5000/api/v1/governance/adversarial/run \
  -H "Authorization: Bearer $TOKEN"
```

### Check Circuit Breakers

```bash
curl http://localhost:5000/api/v1/governance/circuit-breakers \
  -H "Authorization: Bearer $TOKEN"
```

## Docker Integration

```bash
# Build and start
docker-compose -f docker-compose.dev.yml up -d

# Check governance status
curl http://localhost:5000/api/v1/governance/status \
  -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting

### Capability Not Found
- Verify contracts exist in `contracts/capability_contracts/`
- Check `capability_route_map.json` has correct mappings
- Review server logs for contract loading errors

### Policy Engine Blocking
- Check capability is not read-only for write operations
- Verify collection is not in blocked_mutations
- Review policy decision logs

### Circuit Breaker Open
- Check dependency health (MongoDB, Redis, etc.)
- Wait for recovery window or force reset
- Review failure logs for root cause
