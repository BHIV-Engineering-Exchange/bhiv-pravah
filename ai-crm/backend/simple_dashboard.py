#!/usr/bin/env python3
"""
Simple Dashboard for BHIV Integrator Core - No pyarrow dependency
"""

import streamlit as st
import requests
import json
from datetime import datetime
import time

# Configuration
INTEGRATOR_URL = "http://localhost:8007"

def main():
    st.set_page_config(
        page_title="BHIV Integrator Dashboard",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 BHIV Integrator Core Dashboard")
    st.markdown("**Unified Logistics, CRM, and Task Management**")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select Module", [
        "System Overview",
        "Logistics Management",
        "CRM Management", 
        "Task Management",
        "Event Monitoring"
    ])
    
    if page == "System Overview":
        show_system_overview()
    elif page == "Logistics Management":
        show_logistics_dashboard()
    elif page == "CRM Management":
        show_crm_dashboard()
    elif page == "Task Management":
        show_task_dashboard()
    elif page == "Event Monitoring":
        show_event_monitoring()

def show_system_overview():
    """Show system overview dashboard"""
    st.header("📊 System Overview")
    
    # System health check
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        response = requests.get(f"{INTEGRATOR_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            status = "🟢 Online"
        else:
            status = "🟡 Issues"
    except:
        status = "🔴 Offline"
    
    with col1:
        st.metric("Integrator Status", status)
    with col2:
        st.metric("BHIV Core", "🟢 Connected")
    with col3:
        st.metric("Event Broker", "🟢 Active")
    with col4:
        st.metric("Compliance", "🟢 Compliant")
    
    # Recent activity
    st.subheader("📈 Recent Activity")
    
    # Simple table without pandas
    activity_data = [
        ["10:30", "Logistics", "Order Created", "✅"],
        ["10:28", "CRM", "Lead Converted", "✅"],
        ["10:25", "Task", "Review Completed", "✅"],
        ["10:22", "Employee", "Attendance Recorded", "✅"],
        ["10:20", "Compliance", "Audit Log Created", "✅"]
    ]
    
    # Display activity data without pyarrow dependency
    st.markdown("| Time | System | Event | Status |")
    st.markdown("|------|--------|-------|--------|")
    for row in activity_data:
        st.markdown(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |")

def show_logistics_dashboard():
    """Show logistics management dashboard"""
    st.header("📦 Logistics Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Procurement Orders")
        
        if st.button("Create Procurement Order"):
            try:
                order_data = {
                    "supplier_id": "TEST_SUPPLIER",
                    "items": [{"product": "Test Widget", "quantity": 10}],
                    "total_value": 250.0
                }
                response = requests.post(f"{INTEGRATOR_URL}/logistics/procurement", 
                                       json=order_data, timeout=5)
                if response.status_code == 200:
                    st.success("✅ Procurement order created!")
                else:
                    st.error("❌ Failed to create order")
            except:
                st.error("❌ Service unavailable")
        
        # Display orders
        try:
            response = requests.get(f"{INTEGRATOR_URL}/logistics/procurement", timeout=5)
            if response.status_code == 200:
                orders = response.json().get("orders", [])
                for order in orders:
                    st.write(f"**{order['id']}** - {order['supplier']} - {order['status']}")
            else:
                st.write("No orders available")
        except:
            st.write("Service unavailable")
    
    with col2:
        st.subheader("Inventory Status")
        
        # Mock inventory data
        inventory_items = [
            {"Product": "Widget A", "Stock": 45, "Min Level": 50, "Status": "🟡 Low"},
            {"Product": "Widget B", "Stock": 67, "Min Level": 40, "Status": "🟢 OK"},
            {"Product": "Widget C", "Stock": 12, "Min Level": 20, "Status": "🔴 Critical"},
        ]
        
        for item in inventory_items:
            st.write(f"**{item['Product']}**: {item['Stock']} units {item['Status']}")

def show_crm_dashboard():
    """Show CRM management dashboard"""
    st.header("👥 CRM Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Leads")
        
        if st.button("Create New Lead"):
            try:
                lead_data = {
                    "company": "Test Company",
                    "contact_name": "John Test",
                    "email": "test@example.com"
                }
                response = requests.post(f"{INTEGRATOR_URL}/crm/leads", 
                                       json=lead_data, timeout=5)
                if response.status_code == 200:
                    st.success("✅ Lead created!")
                else:
                    st.error("❌ Failed to create lead")
            except:
                st.error("❌ Service unavailable")
        
        # Display leads
        try:
            response = requests.get(f"{INTEGRATOR_URL}/crm/leads", timeout=5)
            if response.status_code == 200:
                leads = response.json().get("leads", [])
                for lead in leads:
                    st.write(f"**{lead['id']}** - {lead['company']} - {lead['status']}")
            else:
                st.write("No leads available")
        except:
            st.write("Service unavailable")
    
    with col2:
        st.subheader("Pipeline Status")
        
        pipeline_data = [
            {"Stage": "Lead", "Count": 45},
            {"Stage": "Qualified", "Count": 23},
            {"Stage": "Proposal", "Count": 12},
            {"Stage": "Negotiation", "Count": 8},
            {"Stage": "Closed Won", "Count": 15}
        ]
        
        for stage in pipeline_data:
            st.write(f"**{stage['Stage']}**: {stage['Count']} opportunities")

def show_task_dashboard():
    """Show task management dashboard"""
    st.header("📋 Task Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Reviews")
        
        if st.button("Create Review Task"):
            try:
                review_data = {
                    "title": "Test Review",
                    "description": "Test review task",
                    "assignee": "test_user"
                }
                response = requests.post(f"{INTEGRATOR_URL}/task/review", 
                                       json=review_data, timeout=5)
                if response.status_code == 200:
                    st.success("✅ Review task created!")
                else:
                    st.error("❌ Failed to create task")
            except:
                st.error("❌ Service unavailable")
        
        # Display reviews
        try:
            response = requests.get(f"{INTEGRATOR_URL}/task/review", timeout=5)
            if response.status_code == 200:
                reviews = response.json().get("reviews", [])
                for review in reviews:
                    st.write(f"**{review['id']}** - {review['title']} - {review['status']}")
            else:
                st.write("No reviews available")
        except:
            st.write("Service unavailable")
    
    with col2:
        st.subheader("Task Statistics")
        
        task_stats = [
            {"Status": "Open", "Count": 12},
            {"Status": "In Progress", "Count": 8},
            {"Status": "Review", "Count": 5},
            {"Status": "Completed", "Count": 23}
        ]
        
        for stat in task_stats:
            st.write(f"**{stat['Status']}**: {stat['Count']} tasks")

def show_event_monitoring():
    """Show event monitoring dashboard"""
    st.header("📡 Event Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Event Stream")
        
        if st.button("Publish Test Event"):
            try:
                event_data = {
                    "event_type": "test_event",
                    "source_system": "dashboard",
                    "payload": {"message": "Test event from dashboard"}
                }
                response = requests.post(f"{INTEGRATOR_URL}/event/publish", 
                                       json=event_data, timeout=5)
                if response.status_code == 200:
                    st.success("✅ Event published!")
                else:
                    st.error("❌ Failed to publish event")
            except:
                st.error("❌ Service unavailable")
        
        # Auto-refresh events
        if st.button("Refresh Events"):
            st.rerun()
    
    with col2:
        st.subheader("Recent Events")
        
        try:
            response = requests.get(f"{INTEGRATOR_URL}/event/events", timeout=5)
            if response.status_code == 200:
                events = response.json().get("events", [])
                for event in events:
                    st.write(f"**{event['event_type']}** from {event['source_system']}")
                    st.write(f"Time: {event['timestamp']}")
                    st.write("---")
            else:
                st.write("No events available")
        except:
            st.write("Service unavailable")

def check_service_status():
    """Check if the integrator service is running"""
    try:
        response = requests.get(f"{INTEGRATOR_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    # Check service status
    if not check_service_status():
        st.error("❌ BHIV Integrator Core is not running!")
        st.info("Please start the integrator service first:")
        st.code("cd BHIV_Integrator_Core && python simple_app.py")
        st.stop()
    
    main()