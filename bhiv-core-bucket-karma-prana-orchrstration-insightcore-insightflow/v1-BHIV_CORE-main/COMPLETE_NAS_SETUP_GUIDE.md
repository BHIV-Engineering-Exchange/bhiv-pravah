# BHIV Knowledge Base - Complete NAS Setup Guide

## Overview
This guide will help you connect your BHIV Knowledge Base to your company's NAS server at `192.168.0.94` with the `Guruukul_DB` share.

## Prerequisites

### 1. Information Required from Your Manager
Please get the following information from your manager:

#### Authentication Details
- **Username**: NAS login username
- **Password**: NAS login password  
- **Domain**: Usually "WORKGROUP" or your company domain

#### Network Access
- **Port**: Usually 445 for SMB (confirm if different)
- **Protocol**: SMB version (2.0, 3.0, etc.)
- **Firewall**: Ensure port 445 is open from your machine to 192.168.0.94

#### Permissions
- **Read/Write access** to Guruukul_DB share
- **Folder creation rights** in the share
- **File access** for creating embeddings and metadata

### 2. Software Requirements
- **Docker Desktop** (for Qdrant)
- **Python 3.8+** (already installed)
- **Network access** to 192.168.0.94

## Step-by-Step Setup

### Step 1: Install Docker Desktop
1. Download from: https://www.docker.com/products/docker-desktop/
2. Install and start Docker Desktop
3. Verify: `docker --version`

### Step 2: Setup Environment
```bash
# Run the environment setup
python setup_nas_environment.py
```

This creates:
- `.env.nas_template` file with configuration
- Required directories
- Test scripts

### Step 3: Configure Credentials
1. Copy `.env.nas_template` to `.env`
2. Edit `.env` file with your NAS credentials:
```env
NAS_USERNAME=your_actual_username
NAS_PASSWORD=your_actual_password
NAS_DOMAIN=WORKGROUP
```

### Step 4: Connect to NAS
```bash
# Connect to the NAS server
python connect_nas.py
```

This will:
- Test connectivity to 192.168.0.94
- Prompt for credentials
- Map the share to drive G:
- Create necessary folders
- Verify access

### Step 5: Start Qdrant
```bash
# Start Qdrant vector database
python setup_qdrant.py --start
```

This will:
- Download Qdrant Docker image
- Start Qdrant container
- Expose on localhost:6333
- Create data directory

### Step 6: Test Setup
```bash
# Test all components
python test_nas_setup.py
```

This verifies:
- NAS connectivity
- Qdrant accessibility  
- Knowledge agent functionality

### Step 7: Load Data to Qdrant
```bash
# Initialize and load your documents
python load_data_to_qdrant.py --init --load-pdfs
```

### Step 8: Test Knowledge Base
```bash
# Test with CLI runner
python cli_runner.py explain "what is dharma" knowledge_agent
```

## Folder Structure on NAS

After setup, your NAS will have:
```
G:\ (\\192.168.0.94\Guruukul_DB\)
├── qdrant_embeddings/     # Vector embeddings
├── source_documents/      # Original PDF files
├── metadata/             # Document metadata
└── qdrant_data/          # Qdrant database files
```

## Troubleshooting

### NAS Connection Issues
1. **Cannot reach 192.168.0.94**
   - Check network connection
   - Verify NAS is powered on
   - Test with: `ping 192.168.0.94`

2. **Authentication Failed**
   - Verify username/password
   - Check domain (WORKGROUP vs company domain)
   - Ensure account has access to Guruukul_DB

3. **Permission Denied**
   - Verify read/write permissions
   - Check folder creation rights
   - Contact IT admin for access

### Qdrant Issues
1. **Docker not found**
   - Install Docker Desktop
   - Start Docker service
   - Verify with: `docker ps`

2. **Port 6333 in use**
   - Stop existing Qdrant: `python setup_qdrant.py --stop`
   - Check other services using port 6333

### Knowledge Base Issues
1. **No results from queries**
   - Verify data loading: `python load_data_to_qdrant.py --status`
   - Check Qdrant collections: `python setup_qdrant.py --status`
   - Ensure PDFs are in source_documents folder

## Configuration Files

### Key Files Updated
- `example/nas_config.py` - NAS connection settings
- `config/bhiv_nas_deployment.json` - Deployment configuration
- `.env` - Environment variables
- `connect_nas.py` - NAS connection script

### Environment Variables
```env
# NAS Settings
NAS_IP=192.168.0.94
NAS_SHARE=Guruukul_DB
NAS_DRIVE=G:

# Qdrant Settings  
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=vedas_knowledge_base

# Paths
EMBEDDINGS_PATH=G:\qdrant_embeddings
DOCUMENTS_PATH=G:\source_documents
METADATA_PATH=G:\metadata
```

## Usage After Setup

### CLI Commands
```bash
# Query knowledge base
python cli_runner.py explain "your question" knowledge_agent

# Batch process documents
python cli_runner.py summarize "analyze documents" knowledge_agent --batch ./documents

# Add new documents
python load_data_to_qdrant.py --add-documents ./new_pdfs
```

### API Usage
```python
from agents.KnowledgeAgent import KnowledgeAgent

agent = KnowledgeAgent()
result = agent.query("What is dharma?")
print(result)
```

## Maintenance

### Regular Tasks
1. **Backup NAS data** - Ensure IT backs up Guruukul_DB share
2. **Update embeddings** - Re-run when adding new documents
3. **Monitor disk space** - Check NAS storage usage
4. **Update Qdrant** - Periodically update Docker image

### Monitoring
- Check NAS connectivity: `python test_nas_setup.py`
- Monitor Qdrant: `python setup_qdrant.py --status`
- View logs: Check `./logs/` directory

## Security Notes

1. **Credentials**: Store in `.env` file (not in code)
2. **Network**: Ensure secure connection to NAS
3. **Access**: Limit NAS permissions to required folders only
4. **Backup**: Regular backups of knowledge base data

## Support

If you encounter issues:
1. Check logs in `./logs/` directory
2. Run diagnostic: `python test_nas_setup.py`
3. Verify network connectivity to 192.168.0.94
4. Contact IT for NAS access issues

## Next Steps After Setup

1. **Add your documents** to `G:\source_documents\`
2. **Run data loading** with `python load_data_to_qdrant.py --load-pdfs`
3. **Test queries** with `python cli_runner.py`
4. **Integrate with your workflow** using the API or CLI

Your knowledge base will now retrieve data from the NAS server when users query through the CLI runner!
