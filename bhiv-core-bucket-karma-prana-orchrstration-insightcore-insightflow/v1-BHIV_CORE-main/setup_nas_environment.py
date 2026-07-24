#!/usr/bin/env python3
"""
Environment Setup for NAS-based Knowledge Base
Sets up environment variables and configuration for NAS access
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

def create_env_file():
    """Create .env file with NAS configuration."""
    env_content = """# BHIV Knowledge Base - NAS Configuration
# Company NAS Server Settings
NAS_USERNAME=your_username_here
NAS_PASSWORD=your_password_here
NAS_DOMAIN=WORKGROUP

# NAS Connection Details
NAS_IP=192.168.0.94
NAS_SHARE=Guruukul_DB
NAS_DRIVE=G:

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=vedas_knowledge_base
QDRANT_VECTOR_SIZE=384
QDRANT_DISTANCE_METRIC=Cosine

# Knowledge Base Paths (on NAS)
EMBEDDINGS_PATH=G:\\qdrant_embeddings
DOCUMENTS_PATH=G:\\source_documents
METADATA_PATH=G:\\metadata
QDRANT_DATA_PATH=G:\\qdrant_data

# Local Cache Settings
LOCAL_CACHE_ENABLED=true
LOCAL_CACHE_PATH=./cache/nas_cache
CACHE_EXPIRY_HOURS=24

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/nas_knowledge_base.log
"""
    
    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists. Creating .env.nas_template instead.")
        env_file = Path(".env.nas_template")
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Environment template created: {env_file}")
    print("📝 Please update the NAS_USERNAME and NAS_PASSWORD values")
    return env_file

def setup_directories():
    """Setup local directories for caching and logs."""
    directories = [
        "cache/nas_cache",
        "logs",
        "qdrant_storage",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        "qdrant-client",
        "sentence-transformers", 
        "langchain-community",
        "python-dotenv",
        "requests"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False
    else:
        print("✅ All required packages are installed")
        return True

def create_nas_test_script():
    """Create a test script for NAS connectivity."""
    test_script = """#!/usr/bin/env python3
'''
Test NAS connectivity and knowledge base access
'''

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_nas_connection():
    '''Test NAS connection and access.'''
    nas_drive = os.getenv('NAS_DRIVE', 'G:')
    
    print("🔍 Testing NAS Connection...")
    print(f"Drive: {nas_drive}")
    
    # Check if drive exists
    if os.path.exists(f"{nas_drive}\\\\"):
        print("✅ NAS drive is accessible")
        
        # Check folders
        folders = ['qdrant_embeddings', 'source_documents', 'metadata', 'qdrant_data']
        for folder in folders:
            folder_path = f"{nas_drive}\\\\{folder}"
            if os.path.exists(folder_path):
                print(f"✅ Folder exists: {folder}")
            else:
                print(f"❌ Folder missing: {folder}")
                
        return True
    else:
        print(f"❌ NAS drive not accessible: {nas_drive}")
        print("Run: python connect_nas.py")
        return False

def test_qdrant_connection():
    '''Test Qdrant connection.'''
    try:
        from qdrant_client import QdrantClient
        
        qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        client = QdrantClient(url=qdrant_url)
        
        collections = client.get_collections()
        print(f"✅ Qdrant accessible at {qdrant_url}")
        print(f"📊 Collections: {len(collections.collections)}")
        return True
        
    except Exception as e:
        print(f"❌ Qdrant not accessible: {e}")
        print("Run: python setup_qdrant.py --start")
        return False

def test_knowledge_agent():
    '''Test knowledge agent functionality.'''
    try:
        from agents.KnowledgeAgent import KnowledgeAgent
        
        agent = KnowledgeAgent()
        print("✅ KnowledgeAgent initialized successfully")
        
        # Test query
        result = agent.query("test query", task_id="test")
        print("✅ Knowledge agent query test passed")
        return True
        
    except Exception as e:
        print(f"❌ KnowledgeAgent test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 BHIV Knowledge Base - NAS Integration Test")
    print("=" * 50)
    
    tests = [
        ("NAS Connection", test_nas_connection),
        ("Qdrant Connection", test_qdrant_connection), 
        ("Knowledge Agent", test_knowledge_agent)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\\n🔬 Testing {test_name}...")
        if test_func():
            passed += 1
        print("-" * 30)
    
    print(f"\\n📊 Test Results: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Your NAS knowledge base is ready!")
    else:
        print("❌ Some tests failed. Please check the setup.")
"""
    
    with open("test_nas_setup.py", 'w') as f:
        f.write(test_script)
    
    print("✅ Created test script: test_nas_setup.py")

def main():
    """Main setup function."""
    print("🚀 BHIV Knowledge Base - NAS Environment Setup")
    print("=" * 50)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("❌ Please install missing dependencies first")
        return False
    
    # Step 2: Setup directories
    setup_directories()
    
    # Step 3: Create environment file
    env_file = create_env_file()
    
    # Step 4: Create test script
    create_nas_test_script()
    
    print("\n✅ Environment setup complete!")
    print("\n📋 Next Steps:")
    print(f"1. Edit {env_file} with your NAS credentials")
    print("2. Run: python connect_nas.py")
    print("3. Run: python setup_qdrant.py --start")
    print("4. Run: python test_nas_setup.py")
    print("5. Run: python load_data_to_qdrant.py --init")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
