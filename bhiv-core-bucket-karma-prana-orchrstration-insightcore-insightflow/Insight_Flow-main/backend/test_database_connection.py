#!/usr/bin/env python3
"""
Test database connection and integration
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_database_connection():
    """Test database connection and basic operations"""
    
    print("🔍 Testing Database Connection...")
    print("=" * 50)
    
    try:
        from app.core.config import settings
        from app.core.database import get_db
        
        print(f"📋 Configuration:")
        print(f"   USE_SOVEREIGN_CORE: {settings.USE_SOVEREIGN_CORE}")
        print(f"   SUPABASE_URL: {settings.SUPABASE_URL[:50]}..." if settings.SUPABASE_URL else "   SUPABASE_URL: Not set")
        print(f"   Environment: {settings.ENVIRONMENT}")
        
        # Get database client
        db = get_db()
        print(f"\n✅ Database client initialized: {type(db).__name__}")
        
        # Test basic operations
        if hasattr(db, 'data'):
            print("📝 Using Mock Database (Development Mode)")
            
            # Test mock operations
            agents = db.table("agents").select("*").execute()
            print(f"✅ Mock agents table: {len(agents.data)} records")
            
            # Test insert
            test_log = {
                "id": "test-123",
                "request_id": "req-123", 
                "input_type": "text",
                "input_data": {"text": "test"},
                "status": "pending"
            }
            
            result = db.table("routing_logs").insert(test_log)
            print("✅ Mock insert operation successful")
            
        else:
            print("🔗 Using Real Database (Supabase)")
            
            # Test Supabase connection
            try:
                agents = db.table("agents").select("*").limit(1).execute()
                print(f"✅ Supabase connection successful: {len(agents.data)} agents found")
                
                # Test table structure
                tables_to_check = ["agents", "routing_logs", "feedback_events"]
                for table in tables_to_check:
                    try:
                        result = db.table(table).select("*", count="exact").limit(1).execute()
                        print(f"✅ Table '{table}': {result.count} records")
                    except Exception as e:
                        print(f"❌ Table '{table}': {str(e)}")
                        
            except Exception as e:
                print(f"❌ Supabase connection failed: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_endpoint_database_integration():
    """Test if endpoints can use database"""
    
    print("\n🎯 Testing Endpoint Database Integration...")
    print("-" * 50)
    
    try:
        from app.services.decision_engine import decision_engine
        
        # Test routing (should use database)
        result = await decision_engine.route_request(
            input_data={"text": "test query"},
            input_type="text",
            context={"user_id": "test_user"},
            strategy="q_learning"
        )
        
        print("✅ Routing engine database integration working")
        print(f"   Agent selected: {result.get('agent_id')}")
        print(f"   Routing log ID: {result.get('routing_log_id')}")
        
        # Test feedback processing
        try:
            await decision_engine.process_feedback(
                routing_log_id=result.get('routing_log_id'),
                feedback_data={
                    "success": True,
                    "latency_ms": 100.0,
                    "accuracy_score": 0.9
                }
            )
            print("✅ Feedback processing database integration working")
        except Exception as e:
            print(f"⚠️  Feedback processing: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Endpoint database integration failed: {e}")
        return False

async def main():
    """Main test function"""
    
    print("🚀 Database Connection & Integration Test")
    print("=" * 60)
    
    # Test 1: Database Connection
    db_test = await test_database_connection()
    
    # Test 2: Endpoint Integration  
    endpoint_test = await test_endpoint_database_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"   Database Connection: {'✅ PASS' if db_test else '❌ FAIL'}")
    print(f"   Endpoint Integration: {'✅ PASS' if endpoint_test else '❌ FAIL'}")
    
    if db_test and endpoint_test:
        print("\n🎉 Database is properly connected and integrated!")
    elif db_test:
        print("\n⚠️  Database connected but endpoint integration has issues")
    else:
        print("\n❌ Database connection issues detected")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if not db_test:
        print("   - Check .env configuration")
        print("   - Verify Supabase credentials")
        print("   - Ensure tables exist in database")
    
    if not endpoint_test:
        print("   - Check service dependencies")
        print("   - Verify database schema matches code")
    
    print("\n🔧 QUICK FIXES:")
    print("   1. Use Supabase: Set USE_SOVEREIGN_CORE=false")
    print("   2. Use Mock DB: Keep USE_SOVEREIGN_CORE=true (development)")
    print("   3. Check Supabase dashboard for table structure")

if __name__ == "__main__":
    asyncio.run(main())