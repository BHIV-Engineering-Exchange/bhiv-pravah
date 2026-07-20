# Capability Registration Guide

## Overview

This guide explains how to register new capabilities with the ARTHA BHIV ecosystem participant.

## Capability Registration Process

### Step 1: Create Capability Contract

Create a new JSON file in `contracts/capability_contracts/`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "capability_id": "ARTHA-NEW-001",
  "capability_name": "New Capability",
  "version": "1.0.0",
  "status": "STABLE",
  "owner": "Your Name",
  "description": "Description of the capability",
  "authority_owned": [
    "What this capability can do"
  ],
  "authority_explicitly_not_owned": [
    "What this capability cannot do"
  ],
  "provider_service": "backend/src/services/new.service.js",
  "provider_model": [
    "backend/src/models/NewModel.js"
  ],
  "api_endpoints": {
    "create": {
      "method": "POST",
      "path": "/api/v1/new/create",
      "auth_required": true,
      "roles": ["accountant", "admin"]
    },
    "get": {
      "method": "GET",
      "path": "/api/v1/new/get",
      "auth_required": true,
      "roles": ["*"]
    }
  },
  "input_schemas": {
    "create": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string", "minLength": 1 }
      }
    }
  },
  "output_schemas": {
    "new_entity": {
      "type": "object",
      "properties": {
        "_id": { "type": "string" },
        "name": { "type": "string" }
      }
    }
  },
  "authentication": {
    "type": "JWT",
    "header": "Authorization: Bearer <token>"
  },
  "trace_requirements": {
    "trace_id_format": "TRC-YYYYMMDD-{8hex}",
    "mandatory_stages": ["CREATED", "VALIDATED"]
  },
  "evidence_requirements": {
    "audit_trail": "Before/after snapshots on every mutation"
  },
  "failure_behavior": {
    "validation_failure": "Throws descriptive error"
  },
  "dependencies": {
    "internal": [],
    "models": ["NewModel"]
  },
  "consumers": [
    { "product": "ARTHA", "modules": ["NewModule"] }
  ],
  "replay_compatibility": {
    "deterministic": true,
    "replay_method": "Replay with same inputs produces same outputs"
  },
  "version_history": [
    { "version": "1.0.0", "date": "2026-07-04", "changes": "Initial capability" }
  ]
}
```

### Step 2: Add Route Mapping

Add route mapping to `contracts/capability_contracts/capability_route_map.json`:

```json
{
  "routes": [
    { "prefix": "/api/v1/ledger", "capability": "ARTHA-LEDGER-001" },
    { "prefix": "/api/v1/new", "capability": "ARTHA-NEW-001" },
    ...
  ]
}
```

### Step 3: Implement Service

Create the service file `backend/src/services/new.service.js`:

```javascript
import logger from '../config/logger.js';

class NewService {
  async create(data, userId) {
    // Validate input
    // Create entity
    // Record provenance
    // Record replay
    // Return result
  }

  async get(id) {
    // Fetch entity
    // Return result
  }
}

const newService = new NewService();
export default newService;
```

### Step 4: Implement Controller

Create the controller file `backend/src/controllers/new.controller.js`:

```javascript
import newService from '../services/new.service.js';
import { guardCollection } from '../middleware/policyEngine.js';

export const create = async (req, res) => {
  try {
    // Verify capability authorization
    guardCollection(req, 'newentities');

    const result = await newService.create(req.body, req.user._id);
    res.json({ success: true, data: result });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

export const get = async (req, res) => {
  try {
    const result = await newService.get(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};
```

### Step 5: Implement Routes

Create the routes file `backend/src/routes/new.routes.js`:

```javascript
import express from 'express';
import { protect } from '../middleware/auth.js';
import { create, get } from '../controllers/new.controller.js';

const router = express.Router();

router.post('/create', protect, create);
router.get('/get/:id', protect, get);

export default router;
```

### Step 6: Register Routes in server.js

Add to `backend/src/server.js`:

```javascript
import newRoutes from './routes/new.routes.js';

// ... existing routes ...
app.use('/api/v1/new', newRoutes);
```

### Step 7: Restart Application

```bash
# Development
npm run dev

# Production
docker-compose -f docker-compose.prod.yml restart
```

### Step 8: Verify Registration

```bash
# Check governance status
curl http://localhost:5000/api/v1/governance/status \
  -H "Authorization: Bearer <token>"

# Check new capability appears
curl http://localhost:5000/api/v1/governance/capabilities/ARTHA-NEW-001 \
  -H "Authorization: Bearer <token>"

# Check route resolution
curl "http://localhost:5000/api/v1/governance/capabilities/resolve?method=POST&path=/api/v1/new/create" \
  -H "Authorization: Bearer <token>"
```

### Step 9: Test Authority Boundaries

```bash
# Run verification suite
curl http://localhost:5000/api/v1/governance/verification/run \
  -H "Authorization: Bearer <token>"

# Run adversarial suite
curl http://localhost:5000/api/v1/governance/adversarial/run \
  -H "Authorization: Bearer <token>"
```

## Capability Contract Best Practices

### 1. Be Specific About Authority

```json
"authority_owned": [
  "Journal entry creation and validation",
  "Double-entry integrity enforcement",
  "Hash chain maintenance"
]
```

### 2. Be Explicit About What You Don't Own

```json
"authority_explicitly_not_owned": [
  "Invoice lifecycle (consumed via InvoiceService)",
  "User authentication (handled by auth middleware)"
]
```

### 3. Define Input Schemas

```json
"input_schemas": {
  "create_entry": {
    "type": "object",
    "required": ["description", "lines"],
    "properties": {
      "description": { "type": "string", "minLength": 1 },
      "lines": { "type": "array", "minItems": 2 }
    }
  }
}
```

### 4. Define Output Schemas

```json
"output_schemas": {
  "journal_entry": {
    "type": "object",
    "properties": {
      "_id": { "type": "string" },
      "entryNumber": { "type": "string", "pattern": "^JE-\\d{8}-\\d{4}$" },
      "status": { "type": "string", "enum": ["DRAFT", "VALIDATED", "POSTED", "VOIDED"] }
    }
  }
}
```

### 5. Document Failure Behavior

```json
"failure_behavior": {
  "validation_failure": "Throws descriptive error, entry remains DRAFT",
  "post_failure": "Entry stays VALIDATED, no ledger entries written",
  "chain_tamper": "verifyHash() returns false, post blocked"
}
```

### 6. Document Dependencies

```json
"dependencies": {
  "internal": [
    { "service": "cache.service.js", "purpose": "Response caching" },
    { "service": "traceability.service.js", "purpose": "Trace stage recording" }
  ],
  "models": ["JournalEntry", "LedgerEntry"]
}
```

### 7. Document Replay Compatibility

```json
"replay_compatibility": {
  "deterministic": true,
  "replay_method": "replayTrace(trace_id) reconstructs full lifecycle",
  "prerequisites": ["MongoDB must contain original entries"]
}
```

## Verification Checklist

After registering a new capability:

- [ ] Contract file created in `contracts/capability_contracts/`
- [ ] Route mapping added to `capability_route_map.json`
- [ ] Service implemented with proper error handling
- [ ] Controller calls `guardCollection()` for mutations
- [ ] Routes registered in server.js
- [ ] Application restarted
- [ ] Capability appears in governance status
- [ ] Route resolution works correctly
- [ ] Authority boundaries enforced
- [ ] Verification suite passes
- [ ] Adversarial suite passes
- [ ] Documentation updated
