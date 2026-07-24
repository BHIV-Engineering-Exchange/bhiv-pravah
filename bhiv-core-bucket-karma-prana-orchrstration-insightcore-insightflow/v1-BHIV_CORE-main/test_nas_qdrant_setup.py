#!/usr/bin/env python3
"""
Test script to verify NAS and Qdrant setup for BHIV Knowledge Base
"""

import os
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_nas_connection():
    """Test NAS connection and folder access."""
    print("🔍 Testing NAS Connection...")
    
    nas_drive = os.getenv("NAS_DRIVE", "G:")
    
    try:
        # Check if drive is mapped
        result = subprocess.run(["net", "use"], capture_output=True, text=True)
        if nas_drive in result.stdout and "192.168.0.94" in result.stdout:
            print(f"✅ NAS is connected at {nas_drive}")
            
            # Test folder access
            drive_path = Path(nas_drive)
            if drive_path.exists():
                print(f"✅ Can access {nas_drive}")
                
                # Check required folders
                required_folders = [
                    "qdrant_embeddings",
                    "source_documents", 
                    "metadata",
                    "qdrant_data"
                ]
                
                for folder in required_folders:
                    folder_path = drive_path / folder
                    if folder_path.exists():
                        print(f"✅ Folder exists: {folder}")
                    else:
                        print(f"❌ Missing folder: {folder}")
                        try:
                            folder_path.mkdir(exist_ok=True)
                            print(f"✅ Created folder: {folder}")
                        except Exception as e:
                            print(f"❌ Failed to create {folder}: {e}")
                
                return True
            else:
                print(f"❌ Cannot access {nas_drive}")
                return False
        else:
            print(f"❌ NAS is not connected to {nas_drive}")
            return False
            
    except Exception as e:
        print(f"❌ NAS test failed: {e}")
        return False

def test_qdrant_connection():
    """Test Qdrant connection and status."""
    print("\n🔍 Testing Qdrant Connection...")
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{qdrant_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Qdrant is accessible")
            
            # Test collections endpoint
            collections_response = requests.get(f"{qdrant_url}/collections", timeout=5)
            if collections_response.status_code == 200:
                collections = collections_response.json()
                print(f"✅ Collections endpoint working")
                
                collection_name = os.getenv("QDRANT_COLLECTION", "vedas_knowledge_base")
                if collections.get("result", {}).get("collections"):
                    collection_names = [c["name"] for c in collections["result"]["collections"]]
                    if collection_name in collection_names:
                        print(f"✅ Collection '{collection_name}' exists")
                    else:
                        print(f"⚠️ Collection '{collection_name}' not found")
                        print(f"Available collections: {collection_names}")
                else:
                    print("⚠️ No collections found")
                
                return True
            else:
                print(f"❌ Collections endpoint failed: {collections_response.status_code}")
                return False
        else:
            print(f"❌ Qdrant not accessible: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Qdrant - is it running?")
        print("Try: python setup_qdrant.py --start")
        return False
    except Exception as e:
        print(f"❌ Qdrant test failed: {e}")
        return False

def test_docker_status():
    """Test Docker status."""
    print("\n🔍 Testing Docker Status...")
    
    try:
        # Check Docker version
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Docker available: {result.stdout.strip()}")
            
            # Check running containers
            ps_result = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=10)
            if ps_result.returncode == 0:
                if "qdrant" in ps_result.stdout.lower():
                    print("✅ Qdrant container is running")
                else:
                    print("⚠️ Qdrant container not found in running containers")
                return True
            else:
                print("❌ Cannot list Docker containers")
                return False
        else:
            print("❌ Docker not available")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Docker command timed out - Docker may not be running")
        return False
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        return False

def test_knowledge_agent():
    """Test KnowledgeAgent functionality."""
    print("\n🔍 Testing Knowledge Agent...")
    
    try:
        from agents.KnowledgeAgent import KnowledgeAgent
        
        agent = KnowledgeAgent()
        print("✅ KnowledgeAgent imported successfully")
        
        # Test a simple query
        test_query = "What is dharma?"
        print(f"Testing query: '{test_query}'")
        
        result = agent.query(test_query)
        if result and len(result) > 0:
            print("✅ Knowledge Agent query successful")
            print(f"Response preview: {result[:200]}...")
            return True
        else:
            print("⚠️ Knowledge Agent returned empty result")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import KnowledgeAgent: {e}")
        return False
    except Exception as e:
        print(f"❌ Knowledge Agent test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 BHIV Knowledge Base - System Test")
    print("=" * 50)
    
    tests = [
        ("Docker Status", test_docker_status),
        ("NAS Connection", test_nas_connection),
        ("Qdrant Connection", test_qdrant_connection),
        ("Knowledge Agent", test_knowledge_agent)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST SUMMARY")
    print(f"{'='*50}")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed! Your knowledge base is ready to use.")
        print("\nTry: python cli_runner.py explain 'what is dharma' knowledge_agent")
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")
        
        if not results.get("Docker Status", False):
            print("- Make sure Docker Desktop is running")
        if not results.get("NAS Connection", False):
            print("- Update NAS credentials in .env file")
            print("- Run: python connect_nas_simple.py")
        if not results.get("Qdrant Connection", False):
            print("- Run: python setup_qdrant.py --start")
        if not results.get("Knowledge Agent", False):
            print("- Run: python load_data_to_qdrant.py --init")

if __name__ == "__main__":
    main()
