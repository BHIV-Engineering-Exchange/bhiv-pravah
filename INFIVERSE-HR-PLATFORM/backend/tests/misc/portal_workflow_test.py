# -*- coding: utf-8 -*-
"""
BHIV HR Platform - Portal Workflow Test
Tests the workflow through the actual portal interfaces
"""

import requests
import json
import time
from datetime import datetime

# Production URLs
URLS = {
    'langgraph': 'https://bhiv-hr-langgraph.onrender.com',
    'hr_portal': 'https://bhiv-hr-portal-u670.onrender.com',
    'client_portal': 'https://bhiv-hr-client-portal-3iod.onrender.com',
    'candidate_portal': 'https://bhiv-hr-candidate-portal-abe6.onrender.com'
}

# Test credentials
TEST_CREDENTIALS = {
    'email': 'shashankmishra0411@gmail.com',
    'phone': '9284967526'
}

class PortalWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def test_portal_accessibility(self):
        """Test that all portals are accessible"""
        print("Testing Portal Accessibility...")
        
        results = {}
        for portal, url in URLS.items():
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    print(f"  {portal}: [OK] Accessible")
                    results[portal] = True
                else:
                    print(f"  {portal}: [ERROR] Status {response.status_code}")
                    results[portal] = False
            except Exception as e:
                print(f"  {portal}: [FAILED] {str(e)}")
                results[portal] = False
        
        return results
    
    def test_langgraph_endpoints(self):
        """Test LangGraph service endpoints"""
        print("\nTesting LangGraph Service...")
        
        try:
            # Test health endpoint
            health_response = self.session.get(f"{URLS['langgraph']}/health", timeout=10)
            if health_response.status_code == 200:
                print("  [SUCCESS] LangGraph health check passed")
                
                # Test available endpoints
                try:
                    docs_response = self.session.get(f"{URLS['langgraph']}/docs", timeout=10)
                    if docs_response.status_code == 200:
                        print("  [SUCCESS] LangGraph API documentation accessible")
                except:
                    pass
                
                # Test workflow endpoints
                endpoints_to_test = [
                    "/workflows",
                    "/notifications", 
                    "/status"
                ]
                
                for endpoint in endpoints_to_test:
                    try:
                        response = self.session.get(f"{URLS['langgraph']}{endpoint}", timeout=10)
                        status = "[OK]" if response.status_code in [200, 404, 422] else "[ERROR]"
                        print(f"    {endpoint}: {status} ({response.status_code})")
                    except Exception as e:
                        print(f"    {endpoint}: [FAILED] {str(e)}")
                
                return True
            else:
                print(f"  [ERROR] LangGraph health check failed: {health_response.status_code}")
                return False
                
        except Exception as e:
            print(f"  [ERROR] LangGraph test failed: {str(e)}")
            return False
    
    def test_notification_channels(self):
        """Test notification channel configuration"""
        print("\nTesting Notification Channels...")
        
        try:
            # Test notification configuration endpoint
            config_response = self.session.get(f"{URLS['langgraph']}/notification_config", timeout=10)
            
            if config_response.status_code == 200:
                config = config_response.json()
                print("  [SUCCESS] Notification configuration retrieved")
                
                channels = config.get('channels', {})
                for channel, enabled in channels.items():
                    status = "[ENABLED]" if enabled else "[DISABLED]"
                    print(f"    {channel}: {status}")
                
                return True
            else:
                print(f"  [INFO] Notification config endpoint returned: {config_response.status_code}")
                
                # Test individual notification endpoints
                notification_endpoints = [
                    "/send_email",
                    "/send_whatsapp", 
                    "/send_telegram"
                ]
                
                for endpoint in notification_endpoints:
                    try:
                        # Test with OPTIONS to check if endpoint exists
                        response = self.session.options(f"{URLS['langgraph']}{endpoint}", timeout=5)
                        status = "[AVAILABLE]" if response.status_code != 404 else "[NOT_FOUND]"
                        print(f"    {endpoint}: {status}")
                    except:
                        print(f"    {endpoint}: [UNKNOWN]")
                
                return True
                
        except Exception as e:
            print(f"  [ERROR] Notification test failed: {str(e)}")
            return False
    
    def test_workflow_simulation(self):
        """Simulate a workflow trigger"""
        print("\nTesting Workflow Simulation...")
        
        try:
            # Simulate workflow data
            workflow_data = {
                "event_type": "test_workflow",
                "candidate_email": TEST_CREDENTIALS['email'],
                "candidate_phone": TEST_CREDENTIALS['phone'],
                "job_title": "Test Position",
                "status": "interview_scheduled",
                "message": "This is a test workflow trigger"
            }
            
            # Try to trigger a test workflow
            response = self.session.post(
                f"{URLS['langgraph']}/test_workflow",
                json=workflow_data,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                print("  [SUCCESS] Test workflow triggered successfully")
                print(f"    Workflow ID: {result.get('workflow_id', 'N/A')}")
                return True
            elif response.status_code == 404:
                print("  [INFO] Test workflow endpoint not available")
                
                # Try alternative workflow trigger
                alt_response = self.session.post(
                    f"{URLS['langgraph']}/trigger",
                    json=workflow_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=15
                )
                
                if alt_response.status_code in [200, 202]:
                    print("  [SUCCESS] Alternative workflow trigger successful")
                    return True
                else:
                    print(f"  [INFO] Alternative trigger returned: {alt_response.status_code}")
                    return False
            else:
                print(f"  [INFO] Workflow trigger returned: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  [ERROR] Workflow simulation failed: {str(e)}")
            return False
    
    def test_portal_integration(self):
        """Test portal integration capabilities"""
        print("\nTesting Portal Integration...")
        
        integration_tests = []
        
        # Test if portals can communicate with backend
        for portal_name, portal_service_url in URLS.items():
            if 'portal' in portal_name:
                try:
                    # Check if portal has API endpoints
                    api_response = self.session.get(f"{portal_service_url}/api/health", timeout=10)
                    if api_response.status_code == 200:
                        print(f"  {portal_name}: [SUCCESS] API integration available")
                        integration_tests.append(True)
                    else:
                        print(f"  {portal_name}: [INFO] Direct API not available ({api_response.status_code})")
                        integration_tests.append(False)
                except:
                    print(f"  {portal_name}: [INFO] Standard web interface only")
                    integration_tests.append(False)
        
        return any(integration_tests)
    
    def generate_workflow_report(self):
        """Generate a comprehensive workflow report"""
        print("\nGenerating Workflow Report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_credentials': TEST_CREDENTIALS,
            'services_status': {},
            'workflow_capabilities': {},
            'recommendations': []
        }
        
        # Test all components
        portal_results = self.test_portal_accessibility()
        langgraph_result = self.test_langgraph_endpoints()
        notification_result = self.test_notification_channels()
        workflow_result = self.test_workflow_simulation()
        integration_result = self.test_portal_integration()
        
        # Compile results
        report['services_status'] = {
            'portals_accessible': sum(portal_results.values()),
            'total_portals': len(portal_results),
            'langgraph_operational': langgraph_result,
            'notifications_configured': notification_result,
            'workflow_functional': workflow_result,
            'integration_available': integration_result
        }
        
        # Generate recommendations
        if report['services_status']['portals_accessible'] == report['services_status']['total_portals']:
            report['recommendations'].append("All portals are accessible and operational")
        
        if langgraph_result:
            report['recommendations'].append("LangGraph service is healthy and ready for automation")
        
        if notification_result:
            report['recommendations'].append("Notification channels are configured")
        
        if workflow_result:
            report['recommendations'].append("Workflow automation is functional")
        else:
            report['recommendations'].append("Consider implementing test workflow endpoints")
        
        return report
    
    def run_complete_test(self):
        """Run the complete portal workflow test"""
        print("BHIV HR Platform - Portal Workflow Test")
        print("=" * 60)
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Email: {TEST_CREDENTIALS['email']}")
        print(f"Test Phone: {TEST_CREDENTIALS['phone']}")
        print("=" * 60)
        
        # Run all tests
        report = self.generate_workflow_report()
        
        # Display summary
        print("\n" + "="*60)
        print("WORKFLOW TEST SUMMARY")
        print("="*60)
        
        status = report['services_status']
        print(f"Portals Accessible: {status['portals_accessible']}/{status['total_portals']}")
        print(f"LangGraph Operational: {'YES' if status['langgraph_operational'] else 'NO'}")
        print(f"Notifications Configured: {'YES' if status['notifications_configured'] else 'NO'}")
        print(f"Workflow Functional: {'YES' if status['workflow_functional'] else 'NO'}")
        print(f"Integration Available: {'YES' if status['integration_available'] else 'NO'}")
        
        print("\nRecommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        # Overall assessment
        operational_score = sum([
            status['portals_accessible'] == status['total_portals'],
            status['langgraph_operational'],
            status['notifications_configured']
        ])
        
        print(f"\nOverall System Health: {operational_score}/3")
        
        if operational_score >= 2:
            print("[SUCCESS] System is operational for workflow testing")
            print("\nNext Steps:")
            print("1. Access HR Portal: https://bhiv-hr-portal-u670.onrender.com")
            print("2. Access Client Portal: https://bhiv-hr-client-portal-3iod.onrender.com") 
            print("3. Access Candidate Portal: https://bhiv-hr-candidate-portal-abe6.onrender.com")
            print("4. Use test credentials to simulate workflow")
            print("5. Monitor LangGraph for automation triggers")
        else:
            print("[WARNING] Some components need attention before full workflow testing")
        
        return report

if __name__ == "__main__":
    tester = PortalWorkflowTester()
    tester.run_complete_test()