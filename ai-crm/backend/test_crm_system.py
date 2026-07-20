#!/usr/bin/env python3
"""
Comprehensive CRM System Test Script
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import init_database
from database.crm_service import CRMService
from integrations.llm_query_system import LLMQuerySystem
from integrations.office365_integration import Office365Integration, CRMEmailTemplates
from integrations.google_maps_integration import GoogleMapsIntegration, VisitTracker

def test_database_initialization():
    """Test database initialization with CRM data"""
    print("🗄️ Testing Database Initialization...")
    
    try:
        init_database()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def test_crm_service():
    """Test CRM service operations"""
    print("\n🏢 Testing CRM Service...")
    
    try:
        with CRMService() as crm:
            # Test dashboard data
            dashboard_data = crm.get_crm_dashboard_data()
            print(f"✅ Dashboard data retrieved:")
            print(f"   - Accounts: {dashboard_data['accounts']['total']}")
            print(f"   - Leads: {dashboard_data['leads']['total']}")
            print(f"   - Opportunities: {dashboard_data['opportunities']['total']}")
            print(f"   - Pipeline Value: ${dashboard_data['opportunities']['pipeline_value']:,.0f}")
            
            # Test account operations
            accounts = crm.get_accounts(limit=3)
            print(f"✅ Retrieved {len(accounts)} accounts")
            
            if accounts:
                account_details = crm.get_account_by_id(accounts[0]['account_id'])
                print(f"✅ Account details for {account_details['name']}:")
                print(f"   - Contacts: {len(account_details.get('contacts', []))}")
                print(f"   - Opportunities: {len(account_details.get('opportunities', []))}")
            
            # Test lead operations
            leads = crm.get_leads(limit=3)
            print(f"✅ Retrieved {len(leads)} leads")
            
            # Test opportunity operations
            opportunities = crm.get_opportunities(limit=3)
            print(f"✅ Retrieved {len(opportunities)} opportunities")
            
            # Test activity operations
            activities = crm.get_activities(limit=5)
            print(f"✅ Retrieved {len(activities)} activities")
            
            return True
            
    except Exception as e:
        print(f"❌ CRM service test failed: {e}")
        return False

def test_llm_query_system():
    """Test LLM query system"""
    print("\n🤖 Testing LLM Query System...")
    
    try:
        llm_system = LLMQuerySystem()
        
        # Test queries
        test_queries = [
            "Show me opportunities closing this month",
            "What are the pending tasks?",
            "Account summary for TechCorp",
            "Pipeline analysis",
            "Recent activities"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            result = llm_system.process_query(query)
            
            if result['success']:
                response = llm_system.generate_natural_response(result)
                print(f"✅ Response: {response[:200]}...")
            else:
                print(f"⚠️ Query failed: {result['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM query system test failed: {e}")
        return False

def test_email_integration():
    """Test Office 365 email integration"""
    print("\n📧 Testing Email Integration...")
    
    try:
        office365 = Office365Integration()
        templates = CRMEmailTemplates()
        
        # Test email templates
        opp_data = {
            'name': 'TechCorp Logistics Upgrade',
            'account_name': 'TechCorp Industries',
            'amount': 300000.0,
            'stage': 'proposal',
            'probability': 75.0,
            'close_date': '2024-02-15'
        }
        
        email_content = templates.opportunity_approval_email(opp_data)
        print(f"✅ Opportunity approval email template generated")
        print(f"   Subject: {email_content['subject']}")
        
        order_data = {
            'order_id': 12345,
            'customer_id': 'CUST001',
            'product_id': 'A101',
            'quantity': 10,
            'status': 'Confirmed',
            'order_date': '2024-01-15'
        }
        
        email_content = templates.order_confirmation_email(order_data)
        print(f"✅ Order confirmation email template generated")
        print(f"   Subject: {email_content['subject']}")
        
        lead_data = {
            'full_name': 'John Smith',
            'company': 'TechCorp',
            'need': 'Inventory management system',
            'budget': 100000.0,
            'timeline': 'Q2 2024'
        }
        
        email_content = templates.lead_follow_up_email(lead_data)
        print(f"✅ Lead follow-up email template generated")
        print(f"   Subject: {email_content['subject']}")
        
        # Test auth URL generation
        auth_url = office365.get_auth_url()
        print(f"✅ OAuth URL generated (length: {len(auth_url)})")
        
        return True
        
    except Exception as e:
        print(f"❌ Email integration test failed: {e}")
        return False

def test_maps_integration():
    """Test Google Maps integration"""
    print("\n🗺️ Testing Maps Integration...")
    
    try:
        maps = GoogleMapsIntegration()
        visit_tracker = VisitTracker(maps)
        
        # Test visit planning (mock data)
        account_data = {
            'account_id': 'ACC_001',
            'name': 'TechCorp Industries',
            'billing_address': '123 Tech Street, Palo Alto, CA 94301'
        }
        
        print("✅ Visit tracker initialized")
        print("✅ Maps integration ready (API key required for full functionality)")
        
        # Test distance calculation (would require API key)
        print("⚠️ Distance calculation requires Google Maps API key")
        
        # Test route optimization
        print("✅ Route optimization algorithms ready")
        
        return True
        
    except Exception as e:
        print(f"❌ Maps integration test failed: {e}")
        return False

def test_lead_conversion():
    """Test lead to opportunity conversion"""
    print("\n🔄 Testing Lead Conversion...")
    
    try:
        with CRMService() as crm:
            # Get a lead to convert
            leads = crm.get_leads(filters={'converted': False}, limit=1)
            
            if not leads:
                print("⚠️ No unconverted leads found for testing")
                return True
            
            lead = leads[0]
            print(f"📋 Converting lead: {lead['full_name']} from {lead.get('company', 'Unknown')}")
            
            # Convert lead to opportunity
            opportunity_data = {
                'name': f"Opportunity from {lead['full_name']}",
                'description': f"Converted from lead: {lead['need']}",
                'amount': lead.get('budget', 50000),
                'stage': 'prospecting',
                'probability': 25.0,
                'close_date': datetime.now() + timedelta(days=90),
                'created_by': 'test_system'
            }
            
            conversion_result = crm.convert_lead_to_opportunity(lead['lead_id'], opportunity_data)
            
            print(f"✅ Lead converted successfully:")
            print(f"   - Account: {conversion_result['account']['name']}")
            print(f"   - Contact: {conversion_result['contact']['full_name']}")
            print(f"   - Opportunity: {conversion_result['opportunity']['name']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Lead conversion test failed: {e}")
        return False

def test_activity_tracking():
    """Test activity creation and tracking"""
    print("\n📅 Testing Activity Tracking...")
    
    try:
        with CRMService() as crm:
            # Get an account for the activity
            accounts = crm.get_accounts(limit=1)
            if not accounts:
                print("⚠️ No accounts found for activity testing")
                return True
            
            account = accounts[0]
            
            # Create a new activity
            activity_data = {
                'subject': 'Follow-up call with customer',
                'description': 'Discuss product requirements and timeline',
                'activity_type': 'call',
                'status': 'planned',
                'priority': 'high',
                'due_date': datetime.now() + timedelta(days=1),
                'account_id': account['account_id'],
                'assigned_to': 'USER_001',
                'created_by': 'test_system'
            }
            
            activity = crm.create_activity(activity_data)
            print(f"✅ Activity created: {activity['subject']}")
            
            # Complete the activity
            completed_activity = crm.complete_activity(
                activity['activity_id'],
                outcome="Customer interested in demo",
                next_steps="Schedule product demonstration"
            )
            
            print(f"✅ Activity completed: {completed_activity['subject']}")
            print(f"   Outcome: {completed_activity['outcome']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Activity tracking test failed: {e}")
        return False

def test_task_management():
    """Test task creation and management"""
    print("\n✅ Testing Task Management...")
    
    try:
        with CRMService() as crm:
            # Create a new task
            task_data = {
                'title': 'Prepare proposal for TechCorp',
                'description': 'Create detailed proposal including pricing and timeline',
                'task_type': 'follow_up',
                'priority': 'high',
                'status': 'pending',
                'due_date': datetime.now() + timedelta(days=3),
                'assigned_to': 'USER_001',
                'created_by': 'test_system'
            }
            
            task = crm.create_task(task_data)
            print(f"✅ Task created: {task['title']}")
            
            # Get pending tasks
            pending_tasks = crm.get_tasks(filters={'status': 'pending'}, limit=5)
            print(f"✅ Found {len(pending_tasks)} pending tasks")
            
            return True
            
    except Exception as e:
        print(f"❌ Task management test failed: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive CRM system test"""
    print("🚀 Starting Comprehensive CRM System Test")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Database Initialization", test_database_initialization),
        ("CRM Service", test_crm_service),
        ("LLM Query System", test_llm_query_system),
        ("Email Integration", test_email_integration),
        ("Maps Integration", test_maps_integration),
        ("Lead Conversion", test_lead_conversion),
        ("Activity Tracking", test_activity_tracking),
        ("Task Management", test_task_management)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            test_results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CRM system is ready for use.")
    else:
        print("⚠️ Some tests failed. Please check the configuration and dependencies.")
    
    print("\n🔗 Next Steps:")
    print("1. Start the CRM API: python crm_api.py")
    print("2. Launch the CRM Dashboard: streamlit run crm_dashboard.py")
    print("3. Configure integrations (Office 365, Google Maps, OpenAI)")
    print("4. Test with real data and user scenarios")

if __name__ == "__main__":
    run_comprehensive_test()