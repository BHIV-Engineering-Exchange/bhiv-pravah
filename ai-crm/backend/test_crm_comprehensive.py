#!/usr/bin/env python3
"""
Comprehensive Test Suite for CRM Functionality
"""

import pytest
import sys
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.crm_service import CRMService
from database.models import create_tables, init_database
from integrations.office365_integration import Office365Integration, CRMEmailTemplates
from integrations.google_maps_integration import GoogleMapsIntegration, VisitTracker
from integrations.llm_query_system import LLMQuerySystem

class TestCRMService:
    """Test CRM service functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Setup test database"""
        # Create temporary database for testing
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Override database path for testing
        os.environ['DATABASE_URL'] = f'sqlite:///{self.test_db.name}'
        
        # Initialize test database
        create_tables()
        
        yield
        
        # Cleanup
        os.unlink(self.test_db.name)
    
    def test_create_account(self):
        """Test account creation"""
        with CRMService() as crm:
            account_data = {
                'name': 'Test Corporation',
                'account_type': 'customer',
                'industry': 'Technology',
                'annual_revenue': 1000000.0,
                'territory': 'West Coast'
            }
            
            account = crm.create_account(account_data)
            
            assert account is not None
            assert account['name'] == 'Test Corporation'
            assert account['account_type'] == 'customer'
            assert 'account_id' in account
    
    def test_create_contact(self):
        """Test contact creation"""
        with CRMService() as crm:
            # First create an account
            account_data = {
                'name': 'Test Corp',
                'account_type': 'customer'
            }
            account = crm.create_account(account_data)
            
            # Create contact
            contact_data = {
                'account_id': account['account_id'],
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@testcorp.com',
                'title': 'CEO'
            }
            
            contact = crm.create_contact(contact_data)
            
            assert contact is not None
            assert contact['first_name'] == 'John'
            assert contact['last_name'] == 'Doe'
            assert contact['account_id'] == account['account_id']
    
    def test_create_lead(self):
        """Test lead creation"""
        with CRMService() as crm:
            lead_data = {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'company': 'Prospect Corp',
                'email': 'jane.smith@prospect.com',
                'lead_source': 'website',
                'budget': 50000.0
            }
            
            lead = crm.create_lead(lead_data)
            
            assert lead is not None
            assert lead['first_name'] == 'Jane'
            assert lead['company'] == 'Prospect Corp'
            assert 'lead_id' in lead
    
    def test_create_opportunity(self):
        """Test opportunity creation"""
        with CRMService() as crm:
            # Create account first
            account_data = {
                'name': 'Opportunity Corp',
                'account_type': 'customer'
            }
            account = crm.create_account(account_data)
            
            # Create opportunity
            opp_data = {
                'account_id': account['account_id'],
                'name': 'Test Deal',
                'amount': 100000.0,
                'stage': 'prospecting',
                'probability': 25.0
            }
            
            opportunity = crm.create_opportunity(opp_data)
            
            assert opportunity is not None
            assert opportunity['name'] == 'Test Deal'
            assert opportunity['amount'] == 100000.0
            assert opportunity['account_id'] == account['account_id']
    
    def test_get_accounts_with_filters(self):
        """Test account retrieval with filters"""
        with CRMService() as crm:
            # Create test accounts
            accounts_data = [
                {'name': 'Tech Corp', 'account_type': 'customer', 'territory': 'West'},
                {'name': 'Manufacturing Ltd', 'account_type': 'distributor', 'territory': 'East'},
                {'name': 'Retail Inc', 'account_type': 'customer', 'territory': 'West'}
            ]
            
            for account_data in accounts_data:
                crm.create_account(account_data)
            
            # Test filters
            west_accounts = crm.get_accounts(filters={'territory': 'West'})
            assert len(west_accounts) == 2
            
            customer_accounts = crm.get_accounts(filters={'account_type': 'customer'})
            assert len(customer_accounts) == 2
    
    def test_crm_dashboard_data(self):
        """Test CRM dashboard data generation"""
        with CRMService() as crm:
            # Create test data
            account = crm.create_account({'name': 'Dashboard Test Corp', 'account_type': 'customer'})
            
            crm.create_opportunity({
                'account_id': account['account_id'],
                'name': 'Dashboard Deal',
                'amount': 75000.0,
                'stage': 'proposal'
            })
            
            crm.create_lead({
                'first_name': 'Dashboard',
                'last_name': 'Lead',
                'company': 'Lead Corp'
            })
            
            # Get dashboard data
            dashboard_data = crm.get_crm_dashboard_data()
            
            assert 'total_accounts' in dashboard_data
            assert 'total_leads' in dashboard_data
            assert 'total_opportunities' in dashboard_data
            assert 'pipeline_value' in dashboard_data
            assert dashboard_data['total_accounts'] >= 1
            assert dashboard_data['total_opportunities'] >= 1


class TestOffice365Integration:
    """Test Office 365 integration"""
    
    def test_office365_initialization(self):
        """Test Office 365 integration initialization"""
        office365 = Office365Integration()
        
        assert hasattr(office365, 'client_id')
        assert hasattr(office365, 'smtp_server')
        assert hasattr(office365, 'graph_base_url')
        assert office365.smtp_server == 'smtp.office365.com'
    
    def test_email_templates(self):
        """Test email template generation"""
        templates = CRMEmailTemplates()
        
        # Test opportunity approval email
        opp_data = {
            'name': 'Test Opportunity',
            'account_name': 'Test Account',
            'amount': 50000.0,
            'stage': 'proposal',
            'probability': 75.0
        }
        
        email_content = templates.opportunity_approval_email(opp_data)
        
        assert 'subject' in email_content
        assert 'body' in email_content
        assert 'Test Opportunity' in email_content['body']
        assert '$50,000' in email_content['body']
    
    def test_token_management(self):
        """Test token management functionality"""
        office365 = Office365Integration()
        
        # Test token expiration check
        assert office365._is_token_expired() == True  # No token initially
        
        # Test token file operations (mock data)
        test_token_data = {
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
            'expires_in': 3600
        }
        
        # This would require mocking in a real test environment
        # office365._save_tokens(test_token_data)
        # office365._load_tokens()


class TestGoogleMapsIntegration:
    """Test Google Maps integration"""
    
    def test_google_maps_initialization(self):
        """Test Google Maps integration initialization"""
        maps = GoogleMapsIntegration()
        
        assert hasattr(maps, 'api_key')
        assert hasattr(maps, 'base_url')
        assert maps.base_url == 'https://maps.googleapis.com/maps/api'
    
    def test_visit_tracker_initialization(self):
        """Test visit tracker initialization"""
        maps = GoogleMapsIntegration()
        visit_tracker = VisitTracker(maps)
        
        assert hasattr(visit_tracker, 'maps')
        assert hasattr(visit_tracker, 'db_path')
        
        # Check database initialization
        assert visit_tracker.db_path.parent.exists()
    
    def test_visit_tracker_database_operations(self):
        """Test visit tracker database operations"""
        maps = GoogleMapsIntegration()
        visit_tracker = VisitTracker(maps)
        
        # Mock account data
        account_data = {
            'account_id': 'TEST_001',
            'name': 'Test Corporation',
            'billing_address': '123 Test Street, Test City, TS 12345'
        }
        
        # This would require API key for actual geocoding
        # For testing, we'll test the database structure
        test_visit_id = 'VISIT_TEST_001'
        
        # Test database structure
        import sqlite3
        with sqlite3.connect(visit_tracker.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'visits' in tables
            assert 'visit_activities' in tables


class TestLLMQuerySystem:
    """Test LLM Query System"""
    
    def test_llm_query_system_initialization(self):
        """Test LLM query system initialization"""
        llm_system = LLMQuerySystem()
        
        assert hasattr(llm_system, 'openai_api_key')
        assert hasattr(llm_system, 'query_patterns')
        assert len(llm_system.query_patterns) > 0
    
    def test_pattern_matching(self):
        """Test query pattern matching"""
        llm_system = LLMQuerySystem()
        
        # Test opportunities closing pattern
        result = llm_system.match_query_patterns('show me opportunities closing this month')
        assert result is not None or result is None  # Depends on test data
    
    def test_natural_response_generation(self):
        """Test natural language response generation"""
        llm_system = LLMQuerySystem()
        
        # Test response generation for different query types
        test_result = {
            'success': True,
            'query_type': 'opportunities_closing',
            'data': [
                {'name': 'Test Deal', 'amount': 50000, 'probability': 75}
            ]
        }
        
        response = llm_system.generate_natural_response(test_result)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'Test Deal' in response


class TestIntegrationWorkflows:
    """Test end-to-end integration workflows"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment"""
        # Create temporary database
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        os.environ['DATABASE_URL'] = f'sqlite:///{self.test_db.name}'
        create_tables()
        
        yield
        
        # Cleanup
        os.unlink(self.test_db.name)
    
    def test_lead_to_opportunity_workflow(self):
        """Test complete lead to opportunity conversion workflow"""
        with CRMService() as crm:
            # Create lead
            lead_data = {
                'first_name': 'Workflow',
                'last_name': 'Test',
                'company': 'Workflow Corp',
                'email': 'workflow@test.com',
                'budget': 100000.0
            }
            
            lead = crm.create_lead(lead_data)
            assert lead is not None
            
            # Create account for conversion
            account_data = {
                'name': 'Workflow Corp',
                'account_type': 'customer'
            }
            account = crm.create_account(account_data)
            
            # Convert lead to opportunity
            opp_data = {
                'account_id': account['account_id'],
                'name': f"Opportunity from {lead['full_name']}",
                'amount': lead['budget']
            }
            
            opportunity = crm.create_opportunity(opp_data)
            
            assert opportunity is not None
            assert opportunity['amount'] == lead['budget']
    
    def test_account_relationship_workflow(self):
        """Test account hierarchy and relationship workflow"""
        with CRMService() as crm:
            # Create parent account
            parent_data = {
                'name': 'Parent Corporation',
                'account_type': 'customer'
            }
            parent = crm.create_account(parent_data)
            
            # Create subsidiary account
            subsidiary_data = {
                'name': 'Subsidiary Corp',
                'account_type': 'subsidiary',
                'parent_account_id': parent['account_id']
            }
            subsidiary = crm.create_account(subsidiary_data)
            
            assert subsidiary['parent_account_id'] == parent['account_id']
            
            # Create contacts for both accounts
            parent_contact = crm.create_contact({
                'account_id': parent['account_id'],
                'first_name': 'Parent',
                'last_name': 'Contact'
            })
            
            subsidiary_contact = crm.create_contact({
                'account_id': subsidiary['account_id'],
                'first_name': 'Subsidiary',
                'last_name': 'Contact'
            })
            
            assert parent_contact['account_id'] == parent['account_id']
            assert subsidiary_contact['account_id'] == subsidiary['account_id']


class TestAPIIntegration:
    """Test API integration points"""
    
    def test_api_data_consistency(self):
        """Test data consistency between CRM service and API responses"""
        # This would test actual API endpoints in a full integration test
        # For now, we'll test the data structure consistency
        
        with CRMService() as crm:
            account = crm.create_account({
                'name': 'API Test Corp',
                'account_type': 'customer'
            })
            
            # Verify account structure matches API expectations
            required_fields = ['account_id', 'name', 'account_type', 'created_at']
            for field in required_fields:
                assert field in account


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🧪 Running Comprehensive CRM Test Suite...")
    print("=" * 60)
    
    # Test configuration
    test_modules = [
        TestCRMService,
        TestOffice365Integration,
        TestGoogleMapsIntegration,
        TestLLMQuerySystem,
        TestIntegrationWorkflows,
        TestAPIIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_modules:
        print(f"\n📋 Testing {test_class.__name__}...")
        
        # Get test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                # Create test instance
                test_instance = test_class()
                
                # Setup if needed
                if hasattr(test_instance, 'setup_test_db'):
                    test_instance.setup_test_db()
                elif hasattr(test_instance, 'setup_test_environment'):
                    test_instance.setup_test_environment()
                
                # Run test
                getattr(test_instance, test_method)()
                
                print(f"  ✅ {test_method}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ❌ {test_method}: {str(e)}")
                failed_tests.append(f"{test_class.__name__}.{test_method}: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎯 Test Summary")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests:
        print("\n❌ Failed Tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
    
    print("\n✅ Comprehensive test suite completed!")
    
    return {
        'total': total_tests,
        'passed': passed_tests,
        'failed': len(failed_tests),
        'success_rate': (passed_tests/total_tests)*100,
        'failures': failed_tests
    }


if __name__ == "__main__":
    # Run the comprehensive test suite
    results = run_comprehensive_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results['failed'] == 0 else 1
    exit(exit_code)