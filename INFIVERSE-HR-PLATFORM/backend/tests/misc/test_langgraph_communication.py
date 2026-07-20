#!/usr/bin/env python3
"""
BHIV HR Platform - LangGraph Communication Testing Script
Tests real communication channels: Email, WhatsApp, Telegram
"""

import requests
import json
import time
from datetime import datetime

# Configuration
LOCAL_LANGGRAPH_URL = "http://localhost:9001"
RENDER_LANGGRAPH_URL = "https://bhiv-hr-langgraph.onrender.com"
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"

def test_service_health(base_url, service_name):
    """Test if service is healthy"""
    print(f"\n🔍 Testing {service_name} Health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {service_name} is healthy")
            print(f"   Environment: {data.get('environment', 'unknown')}")
            print(f"   Version: {data.get('version', 'unknown')}")
            return True
        else:
            print(f"❌ {service_name} health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name} connection failed: {str(e)}")
        return False

def test_notification_endpoint(base_url, service_name):
    """Test notification sending endpoint"""
    print(f"\n📧 Testing {service_name} Notification System...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # Test data for notification
    notification_data = {
        "candidate_id": 999,
        "candidate_name": "Test User",
        "candidate_email": "test@example.com",
        "candidate_phone": "+1234567890",
        "job_title": "Software Engineer",
        "application_status": "shortlisted",
        "message": f"🧪 TEST NOTIFICATION from {service_name} at {datetime.now().strftime('%H:%M:%S')}\\n\\nThis is a test of the BHIV HR Platform communication system.",
        "channels": ["email"]  # Start with email only
    }
    
    try:
        response = requests.post(
            f"{base_url}/tools/send-notification",
            headers=headers,
            json=notification_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {service_name} notification sent successfully")
            print(f"   Channels: {result.get('channels_sent', [])}")
            print(f"   Sent at: {result.get('sent_at', 'unknown')}")
            return True
        else:
            print(f"❌ {service_name} notification failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {service_name} notification error: {str(e)}")
        return False

def test_workflow_creation(base_url, service_name):
    """Test workflow creation and execution"""
    print(f"\n🔄 Testing {service_name} Workflow Creation...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # Test workflow data
    workflow_data = {
        "candidate_id": 999,
        "job_id": 1,
        "application_id": 999,
        "candidate_email": "test@example.com",
        "candidate_phone": "+1234567890",
        "candidate_name": "Test User",
        "job_title": "Software Engineer",
        "job_description": "Test position for communication verification"
    }
    
    try:
        # Start workflow
        response = requests.post(
            f"{base_url}/workflows/application/start",
            headers=headers,
            json=workflow_data,
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            workflow_id = result.get("workflow_id")
            print(f"✅ {service_name} workflow created successfully")
            print(f"   Workflow ID: {workflow_id}")
            print(f"   Status: {result.get('status')}")
            
            # Wait a moment and check status
            time.sleep(3)
            return check_workflow_status(base_url, service_name, workflow_id, headers)
        else:
            print(f"❌ {service_name} workflow creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {service_name} workflow error: {str(e)}")
        return False

def check_workflow_status(base_url, service_name, workflow_id, headers):
    """Check workflow execution status"""
    print(f"\n📊 Checking {service_name} Workflow Status...")
    
    try:
        response = requests.get(
            f"{base_url}/workflows/{workflow_id}/status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ {service_name} workflow status retrieved")
            print(f"   Status: {status.get('status')}")
            print(f"   Progress: {status.get('progress_percentage', 0)}%")
            print(f"   Current Step: {status.get('current_step', 'unknown')}")
            return True
        else:
            print(f"❌ {service_name} status check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ {service_name} status error: {str(e)}")
        return False

def test_multi_channel_notification(base_url, service_name):
    """Test multi-channel notification (Email + WhatsApp + Telegram)"""
    print(f"\n🌐 Testing {service_name} Multi-Channel Communication...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # Test with all channels
    notification_data = {
        "candidate_id": 999,
        "candidate_name": "Test User Multi-Channel",
        "candidate_email": "shashankmishra0411@gmail.com",  # Real email for testing
        "candidate_phone": "+1234567890",
        "job_title": "Full Stack Developer",
        "application_status": "shortlisted",
        "message": f"🚀 MULTI-CHANNEL TEST from {service_name}\\n\\nTesting all communication channels:\\n✅ Email\\n✅ WhatsApp\\n✅ Telegram\\n\\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "channels": ["email", "whatsapp", "telegram"]
    }
    
    try:
        response = requests.post(
            f"{base_url}/tools/send-notification",
            headers=headers,
            json=notification_data,
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {service_name} multi-channel notification sent")
            print(f"   Channels attempted: {notification_data['channels']}")
            print(f"   Channels successful: {result.get('channels_sent', [])}")
            print(f"   Message: {result.get('message', 'No message')}")
            
            # Check your email, WhatsApp, and Telegram for messages!
            print(f"\n📱 CHECK YOUR DEVICES:")
            print(f"   📧 Email: shashankmishra0411@gmail.com")
            print(f"   📱 WhatsApp: {notification_data['candidate_phone']}")
            print(f"   💬 Telegram: @bhiv_hr_assistant_bot")
            
            return True
        else:
            print(f"❌ {service_name} multi-channel failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {service_name} multi-channel error: {str(e)}")
        return False

def main():
    """Main testing function"""
    print("🧪 BHIV HR Platform - LangGraph Communication Testing")
    print("=" * 60)
    
    # Test both local and production services
    services = [
        (LOCAL_LANGGRAPH_URL, "Local LangGraph"),
        (RENDER_LANGGRAPH_URL, "Production LangGraph")
    ]
    
    results = {}
    
    for base_url, service_name in services:
        print(f"\n{'='*20} {service_name} {'='*20}")
        
        # Test 1: Health Check
        health_ok = test_service_health(base_url, service_name)
        
        if health_ok:
            # Test 2: Basic Notification
            notification_ok = test_notification_endpoint(base_url, service_name)
            
            # Test 3: Workflow Creation
            workflow_ok = test_workflow_creation(base_url, service_name)
            
            # Test 4: Multi-Channel Communication (REAL TEST)
            multi_channel_ok = test_multi_channel_notification(base_url, service_name)
            
            results[service_name] = {
                "health": health_ok,
                "notification": notification_ok,
                "workflow": workflow_ok,
                "multi_channel": multi_channel_ok
            }
        else:
            results[service_name] = {
                "health": False,
                "notification": False,
                "workflow": False,
                "multi_channel": False
            }
    
    # Summary
    print(f"\n{'='*60}")
    print("🎯 TESTING SUMMARY")
    print("=" * 60)
    
    for service_name, tests in results.items():
        print(f"\n{service_name}:")
        for test_name, passed in tests.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test_name.capitalize()}: {status}")
    
    # Overall status
    all_tests = [test for tests in results.values() for test in tests.values()]
    success_rate = (sum(all_tests) / len(all_tests)) * 100 if all_tests else 0
    
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print("🎉 LangGraph communication system is working well!")
    elif success_rate >= 50:
        print("⚠️ LangGraph communication has some issues but is functional")
    else:
        print("❌ LangGraph communication system needs attention")
    
    print(f"\n📱 If multi-channel tests passed, check your devices for real messages!")

if __name__ == "__main__":
    main()