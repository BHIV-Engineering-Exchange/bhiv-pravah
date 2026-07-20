# BHIV Full Integration Pipeline

**Status**: ✅ COMPLETED - Production Ready  
**Version**: 1.0.0  
**Integration**: Prompt Runner → Creator Core → BHIV Core → Bucket  

## Overview

This is the complete BHIV integration that converts separate working components into ONE unified, production-ready pipeline. The system provides a deterministic, plug-and-play infrastructure module usable across TTG, TTV, and all BHIV products.

## Architecture

```
User Prompt 
    ↓
Prompt Runner (8003) ──→ Structured Instruction
    ↓
Creator Core (8000) ──→ Blueprint Envelope  
    ↓
BHIV Core (8001) ──→ Execution Result
    ↓
Bucket (8005) ──→ Stored Artifacts
    ↓
Integration Bridge (8004) ──→ Final Result
```

## Components

| Component | Port | Purpose | Status |
|-----------|------|---------|--------|
| **Prompt Runner** | 8003 | Convert prompts to structured instructions | ✅ Active |
| **Creator Core** | 8000 | Generate blueprints from instructions | ✅ Active |
| **BHIV Core** | 8001 | Execute blueprints through modules | ✅ Active |
| **Integration Bridge** | 8004 | Orchestrate full pipeline | ✅ Active |
| **BHIV Bucket** | 8005 | Store and retrieve artifacts | ✅ Active |

## Quick Start

### 1. Start All Components

```bash
# Option A: Use the startup orchestration script (recommended)
python start_all.py
```

### 2. Start Services Manually

```bash
# Terminal 1: Prompt Runner
python prompt-runner01/run_server.py

# Terminal 2: Creator Core
cd creator-core/Core-Integrator-Sprint-1.1
python main.py

# Terminal 3: BHIV Core
cd ../../
python main.py

# Terminal 4: Integration Bridge
copy .env.integration_bridge.example .env.integration_bridge
# Edit .env.integration_bridge as needed
python start_integration_bridge.py

# Terminal 5: Bucket
python bhiv_bucket.py
```

### 3. Alternative Startup Options

```bash
# Start all microservices in the correct order
python start_services.py
```

### 4. Test the Pipeline

```bash
# Run the included service tests
python test_services.py

# Manual run
curl -X POST http://localhost:8004/pipeline/execute \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Design a residential building for Mumbai"}'
```

## API Endpoints

### Integration Bridge (Port 8004)

- `POST /pipeline/execute` - Execute full pipeline
- `GET /pipeline/health` - Check all component health  
- `GET /pipeline/replay/{trace_id}` - Replay from trace ID

### BHIV Bucket (Port 8005)

- `POST /bucket/store` - Store artifact
- `GET /bucket/artifact/{artifact_id}` - Get artifact by ID
- `GET /bucket/trace/{trace_id}` - Get all artifacts for trace
- `GET /bucket/stats` - Get bucket statistics

## Pipeline Flow

### Input
```json
{
  "prompt": "Design a residential building for a 1000 sqft plot in Mumbai"
}
```

### Output
```json
{
  "status": "success",
  "trace_id": "trace_abc123def456",
  "artifact_chain": {
    "A1_instruction": "instruction_12345678",
    "A2_blueprint": "blueprint_87654321", 
    "A3_execution": "execution_11223344",
    "A4_result": "result_55667788"
  },
  "pipeline_result": {
    "original_prompt": "Design a residential building...",
    "pipeline_status": "completed",
    "deterministic_hash": "a1b2c3d4e5f67890"
  }
}
```

## Artifact Chain (A1 → A4)

| Artifact | Type | Description |
|----------|------|-------------|
| **A1** | Instruction | Structured instruction from Prompt Runner |
| **A2** | Blueprint | Blueprint envelope from Creator Core |
| **A3** | Execution | Execution result from BHIV Core |
| **A4** | Result | Final assembled result |

## Features

### ✅ Deterministic Processing
- Same input always produces same deterministic hash
- Consistent results across multiple runs
- Hash-based validation for replay

### ✅ Artifact Traceability  
- Complete A1→A4 chain with trace_id
- Immutable artifact storage in bucket
- Full pipeline reconstruction capability

### ✅ Replay & Reconstruction
- Replay pipeline from any trace_id
- Reconstruct results from stored artifacts
- Determinism validation across replays

### ✅ Health Monitoring
- Component status checking
- Pipeline health endpoints
- Graceful degradation handling

### ✅ TTG/TTV Integration
- Plug-and-play module design
- Standard input/output interfaces
- No internal leakage between products

## Validation

The system includes comprehensive validation:

```bash
python validate_full_integration.py
```

**Validation Tests:**
1. ✅ Component Health Check
2. ✅ End-to-End Flow Proof  
3. ✅ Artifact Chain Validation (A1→A4)
4. ✅ Replay & Reconstruction Proof
5. ✅ Determinism Validation
6. ✅ TTG/TTV Integration Proof

## Configuration

Configuration is managed through `bhiv_config.py`:

```python
from bhiv_config import BHIVConfig

# Get component URLs
urls = BHIVConfig.get_component_urls()

# Validate configuration
validation = BHIVConfig.validate_config()
```

Environment variables can be set in `.env` file:

```bash
# Component URLs
PROMPT_RUNNER_URL=http://127.0.0.1:8003
CREATOR_CORE_URL=http://127.0.0.1:8000
BHIV_CORE_URL=http://127.0.0.1:8001

# Timeouts
REQUEST_TIMEOUT=30
PIPELINE_TIMEOUT=60
```

## Error Handling

The system handles various failure scenarios:

- **Component Unavailability**: Graceful degradation with clear error messages
- **Invalid Input**: Prompt and schema validation at entry points
- **Pipeline Interruption**: Partial artifact preservation and error tracking
- **Storage Failures**: Bucket write failure handling and backup mechanisms

## Monitoring

### Health Check
```bash
curl http://localhost:8004/pipeline/health
```

### Bucket Statistics
```bash
curl http://localhost:8005/bucket/stats
```

### Component Status
Each component provides its own health endpoint for detailed monitoring.

## Production Deployment

### Requirements
- Python 3.8+
- All component dependencies installed
- Network connectivity between components
- Sufficient storage for artifact bucket

### Scaling Considerations
- Components can be deployed on separate servers
- Update URLs in configuration for distributed deployment
- Consider load balancing for high-traffic scenarios
- Monitor bucket storage growth

## Render Deployment

This repo includes a `render.yaml` manifest for Render deployment.
The `render.yaml` defines a set of web services, including `prompt-runner` and `creator-core`.

### Recommended first step
Deploy `prompt-runner` and `creator-core` first, then add the remaining services.

### Required environment variables for prompt-runner
- `GROQ_API_KEY`
- `CREATOR_CORE_URL` should point to the Creator Core service URL, for example:
  `https://creator-core.onrender.com/creator-core/generate-blueprint`

### Required environment variables for creator-core
- `BHIV_CORE_URL` (when BHIV forwarding is enabled)
- `BUCKET_URL` (if you later enable full pipeline artifact storage)

### Verify the flow
1. `prompt-runner` health: `GET /health`
2. `creator-core` endpoint: `POST /creator-core/generate-blueprint`
3. `prompt-runner` flow: `POST /run` or `POST /generate`

If these work, the core + prompt-runner flow is operational.

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check if ports are in use
   netstat -an | findstr "8003 8000 8001 8004 8005"
   ```

2. **Component Not Starting**
   ```bash
   # Check component logs
   # Verify dependencies are installed
   # Ensure correct working directory
   ```

3. **Pipeline Failures**
   ```bash
   # Check component health
   curl http://localhost:8004/pipeline/health
   
   # Review error messages in response
   # Check individual component endpoints
   ```

## Development

### Adding New Components
1. Update `bhiv_config.py` with new component URL/port
2. Modify `integration_bridge_v2.py` to include new component in flow
3. Update health checks and validation
4. Test integration with `validate_full_integration.py`

### Extending Pipeline
1. Add new artifact types to `ArtifactGraph`
2. Update bucket storage schema
3. Modify pipeline flow in `BHIVIntegrationBridge`
4. Add validation tests

## Files Structure

```
Core-Integrator-Sprint-1.1-/
├── integration_bridge_v2.py       # Main pipeline orchestrator
├── bhiv_bucket.py                 # Artifact storage system
├── validate_full_integration.py   # Comprehensive validation
├── test_integration.py            # Quick integration test
├── start_bhiv_pipeline.py         # Component startup script
├── start_integration_bridge.py    # Bridge startup helper
├── bhiv_config.py                 # Configuration management
├── review_packets/
│   └── full_integration_v1.md     # Review packet (MANDATORY)
├── creator-core/                  # Creator Core component
└── README.md                      # This file
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review component logs
3. Run validation tests
4. Check the review packet for detailed documentation

## License

This integration is part of the BHIV infrastructure system.

---

**🎯 Integration Status**: COMPLETED ✅  
**🚀 Production Ready**: YES ✅  
**🔗 Pipeline Operational**: YES ✅  
**📊 All Tests Passing**: YES ✅