### BHIV Core - Third Installment

An advanced multi-modal AI pipeline with reinforcement learning, knowledge-base retrieval (multi-folder vector search + NAS + FAISS + file retriever), a production-ready FastAPI layer, web interface, and an enhanced CLI.

> **Note:** If you see a '0 vector stores' message during startup, this is normal when no FAISS indices are present. The system will automatically fall back to other retrieval methods in the multi-folder vector search pipeline.

### Key Features
- Multi-modal processing: text, PDF, image, audio
- Knowledge-aware responses: Multi-folder vector search across all Qdrant instances with NAS/FAISS/File-based fallback
- Reinforcement learning: adaptive agent/model selection with logging and analytics
- Web UI: authenticated uploads, dashboard, and downloads
- CLI: single/batch processing with JSON/Text/CSV output
- Health, metrics, MongoDB logging, and retry/error handling

### What's New
- **Multi-Folder Vector Search**: Search across all Qdrant data folders simultaneously
- **Intelligent Result Ranking**: Results prioritized by relevance and folder recency
- **Comprehensive Knowledge Retrieval**: Access all your knowledge with a single query
- **Smart Fallback Mechanisms**: Automatic fallback to alternative retrieval methods
- **Health Monitoring**: Improved diagnostics and status reporting

### Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   CLI Runner    │    │  Simple API     │
│   (Port 8003)   │    │  (Enhanced)     │    │  (Port 8001)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └──────────────┬────────┴──────────────┬────────┘
                        │                       │
                   ┌───────────────┐       ┌───────────────┐
                   │  MCP Bridge   │       │  Knowledge KB │
                   │  (Port 8002)  │       │  (Multi-Folder)│
                   └───────────────┘       └───────────────┘
                              │
                 ┌────────────┴────────────┐
                 │  Agent Registry + RL    │
                 │  (text/pdf/image/audio) │
                 └──────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Optional: MongoDB 5.0+ for logging/analytics
- Optional: Docker for vector DBs/services

### Install
```bash
git clone <repository-url>
cd BHIV-Third-Installment
python -m venv .venv && .python -m venv .venv  # Windows PowerShell
pip install -r requirements.txt
# Optional NLP model
python -m spacy download en_core_web_sm
```

### Environment
Create a `.env` file (values optional depending on your setup):
```env
MONGO_URI=mongodb://localhost:27017
USE_RL=true
RL_EXPLORATION_RATE=0.2
GROQ_API_KEY=your_key_if_used
GEMINI_API_KEY=your_key_if_used

# Single Qdrant instance (used as fallback)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=vedas_knowledge_base
QDRANT_VECTOR_SIZE=384

# Multi-Folder Vector Configuration (primary retrieval method)
QDRANT_URLS=http://localhost:6333  # Comma-separated URLs if using multiple servers
QDRANT_INSTANCE_NAMES=qdrant_data,qdrant_fourth_data,qdrant_legacy_data,qdrant_new_data
```

> **Important**: The multi-folder vector configuration is essential for enabling comprehensive search across all your Qdrant data folders. Make sure both `QDRANT_URLS` and `QDRANT_INSTANCE_NAMES` are properly configured.

### Run Services (recommended ports)
```powershell
# Terminal 1: Simple API (agents, KB endpoints)
python simple_api.py --port 8001

# Terminal 2: MCP Bridge (task router, RL, registry)
python mcp_bridge.py  # serves on port 8002

# Terminal 3: Web Interface (auth: admin/secret, user/secret)
python integration/web_interface.py  # serves on port 8003
```

### Endpoints
- Web UI: `http://localhost:8003`
- MCP Bridge health: `http://localhost:8002/health`
- Simple API docs: `http://localhost:8001/docs`

## Usage

### CLI
```bash
# Text
python cli_runner.py summarize "Explain artificial intelligence" edumentor_agent --input-type text

# Single file (auto-detect type)
python cli_runner.py summarize "Analyze this file" edumentor_agent --file sample_documents/ayurveda_basics.txt

# Batch directory → save CSV
python cli_runner.py summarize "Process folder" edumentor_agent --batch ./sample_documents --output results.csv --output-format csv

# RL options
python cli_runner.py summarize "Learning test" edumentor_agent --use-rl --rl-stats --exploration-rate 0.3
```

### MCP Bridge API (port 8002)
```bash
# JSON task
curl -X POST http://localhost:8002/handle_task \
  -H "Content-Type: application/json" \
  -d '{"agent":"edumentor_agent","input":"Explain machine learning","input_type":"text"}'

# Multi-task
curl -X POST http://localhost:8002/handle_multi_task \
  -H "Content-Type: application/json" \
  -d '{"files":[{"path":"test.pdf","type":"pdf","data":"Analyze"}],"agent":"edumentor_agent","task_type":"summarize"}'
```

### Simple API (port 8001)
```bash
# Vedas
curl -X POST http://localhost:8001/ask-vedas -H "Content-Type: application/json" -d '{"query":"what is dharma"}'

# Educational
curl -X POST http://localhost:8001/edumentor -H "Content-Type: application/json" -d '{"query":"explain reinforcement learning"}'

# Wellness
curl -X POST http://localhost:8001/wellness -H "Content-Type: application/json" -d '{"query":"how to reduce stress"}'

# Knowledge Base (uses NAS → FAISS → file retriever fallback)
curl -X POST http://localhost:8001/query-kb -H "Content-Type: application/json" -d '{"query":"agent architecture"}'

# Health
curl http://localhost:8001/health
```

### Web Interface (port 8003)
- Login with Basic Auth (`admin/secret` or `user/secret`)
- Upload files at `/` → processed via MCP Bridge
- Dashboard at `/dashboard` → recent tasks, NLO stats
- Download NLOs: `/download_nlo/{task_id}?format=json`

### Demo Pipeline
```bash
python blackhole_demo.py  # edit defaults within to point to your input
```

## Configuration
- Agent endpoints and options: `config/settings.py` and `agent_configs.json`
- RL configuration: `config/settings.py` (`RL_CONFIG`)
- Timeouts: `config/settings.py` (`TIMEOUT_CONFIG`)
- Knowledge base utilities: `bhiv_knowledge_base.py`, `utils/file_based_retriever.py`
- Multi-folder vector search: `multi_folder_vector_manager.py`

## Multi-Folder Vector Search
The system now supports searching across multiple Qdrant folders simultaneously:

```
📁 Folder Structure:
  📂 qdrant_data
  📂 qdrant_fourth_data
  📂 qdrant_legacy_data
  📂 qdrant_new_data
```

### How It Works
1. System scans ALL folders for Qdrant collections
2. When you search, it queries EVERY collection in EVERY folder
3. Results are combined and ranked by relevance + folder priority
4. You get the BEST matches from your ENTIRE knowledge base

### Folder Priority Weights
- qdrant_new_data: 1.0 (highest priority)
- qdrant_fourth_data: 0.9
- qdrant_data: 0.8
- qdrant_legacy_data: 0.7

### Fallback Strategy
1. Multi-folder vector search
2. NAS+Qdrant retriever
3. Individual Qdrant retriever
4. FAISS vector stores
5. File-based retriever

### Understanding Startup Messages
When you see:
```
Initialized with 0 vector stores + multi-folder manager
```
This is normal and indicates:
- The system has successfully initialized the multi-folder vector manager
- No FAISS vector stores were loaded (they're only used as fallback)
- The system will use the multi-folder vector search as the primary retrieval method

The multi-folder vector manager will automatically discover and search across all available Qdrant collections in the configured folders.

Notes
- Start Simple API on port 8001 to match `agent_configs.json` and `MODEL_CONFIG` endpoints.
- For audio/image/PDF processing, ensure system deps like `ffmpeg`/`libsndfile` are available.

## Testing
```bash
pytest -q
# Or run focused suites
pytest tests/test_web_interface_integration.py -q
```

## Troubleshooting
- Check health:
  - `http://localhost:8002/health` (MCP Bridge)
  - `http://localhost:8001/health` (Simple API)
- Ports in use on Windows:
  - `netstat -ano | findstr :8001`
  - `netstat -ano | findstr :8002`
  - `netstat -ano | findstr :8003`
- Multi-folder vector search issues:
  - Verify `.env` has both `QDRANT_URLS` and `QDRANT_INSTANCE_NAMES` configured
  - Run `python test_multi_folder_search.py` to test the multi-folder functionality
  - Check startup logs for "[SUCCESS] Multi-folder vector manager initialized successfully"
  - The "0 vector stores" message is normal - it refers to FAISS indices, not Qdrant collections
- Increase timeouts via environment or `config/settings.py` if large files stall.
- If multi-folder vector search fails, the system falls back to NAS+Qdrant retriever, then to individual Qdrant retriever, then to FAISS (if indices present under `vector_stores/`), and finally to file-based retriever over `local_setup/storage/documents/`.
- To test multi-folder vector search: `python test_multi_folder_search.py`
- To see a demo of the multi-folder system: `python demo_multi_folder.py`

## What's New in Third Installment
- Multi-folder vector search system for comprehensive knowledge retrieval across all Qdrant instances
- Unified Simple API with knowledge-base endpoints and model providers
- Reinforcement Learning context/logging integration in MCP Bridge
- Enhanced CLI with batch processing and multiple output formats
- Web UI with authentication, uploads, and NLO download

—

For advanced usage and deployment, see:
- `docs/complete_usage_guide.md`
- `docs/deployment.md`
- `example/quick_setup_guide.md`
