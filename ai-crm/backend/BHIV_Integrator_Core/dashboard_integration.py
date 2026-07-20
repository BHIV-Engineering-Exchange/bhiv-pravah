#!/usr/bin/env python3
"""
Dashboard Integration for BHIV Integrator Core
Provides unified dashboard flow across all systems
"""

import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any

# Configuration
INTEGRATOR_URL = "http://localhost:8005"
DASHBOARD_URL = "http://localhost:8501"

def main():
    st.set_page_config(
        page_title="BHIV Integrator Dashboard",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 BHIV Integrator Core - Unified Dashboard")
    st.markdown("**Consolidated Logistics, CRM, and Task Management**")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select Module", [
        "System Overview",
        "Logistics Management",
        "CRM Management", 
        "Task Management",
        "Employee Management",
        "Event Monitoring",
        "Compliance Dashboard"
    ])
    
    if page == "System Overview":
        show_system_overview()
    elif page == "Logistics Management":
        show_logistics_dashboard()
    elif page == "CRM Management":
        show_crm_dashboard()
    elif page == "Task Management":
        show_task_dashboard()
    elif page == "Employee Management":
        show_employee_dashboard()
    elif page == "Event Monitoring":
        show_event_monitoring()
    elif page == "Compliance Dashboard":
        show_compliance_dashboard()

def show_system_overview():
    """Show system overview dashboard"""
    st.header("📊 System Overview")
    
    # System health check
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Integrator Status", "🟢 Online", "100% uptime")
    with col2:
        st.metric("BHIV Core", "🟢 Connected", "Response: 45ms")
    with col3:
        st.metric("Event Broker", "🟢 Active", "23 events/min")
    with col4:
        st.metric("Compliance", "🟢 Compliant", "98.5% rate")
    
    # Recent activity
    st.subheader("📈 Recent Activity")
    
    # Mock data for demo
    activity_data = [
        {"time": "10:30", "system": "Logistics", "event": "Order Created", "status": "✅"},
        {"time": "10:28", "system": "CRM", "event": "Lead Converted", "status": "✅"},
        {"time": "10:25", "system": "Task", "event": "Review Completed", "status": "✅"},
        {"time": "10:22", "system": "Employee", "event": "Attendance Recorded", "status": "✅"},
        {"time": "10:20", "system": "Compliance", "event": "Audit Log Created", "status": "✅"}
    ]
    
    df = pd.DataFrame(activity_data)
    st.dataframe(df, use_container_width=True)

def show_logistics_dashboard():
    """Show logistics management dashboard"""
    st.header("📦 Logistics Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Procurement Orders")
        if st.button("Create Procurement Order"):
            create_procurement_order()
        
        # Mock procurement data
        procurement_data = [
            {"ID": "PO-001", "Supplier": "TechSupply Co", "Amount": "$5,000", "Status": "Pending"},
            {"ID": "PO-002", "Supplier": "Global Parts", "Amount": "$3,200", "Status": "Approved"},
            {"ID": "PO-003", "Supplier": "Quick Delivery", "Amount": "$1,800", "Status": "Delivered"}
        ]
        st.dataframe(pd.DataFrame(procurement_data))
    
    with col2:
        st.subheader("Inventory Levels")
        
        # Mock inventory chart
        inventory_data = {
            "Product": ["Widget A", "Widget B", "Widget C", "Widget D"],
            "Current Stock": [45, 23, 67, 12],
            "Min Level": [50, 30, 40, 20]
        }
        
        fig = px.bar(inventory_data, x="Product", y=["Current Stock", "Min Level"],
                    title="Current vs Minimum Stock Levels")
        st.plotly_chart(fig, use_container_width=True)

def show_crm_dashboard():
    """Show CRM management dashboard"""
    st.header("👥 CRM Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales Pipeline")
        
        # Mock pipeline data
        pipeline_data = {
            "Stage": ["Lead", "Qualified", "Proposal", "Negotiation", "Closed Won"],
            "Count": [45, 23, 12, 8, 15],
            "Value": [225000, 460000, 240000, 320000, 750000]
        }
        
        fig = px.funnel(pipeline_data, x="Count", y="Stage", 
                       title="Sales Pipeline by Stage")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Recent Opportunities")
        
        opportunities_data = [
            {"Company": "TechCorp", "Value": "$50K", "Stage": "Proposal", "Probability": "75%"},
            {"Company": "InnovateLtd", "Value": "$35K", "Stage": "Negotiation", "Probability": "90%"},
            {"Company": "StartupXYZ", "Value": "$25K", "Stage": "Qualified", "Probability": "45%"}
        ]
        st.dataframe(pd.DataFrame(opportunities_data))

def show_task_dashboard():
    """Show task management dashboard"""
    st.header("📋 Task Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Task Status")
        
        # Mock task data
        task_status = {
            "Status": ["Open", "In Progress", "Review", "Completed"],
            "Count": [12, 8, 5, 23]
        }
        
        fig = px.pie(task_status, values="Count", names="Status",
                    title="Task Distribution by Status")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Pending Reviews")
        
        reviews_data = [
            {"Task": "Order Processing Review", "Assignee": "John Doe", "Due": "Today"},
            {"Task": "Customer Feedback Analysis", "Assignee": "Jane Smith", "Due": "Tomorrow"},
            {"Task": "Compliance Audit", "Assignee": "Bob Wilson", "Due": "2 days"}
        ]
        st.dataframe(pd.DataFrame(reviews_data))

def show_employee_dashboard():
    """Show employee management dashboard"""
    st.header("👨‍💼 Employee Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Attendance Overview")
        
        # Mock attendance data
        attendance_data = {
            "Date": pd.date_range(start="2024-01-01", periods=7),
            "Present": [45, 43, 46, 44, 47, 0, 0],
            "Late": [2, 4, 1, 3, 0, 0, 0],
            "Absent": [3, 3, 3, 3, 3, 50, 50]
        }
        
        df = pd.DataFrame(attendance_data)
        fig = px.line(df, x="Date", y=["Present", "Late", "Absent"],
                     title="Weekly Attendance Trends")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Performance Metrics")
        
        performance_data = [
            {"Employee": "John Doe", "Score": 95, "Tasks": 23, "Rating": "⭐⭐⭐⭐⭐"},
            {"Employee": "Jane Smith", "Score": 88, "Tasks": 19, "Rating": "⭐⭐⭐⭐"},
            {"Employee": "Bob Wilson", "Score": 92, "Tasks": 21, "Rating": "⭐⭐⭐⭐⭐"}
        ]
        st.dataframe(pd.DataFrame(performance_data))

def show_event_monitoring():
    """Show event monitoring dashboard"""
    st.header("📡 Event Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Event Flow")
        
        # Mock event data
        event_data = {
            "Time": pd.date_range(start="2024-01-01 10:00", periods=10, freq="5min"),
            "Events": [5, 8, 12, 6, 9, 15, 7, 11, 4, 13]
        }
        
        df = pd.DataFrame(event_data)
        fig = px.line(df, x="Time", y="Events", title="Event Volume Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Recent Events")
        
        events_data = [
            {"Type": "order_created", "Source": "logistics", "Priority": "high", "Status": "✅"},
            {"Type": "lead_converted", "Source": "crm", "Priority": "medium", "Status": "✅"},
            {"Type": "task_escalated", "Source": "task_manager", "Priority": "high", "Status": "⚠️"},
            {"Type": "compliance_check", "Source": "compliance", "Priority": "low", "Status": "✅"}
        ]
        st.dataframe(pd.DataFrame(events_data))

def show_compliance_dashboard():
    """Show compliance dashboard"""
    st.header("🔒 Compliance Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Compliance Metrics")
        
        # Mock compliance data
        compliance_metrics = {
            "Metric": ["GDPR Compliance", "Data Encryption", "Audit Trail", "Access Control"],
            "Status": [98.5, 100.0, 99.2, 95.8],
            "Target": [95.0, 100.0, 98.0, 95.0]
        }
        
        df = pd.DataFrame(compliance_metrics)
        fig = px.bar(df, x="Metric", y=["Status", "Target"],
                    title="Compliance Status vs Targets")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Audit Log Summary")
        
        audit_data = [
            {"Action": "Data Access", "User": "john.doe", "Status": "Approved", "Time": "10:30"},
            {"Action": "Record Update", "User": "jane.smith", "Status": "Logged", "Time": "10:25"},
            {"Action": "Export Data", "User": "admin", "Status": "Approved", "Time": "10:20"}
        ]
        st.dataframe(pd.DataFrame(audit_data))

def create_procurement_order():
    """Create a sample procurement order"""
    try:
        order_data = {
            "supplier_id": "SUPP-001",
            "items": [{"product": "Widget A", "quantity": 100, "price": 50.0}],
            "total_value": 5000.0,
            "delivery_date": "2024-02-01"
        }
        
        response = requests.post(f"{INTEGRATOR_URL}/logistics/procurement", json=order_data)
        if response.status_code == 200:
            st.success("✅ Procurement order created successfully!")
        else:
            st.error(f"❌ Failed to create order: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()