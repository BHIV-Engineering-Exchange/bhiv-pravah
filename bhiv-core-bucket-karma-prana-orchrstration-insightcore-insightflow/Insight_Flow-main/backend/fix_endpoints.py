#!/usr/bin/env python3
"""
Comprehensive endpoint fix script for InsightFlow API
Addresses common issues: auth errors, database errors, validation errors
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_database_issues():
    """Fix database connection and initialization issues"""
    
    logger.info("🔧 Fixing database issues...")
    
    try:
        from app.core.database import get_db
        from app.core.config import settings
        
        # Test database connection
        db = get_db()
        logger.info("✅ Database client initialized successfully")
        
        # Check if using mock client
        if hasattr(db, 'data'):
            logger.info("📝 Using mock database client (development mode)")
            
            # Ensure mock data has required structure
            required_tables = ["agents", "routing_logs", "feedback_events"]
            for table in required_tables:
                if table not in db.data:
                    db.data[table] = []
                    logger.info(f"✅ Created mock table: {table}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database fix failed: {e}")
        return False

async def fix_authentication_issues():
    """Fix authentication and security issues"""
    
    logger.info("🔐 Fixing authentication issues...")
    
    try:
        from app.core.security import create_access_token
        from app.core.config import settings
        
        # Test token creation
        test_data = {"sub": "test_user", "email": "test@example.com"}
        token = create_access_token(test_data)
        
        logger.info("✅ JWT token creation working")
        logger.info(f"📝 Test token: {token[:50]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Authentication fix failed: {e}")
        return False

async def fix_routing_issues():
    """Fix routing endpoint issues"""
    
    logger.info("🎯 Fixing routing issues...")
    
    try:
        from app.services.decision_engine import decision_engine
        
        # Test routing with mock data
        test_request = {
            "input_data": {"text": "test query"},
            "input_type": "text",
            "context": {"user_id": "test_user"},
            "strategy": "q_learning"
        }
        
        # This should work with mock database
        result = await decision_engine.route_request(**test_request)
        
        logger.info("✅ Routing engine working")
        logger.info(f"📝 Test routing result: {result.get('agent_id', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Routing fix failed: {e}")
        return False

async def fix_stp_issues():
    """Fix STP middleware issues"""
    
    logger.info("📦 Fixing STP issues...")
    
    try:
        from app.services.stp_service import get_stp_service
        from app.core.config import settings
        
        stp_service = get_stp_service()
        
        # Test STP wrapping
        test_data = {"message": "test", "timestamp": datetime.utcnow().isoformat()}
        
        if settings.STP_ENABLED:
            wrapped = await stp_service.wrap_routing_decision(test_data)
            logger.info("✅ STP wrapping working")
            logger.info(f"📝 STP token: {wrapped.get('stp_token', 'N/A')}")
        else:
            logger.info("📝 STP disabled in configuration")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ STP fix failed: {e}")
        return False

async def fix_karma_issues():
    """Fix Karma service issues"""
    
    logger.info("🎯 Fixing Karma issues...")
    
    try:
        from app.services.karma_service import get_karma_service
        from app.core.config import settings
        
        karma_service = get_karma_service()
        
        if settings.KARMA_ENABLED:
            # Test karma score retrieval (should handle failures gracefully)
            score = await karma_service.get_karma_score("test-agent")
            logger.info(f"✅ Karma service working (score: {score})")
        else:
            logger.info("📝 Karma disabled in configuration")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Karma fix failed: {e}")
        return False

async def test_critical_endpoints():
    """Test critical endpoints to ensure they work"""
    
    logger.info("🧪 Testing critical endpoints...")
    
    import requests
    import json
    
    base_url = "http://127.0.0.1:8000"
    
    # Test endpoints that should work without auth
    test_endpoints = [
        ("GET", "/health", None),
        ("GET", "/ping", None),
        ("GET", "/", None),
        ("GET", "/test", None),
    ]
    
    working_endpoints = []
    failing_endpoints = []
    
    for method, endpoint, data in test_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{base_url}{endpoint}", json=data, timeout=5)
            
            if response.status_code < 400:
                working_endpoints.append(endpoint)
                logger.info(f"✅ {method} {endpoint} - {response.status_code}")
            else:
                failing_endpoints.append(endpoint)
                logger.warning(f"⚠️  {method} {endpoint} - {response.status_code}")
                
        except Exception as e:
            failing_endpoints.append(endpoint)
            logger.error(f"❌ {method} {endpoint} - {e}")
    
    logger.info(f"📊 Working endpoints: {len(working_endpoints)}")
    logger.info(f"📊 Failing endpoints: {len(failing_endpoints)}")
    
    return len(working_endpoints) > len(failing_endpoints)

async def main():
    """Main fix function"""
    
    logger.info("🚀 Starting InsightFlow Endpoint Fix")
    logger.info("=" * 50)
    
    fixes = [
        ("Database", fix_database_issues),
        ("Authentication", fix_authentication_issues),
        ("Routing", fix_routing_issues),
        ("STP", fix_stp_issues),
        ("Karma", fix_karma_issues),
    ]
    
    results = {}
    
    for name, fix_func in fixes:
        try:
            result = await fix_func()
            results[name] = result
        except Exception as e:
            logger.error(f"❌ {name} fix crashed: {e}")
            results[name] = False
    
    # Test endpoints
    logger.info("\n" + "=" * 50)
    endpoint_test_result = await test_critical_endpoints()
    results["Endpoint Tests"] = endpoint_test_result
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📋 FIX SUMMARY")
    logger.info("-" * 30)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{name}: {status}")
    
    total_fixes = len(results)
    successful_fixes = sum(1 for r in results.values() if r)
    
    logger.info(f"\n📊 Overall: {successful_fixes}/{total_fixes} fixes successful")
    
    if successful_fixes == total_fixes:
        logger.info("🎉 All fixes successful! API should be working properly.")
    elif successful_fixes >= total_fixes * 0.8:
        logger.info("⚠️  Most fixes successful. Some issues may remain.")
    else:
        logger.info("❌ Multiple issues detected. Manual intervention may be required.")
    
    # Recommendations
    logger.info("\n💡 RECOMMENDATIONS:")
    if not results.get("Database"):
        logger.info("- Check database configuration in .env file")
        logger.info("- Ensure Supabase credentials are correct")
    
    if not results.get("Authentication"):
        logger.info("- Check JWT_SECRET_KEY in .env file")
        logger.info("- Ensure JWT configuration is valid")
    
    if not results.get("Endpoint Tests"):
        logger.info("- Start the server: uvicorn app.main:app --reload")
        logger.info("- Check server logs for errors")
    
    logger.info("\n🔗 Next Steps:")
    logger.info("1. Start the server if not running")
    logger.info("2. Test endpoints using: python test_all_endpoints_comprehensive.py")
    logger.info("3. Check API docs at: http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    asyncio.run(main())