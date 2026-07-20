#!/usr/bin/env python3
"""
🚀 BHIV HR Platform - Comprehensive Test Runner
Quick execution script for comprehensive endpoint testing
"""

import asyncio
import sys
import os
from pathlib import Path

# Add tests directory to path
tests_dir = Path(__file__).parent / "tests"
sys.path.insert(0, str(tests_dir))

try:
    from comprehensive_endpoint_test_updated import BHIVEndpointTester
    print("✅ Using enhanced test module with URL discovery and API key validation")
except ImportError as e:
    print(f"⚠️ Enhanced test module not found: {e}")
    print("📋 Falling back to original test module...")
    try:
        from comprehensive_endpoint_test import BHIVEndpointTester
        print("✅ Using original test module")
    except ImportError as e2:
        print(f"❌ Error importing test modules: {e2}")
        print("📋 Please ensure you're in the BHIV HR PLATFORM directory")
        print("📋 Install requirements: pip install -r tests/requirements.txt")
        sys.exit(1)

async def run_tests():
    """Run enhanced comprehensive endpoint tests"""
    print("🚀 BHIV HR Platform - Enhanced Comprehensive Endpoint Testing")
    print("=" * 70)
    print("✨ Enhanced Features:")
    print("   • LangGraph URL discovery")
    print("   • Production API key validation")
    print("   • Enhanced authentication tokens")
    print("   • Comprehensive error handling")
    print("📊 Testing 89 endpoints across 6 services")
    print("🐳 Environment: Docker (Local Development)")
    print("⏱️ Estimated time: 2-3 minutes")
    print("=" * 70)
    
    # Check if API key is set
    api_key = os.getenv("API_KEY_SECRET")
    if not api_key:
        print("⚠️ Warning: API_KEY_SECRET not set in environment")
        print("🔍 The test will attempt to discover a working API key")
        print("💡 For best results, set API_KEY_SECRET environment variable")
        print()
    else:
        print(f"✅ API Key configured: {api_key[:10]}...")
        print()
    
    # Check for custom service URLs
    custom_urls = {}
    for service in ['GATEWAY_SERVICE_URL', 'AGENT_SERVICE_URL', 'LANGGRAPH_SERVICE_URL', 'PORTAL_SERVICE_URL', 'CLIENT_PORTAL_SERVICE_URL', 'CANDIDATE_PORTAL_SERVICE_URL']:
        url = os.getenv(service)
        if url:
            custom_urls[service] = url
    
    if custom_urls:
        print("🔧 Custom service URLs detected:")
        for service, url in custom_urls.items():
            print(f"   {service}: {url}")
        print()
    
    try:
        tester = BHIVEndpointTester()
        await tester.run_comprehensive_test()
        
        print("\n🎉 Enhanced comprehensive testing completed successfully!")
        print("📊 Check ENHANCED_COMPREHENSIVE_TEST_REPORT.md for detailed results")
        print("\n🎯 Key Improvements:")
        print("   • Docker service discovery")
        print("   • Local API key validation")
        print("   • Enhanced authentication handling")
        print("   • Improved error reporting")
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Critical error during testing: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure Docker services are running")
        print("   2. Check docker-compose up -d status")
        print("   3. Verify localhost ports are accessible")
        print("   4. Check Docker container logs")
        sys.exit(1)

if __name__ == "__main__":
    # Set UTF-8 encoding for Windows (if needed)
    if sys.platform == 'win32':
        try:
            import codecs
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except:
            pass  # Skip encoding setup if it fails
    
    # Don't set default API key - let the enhanced test discover it
    asyncio.run(run_tests())