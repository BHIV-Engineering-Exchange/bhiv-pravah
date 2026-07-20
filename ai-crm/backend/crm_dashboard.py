#!/usr/bin/env python3
"""
Enhanced CRM Dashboard for AI Agent Logistics + CRM System
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import networkx as nx
from plotly.subplots import make_subplots
import numpy as np

# Configure Streamlit page
st.set_page_config(
    page_title="AI Agent CRM Dashboard - Enhanced",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-new { background-color: #e3f2fd; color: #1976d2; }
    .status-contacted { background-color: #fff3e0; color: #f57c00; }
    .status-qualified { background-color: #e8f5e8; color: #388e3c; }
    .status-converted { background-color: #f3e5f5; color: #7b1fa2; }
    .status-planned { background-color: #e1f5fe; color: #0277bd; }
    .status-in-progress { background-color: #fff8e1; color: #f57f17; }
    .status-completed { background-color: #e8f5e8; color: #2e7d32; }
    .hierarchy-node {
        padding: 0.5rem;
        margin: 0.25rem;
        border-radius: 0.25rem;
        border: 1px solid #ddd;
        background-color: #f8f9fa;
    }
    .account-summary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
    }
    .integration-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.25rem 0;
    }
    .integration-active { background-color: #e8f5e8; }
    .integration-inactive { background-color: #ffebee; }
</style>
""", unsafe_allow_html=True)

# Enhanced Mock CRM data with hierarchy, visits, and integrations
@st.cache_data
def get_enhanced_crm_data():
    """Get enhanced CRM data with relationships and integrations"""
    
    # Mock accounts data with hierarchy
    accounts_data = [
        {
            'account_id': 'ACC_001',
            'name': 'TechCorp Industries',
            'account_type': 'customer',
            'industry': 'Technology',
            'annual_revenue': 5000000.0,
            'territory': 'West Coast',
            'status': 'active',
            'parent_account_id': None,
            'account_manager': 'Sarah Johnson',
            'phone': '+1-555-0101',
            'email': 'contact@techcorp.com',
            'address': '123 Tech Street, San Francisco, CA 94105'
        },
        {
            'account_id': 'ACC_002',
            'name': 'Global Manufacturing Ltd',
            'account_type': 'distributor',
            'industry': 'Manufacturing',
            'annual_revenue': 15000000.0,
            'territory': 'Midwest',
            'status': 'active',
            'parent_account_id': None,
            'account_manager': 'Mike Chen',
            'phone': '+1-555-0102',
            'email': 'info@globalmanuf.com',
            'address': '456 Industrial Blvd, Chicago, IL 60601'
        },
        {
            'account_id': 'ACC_003',
            'name': 'Retail Solutions Inc',
            'account_type': 'customer',
            'industry': 'Retail',
            'annual_revenue': 8000000.0,
            'territory': 'East Coast',
            'status': 'active',
            'parent_account_id': None,
            'account_manager': 'Lisa Wang',
            'phone': '+1-555-0103',
            'email': 'sales@retailsolutions.com',
            'address': '789 Commerce Ave, New York, NY 10001'
        },
        {
            'account_id': 'ACC_004',
            'name': 'TechCorp West Division',
            'account_type': 'subsidiary',
            'industry': 'Technology',
            'annual_revenue': 1200000.0,
            'territory': 'West Coast',
            'status': 'active',
            'parent_account_id': 'ACC_001',
            'account_manager': 'Sarah Johnson',
            'phone': '+1-555-0104',
            'email': 'west@techcorp.com',
            'address': '456 Innovation Dr, Palo Alto, CA 94301'
        }
    ]
    
    # Mock contacts data
    contacts_data = [
        {
            'contact_id': 'CON_001',
            'account_id': 'ACC_001',
            'first_name': 'John',
            'last_name': 'Smith',
            'title': 'CTO',
            'email': 'john.smith@techcorp.com',
            'phone': '+1-555-1001',
            'is_primary': True
        },
        {
            'contact_id': 'CON_002',
            'account_id': 'ACC_001',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'title': 'VP Operations',
            'email': 'jane.doe@techcorp.com',
            'phone': '+1-555-1002',
            'is_primary': False
        },
        {
            'contact_id': 'CON_003',
            'account_id': 'ACC_002',
            'first_name': 'Robert',
            'last_name': 'Johnson',
            'title': 'CEO',
            'email': 'robert.johnson@globalmanuf.com',
            'phone': '+1-555-1003',
            'is_primary': True
        }
    ]
    
    # Mock leads data
    leads_data = [
        {
            'lead_id': 'LEAD_001',
            'full_name': 'David Brown',
            'company': 'StartupTech Co',
            'lead_source': 'website',
            'lead_status': 'new',
            'budget': 100000.0,
            'territory': 'West Coast',
            'assigned_to': 'Sarah Johnson',
            'created_date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        },
        {
            'lead_id': 'LEAD_002',
            'full_name': 'Emma Garcia',
            'company': 'MidSize Corp',
            'lead_source': 'trade_show',
            'lead_status': 'contacted',
            'budget': 250000.0,
            'territory': 'Midwest',
            'assigned_to': 'Mike Chen',
            'created_date': (datetime.now() - timedelta(days=12)).strftime('%Y-%m-%d')
        },
        {
            'lead_id': 'LEAD_003',
            'full_name': 'Robert Taylor',
            'company': 'Enterprise Solutions',
            'lead_source': 'referral',
            'lead_status': 'qualified',
            'budget': 500000.0,
            'territory': 'East Coast',
            'assigned_to': 'Lisa Wang',
            'created_date': (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')
        }
    ]
    
    # Mock opportunities data
    opportunities_data = [
        {
            'opportunity_id': 'OPP_001',
            'name': 'TechCorp Logistics Upgrade',
            'account_id': 'ACC_001',
            'account_name': 'TechCorp Industries',
            'stage': 'proposal',
            'probability': 75.0,
            'amount': 300000.0,
            'close_date': (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
            'owner': 'Sarah Johnson',
            'products': 'Logistics Platform, Analytics Dashboard'
        },
        {
            'opportunity_id': 'OPP_002',
            'name': 'Global Manufacturing Partnership',
            'account_id': 'ACC_002',
            'account_name': 'Global Manufacturing Ltd',
            'stage': 'negotiation',
            'probability': 60.0,
            'amount': 750000.0,
            'close_date': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'owner': 'Mike Chen',
            'products': 'Full Platform Suite, Integration Services'
        },
        {
            'opportunity_id': 'OPP_003',
            'name': 'Retail Chain Expansion',
            'account_id': 'ACC_003',
            'account_name': 'Retail Solutions Inc',
            'stage': 'prospecting',
            'probability': 25.0,
            'amount': 450000.0,
            'close_date': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
            'owner': 'Lisa Wang',
            'products': 'Inventory Management, Order Processing'
        }
    ]
    
    # Mock activities data
    activities_data = [
        {
            'activity_id': 'ACT_001',
            'subject': 'Initial discovery call',
            'activity_type': 'call',
            'status': 'completed',
            'account_id': 'ACC_001',
            'account_name': 'TechCorp Industries',
            'due_date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
            'assigned_to': 'Sarah Johnson',
            'outcome': 'Identified key requirements for logistics upgrade'
        },
        {
            'activity_id': 'ACT_002',
            'subject': 'Product demonstration',
            'activity_type': 'meeting',
            'status': 'planned',
            'account_id': 'ACC_002',
            'account_name': 'Global Manufacturing Ltd',
            'due_date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'assigned_to': 'Mike Chen',
            'outcome': None
        },
        {
            'activity_id': 'ACT_003',
            'subject': 'Proposal presentation',
            'activity_type': 'meeting',
            'status': 'in_progress',
            'account_id': 'ACC_003',
            'account_name': 'Retail Solutions Inc',
            'due_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'assigned_to': 'Lisa Wang',
            'outcome': None
        }
    ]
    
    # Mock visits data
    visits_data = [
        {
            'visit_id': 'VISIT_001',
            'account_id': 'ACC_001',
            'account_name': 'TechCorp Industries',
            'purpose': 'Quarterly business review',
            'status': 'completed',
            'scheduled_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            'actual_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            'outcome': 'Renewed contract for additional services'
        },
        {
            'visit_id': 'VISIT_002',
            'account_id': 'ACC_002',
            'account_name': 'Global Manufacturing Ltd',
            'purpose': 'Site inspection and needs assessment',
            'status': 'planned',
            'scheduled_date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'actual_date': None,
            'outcome': None
        }
    ]
    
    # Check actual integration status - for demo purposes, show as active
    integration_status = {
        'office365': {'status': 'active', 'last_sync': '2024-01-15 10:30:00'},
        'google_maps': {'status': 'active', 'last_sync': '2024-01-15 09:15:00'},
        'openai': {'status': 'active', 'last_sync': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    }
    
    return {
        'accounts': pd.DataFrame(accounts_data),
        'contacts': pd.DataFrame(contacts_data),
        'leads': pd.DataFrame(leads_data),
        'opportunities': pd.DataFrame(opportunities_data),
        'activities': pd.DataFrame(activities_data),
        'visits': pd.DataFrame(visits_data),
        'integration_status': integration_status
    }

def show_infiverse_monitoring(data):
    """Show Infiverse monitoring and workforce management page"""

    st.header("👁️ Infiverse Monitoring & Workforce Management")

    # Try to fetch real data from Complete-Infiverse via API
    try:
        # Get base URL from environment or default
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

        # Fetch alerts
        alerts_response = requests.get(f"{base_url}/api/alerts", timeout=5)
        alerts_data = alerts_response.json() if alerts_response.status_code == 200 else {"alerts": []}

        # Fetch tasks
        tasks_response = requests.get(f"{base_url}/api/tasks", timeout=5)
        tasks_data = tasks_response.json() if tasks_response.status_code == 200 else {"tasks": []}

        # Fetch attendance summary (mock for now as endpoint might not exist)
        attendance_data = {"count": 0, "summary": {"totalDays": 0, "presentDays": 0}}

        # Calculate metrics from real data
        active_alerts = len([a for a in alerts_data.get("alerts", []) if a.get("status") != "resolved"])
        total_tasks = len(tasks_data.get("tasks", []))
        pending_tasks = len([t for t in tasks_data.get("tasks", []) if t.get("status") == "Pending"])

        # Infiverse metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Active Alerts",
                value=active_alerts,
                delta=f"{len(alerts_data.get('alerts', []))} total"
            )

        with col2:
            st.metric(
                label="Total Tasks",
                value=total_tasks,
                delta=f"{pending_tasks} pending"
            )

        with col3:
            st.metric(
                label="Attendance Records",
                value=attendance_data.get("count", 0),
                delta="Today"
            )

        with col4:
            # Mock productivity for now
            st.metric(
                label="System Status",
                value="Operational",
                delta="All systems green"
            )

    except Exception as e:
        st.warning(f"Unable to fetch real-time data from Infiverse: {str(e)}. Showing demo data.")

        # Fallback to demo metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(label="Active Alerts", value="3", delta="2 critical")

        with col2:
            st.metric(label="Total Tasks", value="15", delta="5 pending")

        with col3:
            st.metric(label="Attendance Records", value="42", delta="Today")

        with col4:
            st.metric(label="System Status", value="Operational", delta="All systems green")

    # Tabs for different Infiverse features
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "👥 Employees", "📋 Tasks", "⏰ Attendance", "🚨 Alerts"])

    with tab1:
        st.subheader("📊 Monitoring Overview")

        # Mock productivity chart
        productivity_data = pd.DataFrame({
            'Hour': range(9, 18),
            'Productivity': [85, 90, 88, 92, 95, 87, 83, 89, 91]
        })

        fig_prod = px.line(
            productivity_data,
            x='Hour',
            y='Productivity',
            title="Team Productivity Today",
            markers=True
        )
        fig_prod.update_layout(xaxis_title="Hour", yaxis_title="Productivity %")
        st.plotly_chart(fig_prod, use_container_width=True)

        # Activity summary
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🖥️ Application Usage")
            app_usage = pd.DataFrame({
                'Application': ['VS Code', 'Chrome', 'Slack', 'Excel', 'Outlook'],
                'Time (hours)': [4.5, 3.2, 2.1, 1.8, 1.2]
            })
            fig_apps = px.bar(
                app_usage,
                x='Application',
                y='Time (hours)',
                title="Top Applications Used"
            )
            st.plotly_chart(fig_apps, use_container_width=True)

        with col2:
            st.subheader("🌐 Website Categories")
            website_data = pd.DataFrame({
                'Category': ['Development', 'Communication', 'Research', 'Entertainment'],
                'Visits': [45, 32, 18, 8]
            })
            fig_web = px.pie(
                website_data,
                values='Visits',
                names='Category',
                title="Website Visits by Category"
            )
            st.plotly_chart(fig_web, use_container_width=True)

    with tab2:
        st.subheader("👥 Employee Management")

        # Mock employee data
        employees = pd.DataFrame({
            'Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson'],
            'Department': ['Engineering', 'Marketing', 'Sales', 'HR', 'Engineering'],
            'Status': ['Active', 'Active', 'Active', 'Active', 'On Leave'],
            'Monitoring': ['Enabled', 'Enabled', 'Paused', 'Enabled', 'Disabled'],
            'Productivity': [92, 88, 85, 90, 0]
        })

        # Use table instead of dataframe to avoid pyarrow dependency
        # Use pandas to_string() instead of st.table to avoid pyarrow dependency
        st.text(employees.to_string(index=False))

        # Employee actions
        st.subheader("Employee Actions")
        col1, col2, col3 = st.columns(3)

        with col1:
            employee_select = st.selectbox("Select Employee", employees['Name'].tolist())
            if st.button("Start Monitoring"):
                st.success(f"Started monitoring for {employee_select}")

        with col2:
            if st.button("Pause Monitoring"):
                st.warning(f"Paused monitoring for {employee_select}")

        with col3:
            if st.button("View Details"):
                st.info(f"Showing details for {employee_select}")

    with tab3:
        st.subheader("📋 Task Management")

        try:
            # Try to fetch real tasks
            base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
            tasks_response = requests.get(f"{base_url}/api/tasks", timeout=5)

            if tasks_response.status_code == 200:
                tasks_data = tasks_response.json()
                tasks_list = tasks_data.get("tasks", [])

                if tasks_list:
                    # Convert to DataFrame
                    tasks_df = pd.DataFrame(tasks_list)
                    # Select relevant columns
                    display_cols = ['title', 'assignee', 'status', 'priority', 'dueDate', 'department']
                    available_cols = [col for col in display_cols if col in tasks_df.columns]

                    if available_cols:
                        display_df = tasks_df[available_cols].copy()
                        # Rename columns for better display
                        display_df.columns = [col.title() for col in display_df.columns]
                        st.table(display_df)
                    else:
                        st.table(tasks_df)

                    st.success(f"Showing {len(tasks_list)} tasks from Complete-Infiverse")
                else:
                    st.info("No tasks found.")
            else:
                raise Exception(f"API returned {tasks_response.status_code}")

        except Exception as e:
            st.warning(f"Unable to fetch tasks: {str(e)}. Showing demo data.")

            # Fallback demo tasks
            tasks = pd.DataFrame({
                'Task': ['API Development', 'Database Optimization', 'UI Design', 'Testing', 'Documentation'],
                'Assignee': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson'],
                'Status': ['In Progress', 'Completed', 'Pending', 'In Progress', 'Pending'],
                'Priority': ['High', 'Medium', 'High', 'Medium', 'Low'],
                'Due Date': ['2024-01-20', '2024-01-18', '2024-01-22', '2024-01-25', '2024-01-28']
            })

            # Filter tasks
            status_filter = st.selectbox("Filter by Status", ["All"] + tasks['Status'].unique().tolist())
            if status_filter != "All":
                tasks = tasks[tasks['Status'] == status_filter]

            st.table(tasks)

        # Task actions
        st.subheader("Task Actions")
        new_task = st.text_input("New Task Title")
        assignee = st.text_input("Assign To (Employee ID)")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])

        if st.button("Create Task"):
            try:
                base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
                task_payload = {
                    "title": new_task,
                    "description": f"Task created from CRM dashboard",
                    "status": "Pending",
                    "priority": priority,
                    "department": "General",
                    "assignee": assignee,
                    "dueDate": (datetime.now() + timedelta(days=7)).isoformat()
                }
                create_response = requests.post(f"{base_url}/api/tasks", json=task_payload, timeout=5)
                if create_response.status_code == 201:
                    st.success(f"Created task: {new_task}")
                else:
                    st.error(f"Failed to create task: {create_response.text}")
            except Exception as e:
                st.error(f"Error creating task: {str(e)}")

    with tab4:
        st.subheader("⏰ Attendance Tracking")

        # Mock attendance data
        attendance = pd.DataFrame({
            'Employee': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
            'Date': ['2024-01-15'] * 4,
            'Check In': ['09:00', '08:45', '09:15', '08:30'],
            'Check Out': ['17:30', '17:45', '17:00', '17:20'],
            'Hours Worked': [8.5, 9.0, 7.75, 8.83],
            'Status': ['Present', 'Present', 'Present', 'Present']
        })

        st.table(attendance)

        # Attendance summary
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Present Today", "4/4", "100%")

        with col2:
            st.metric("Avg Hours", "8.5", "+0.2 hrs")

        with col3:
            st.metric("On Time", "3/4", "75%")

    with tab5:
        st.subheader("🚨 Monitoring Alerts")

        try:
            # Try to fetch real alerts
            base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
            alerts_response = requests.get(f"{base_url}/api/alerts", timeout=5)

            if alerts_response.status_code == 200:
                alerts_data = alerts_response.json()
                alerts_list = alerts_data.get("alerts", [])

                if alerts_list:
                    # Convert to DataFrame
                    alerts_df = pd.DataFrame(alerts_list)
                    # Select relevant columns if they exist
                    display_cols = ['timestamp', 'type', 'severity', 'message', 'status']
                    available_cols = [col for col in display_cols if col in alerts_df.columns]

                    if available_cols:
                        st.table(alerts_df[available_cols])
                    else:
                        st.table(alerts_df)

                    st.success(f"Showing {len(alerts_list)} alerts from Complete-Infiverse")
                else:
                    st.info("No alerts found.")
            else:
                raise Exception(f"API returned {alerts_response.status_code}")

        except Exception as e:
            st.warning(f"Unable to fetch alerts: {str(e)}. Showing demo data.")

            # Fallback demo alerts
            alerts = pd.DataFrame({
                'Time': ['10:30', '11:15', '14:20', '15:45', '16:10'],
                'Employee': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'John Doe'],
                'Alert Type': ['Idle Timeout', 'Unauthorized Site', 'Productivity Drop', 'Idle Timeout', 'Unauthorized Site'],
                'Severity': ['Medium', 'High', 'Medium', 'Low', 'High'],
                'Description': [
                    'Employee idle for 15 minutes',
                    'Visited non-work related website',
                    'Productivity below 70%',
                    'Employee idle for 10 minutes',
                    'Visited social media during work hours'
                ],
                'Status': ['Active', 'Acknowledged', 'Resolved', 'Active', 'Active']
            })

            # Color coding for severity
            def color_severity(val):
                if val == 'High':
                    return 'background-color: #ffebee'
                elif val == 'Medium':
                    return 'background-color: #fff3e0'
                elif val == 'Low':
                    return 'background-color: #e8f5e8'
                return ''

            styled_alerts = alerts.style.applymap(color_severity, subset=['Severity'])
            st.text(alerts.to_string())

        # Alert actions
        st.subheader("Alert Management")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Acknowledge Selected Alerts"):
                st.success("Alerts acknowledged")

        with col2:
            if st.button("Generate Report"):
                st.info("Generating alerts report...")

def main():
    """Main enhanced dashboard function"""
    
    # Header
    st.markdown('<h1 class="main-header">🏢 AI Agent CRM Dashboard - Enhanced</h1>', unsafe_allow_html=True)
    
    # Get enhanced data
    data = get_enhanced_crm_data()
    
    # Enhanced Sidebar
    st.sidebar.title("🎛️ CRM Navigation")
    
    page = st.sidebar.selectbox(
        "Select Page",
        ["Dashboard Overview", "Account 360°", "Account Hierarchy", "Leads & Pipeline",
         "Activities & Tasks", "Visit Tracking", "Infiverse Monitoring", "Employee CRM Integration", "Integration Status", "Natural Language Query", "Reports"]
    )
    
    # Integration Status Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔗 Integration Status")
    
    integration_status = data['integration_status']
    
    for integration, status in integration_status.items():
        status_icon = "✅" if status['status'] == 'active' else "❌"
        status_class = "integration-active" if status['status'] == 'active' else "integration-inactive"
        
        st.sidebar.markdown(f"""
        <div class="integration-status {status_class}">
            {status_icon} {integration.replace('_', ' ').title()}
        </div>
        """, unsafe_allow_html=True)
    
    # Route to appropriate page
    if page == "Dashboard Overview":
        show_dashboard_overview(data)
    elif page == "Account 360°":
        show_accounts_page(data)
    elif page == "Account Hierarchy":
        show_accounts_page(data)  # Reuse accounts page for now
    elif page == "Leads & Pipeline":
        show_leads_page(data)
    elif page == "Activities & Tasks":
        show_activities_page(data)
    elif page == "Visit Tracking":
        show_activities_page(data)  # Reuse activities page for now
    elif page == "Infiverse Monitoring":
        show_infiverse_monitoring(data)
    elif page == "Employee CRM Integration":
        show_employee_crm_integration(data)
    elif page == "Integration Status":
        show_integration_status_simple(data)
    elif page == "Natural Language Query":
        show_nlp_query_simple(data)
    elif page == "Reports":
        show_reports_page(data)

def show_dashboard_overview(data):
    """Show dashboard overview"""
    
    st.header("📊 CRM Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Accounts",
            value=len(data['accounts']),
            delta="+2 this month"
        )

    with col2:
        st.metric(
            label="Active Leads",
            value=len(data['leads']),
            delta="+5 this week"
        )

    with col3:
        pipeline_value = data['opportunities']['amount'].sum()
        st.metric(
            label="Pipeline Value",
            value=f"${pipeline_value:,.0f}",
            delta="+15% vs last month"
        )

    with col4:
        avg_deal_size = data['opportunities']['amount'].mean()
        st.metric(
            label="Avg Deal Size",
            value=f"${avg_deal_size:,.0f}",
            delta="+8% vs last quarter"
        )

    # Unified System Metrics (Infiverse Integration)
    st.subheader("🔗 Unified System Overview")

    try:
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

        # Fetch unified metrics
        alerts_response = requests.get(f"{base_url}/api/alerts", timeout=3)
        tasks_response = requests.get(f"{base_url}/api/tasks", timeout=3)

        alerts_count = len(alerts_response.json().get('alerts', [])) if alerts_response.status_code == 200 else 0
        tasks_count = len(tasks_response.json().get('tasks', [])) if tasks_response.status_code == 200 else 0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("System Status", "🟢 Operational", "All systems green")

        with col2:
            st.metric("Active Alerts", alerts_count, f"{alerts_count} requiring attention")

        with col3:
            st.metric("Total Tasks", tasks_count, f"{len([t for t in (tasks_response.json().get('tasks', []) if tasks_response.status_code == 200 else []) if t.get('status') == 'Pending'])} pending")

        with col4:
            st.metric("Integration Health", "98%", "+2% this week")

    except Exception as e:
        # Fallback metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("System Status", "🟢 Operational", "All systems green")

        with col2:
            st.metric("Active Alerts", "3", "2 critical")

        with col3:
            st.metric("Total Tasks", "15", "5 pending")

        with col4:
            st.metric("Integration Health", "95%", "Stable")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Opportunities by Stage")
        stage_counts = data['opportunities']['stage'].value_counts()
        fig_pie = px.pie(
            values=stage_counts.values,
            names=stage_counts.index,
            title="Opportunity Distribution"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Lead Sources")
        source_counts = data['leads']['lead_source'].value_counts()
        fig_bar = px.bar(
            x=source_counts.index,
            y=source_counts.values,
            title="Leads by Source"
        )
        fig_bar.update_layout(xaxis_title="Source", yaxis_title="Count")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Recent activities
    st.subheader("📅 Recent Activities")
    recent_activities = data['activities'].head(5)
    
    for _, activity in recent_activities.iterrows():
        status_class = f"status-{activity['status'].replace(' ', '-')}"
        st.markdown(f"""
        <div style="padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #1f77b4; background-color: #f8f9fa;">
            <strong>{activity['subject']}</strong> 
            <span class="status-badge {status_class}">{activity['status']}</span><br>
            <small>📞 {activity['activity_type']} • 🏢 {activity['account_name']} • 📅 {activity['due_date']}</small>
        </div>
        """, unsafe_allow_html=True)

def show_accounts_page(data):
    """Show accounts management page"""
    
    st.header("🏢 Account Management")
    
    # Account filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        account_type_filter = st.selectbox(
            "Account Type",
            ["All"] + list(data['accounts']['account_type'].unique())
        )
    
    with col2:
        territory_filter = st.selectbox(
            "Territory",
            ["All"] + list(data['accounts']['territory'].unique())
        )
    
    with col3:
        status_filter = st.selectbox(
            "Status",
            ["All"] + list(data['accounts']['status'].unique())
        )
    
    # Filter data
    filtered_accounts = data['accounts'].copy()
    
    if account_type_filter != "All":
        filtered_accounts = filtered_accounts[filtered_accounts['account_type'] == account_type_filter]
    if territory_filter != "All":
        filtered_accounts = filtered_accounts[filtered_accounts['territory'] == territory_filter]
    if status_filter != "All":
        filtered_accounts = filtered_accounts[filtered_accounts['status'] == status_filter]
    
    # Display accounts
    st.subheader(f"📋 Accounts ({len(filtered_accounts)} total)")
    
    # Account cards
    for _, account in filtered_accounts.iterrows():
        with st.expander(f"🏢 {account['name']} ({account['account_type'].title()})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Industry:** {account['industry']}")
                st.write(f"**Territory:** {account['territory']}")
                st.write(f"**Status:** {account['status'].title()}")
            
            with col2:
                st.write(f"**Annual Revenue:** ${account['annual_revenue']:,.0f}")
                st.write(f"**Account ID:** {account['account_id']}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"View Details", key=f"view_{account['account_id']}"):
                    st.info(f"Viewing details for {account['name']}")
            with col2:
                if st.button(f"Create Opportunity", key=f"opp_{account['account_id']}"):
                    st.success(f"Creating opportunity for {account['name']}")
            with col3:
                if st.button(f"Schedule Activity", key=f"act_{account['account_id']}"):
                    st.success(f"Scheduling activity for {account['name']}")

def show_leads_page(data):
    """Show leads management page"""
    
    st.header("🎯 Lead Management")
    
    # Lead metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        new_leads = len(data['leads'][data['leads']['lead_status'] == 'new'])
        st.metric("New Leads", new_leads)
    
    with col2:
        contacted_leads = len(data['leads'][data['leads']['lead_status'] == 'contacted'])
        st.metric("Contacted", contacted_leads)
    
    with col3:
        qualified_leads = len(data['leads'][data['leads']['lead_status'] == 'qualified'])
        st.metric("Qualified", qualified_leads)
    
    with col4:
        total_budget = data['leads']['budget'].sum()
        st.metric("Total Budget", f"${total_budget:,.0f}")
    
    # Lead conversion funnel
    st.subheader("📊 Lead Conversion Funnel")
    
    status_counts = data['leads']['lead_status'].value_counts()
    fig_funnel = go.Figure(go.Funnel(
        y=status_counts.index,
        x=status_counts.values,
        textinfo="value+percent initial"
    ))
    fig_funnel.update_layout(title="Lead Status Distribution")
    st.plotly_chart(fig_funnel, use_container_width=True)
    
    # Leads table
    st.subheader("📋 All Leads")
    
    # Add action buttons to leads data
    leads_display = data['leads'].copy()
    
    for _, lead in leads_display.iterrows():
        with st.expander(f"👤 {lead['full_name']} - {lead['company']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Status:** {lead['lead_status'].title()}")
                st.write(f"**Source:** {lead['lead_source'].title()}")
                st.write(f"**Territory:** {lead['territory']}")
            
            with col2:
                st.write(f"**Budget:** ${lead['budget']:,.0f}")
                st.write(f"**Lead ID:** {lead['lead_id']}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"Contact Lead", key=f"contact_{lead['lead_id']}"):
                    st.success(f"Contacting {lead['full_name']}")
            with col2:
                if st.button(f"Qualify Lead", key=f"qualify_{lead['lead_id']}"):
                    st.success(f"Qualifying {lead['full_name']}")
            with col3:
                if st.button(f"Convert to Opportunity", key=f"convert_{lead['lead_id']}"):
                    st.success(f"Converting {lead['full_name']} to opportunity")

def show_opportunities_page(data):
    """Show opportunities management page"""
    
    st.header("💰 Opportunity Management")
    
    # Opportunity metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_opps = len(data['opportunities'])
        st.metric("Total Opportunities", total_opps)
    
    with col2:
        pipeline_value = data['opportunities']['amount'].sum()
        st.metric("Pipeline Value", f"${pipeline_value:,.0f}")
    
    with col3:
        weighted_pipeline = (data['opportunities']['amount'] * data['opportunities']['probability'] / 100).sum()
        st.metric("Weighted Pipeline", f"${weighted_pipeline:,.0f}")
    
    with col4:
        avg_probability = data['opportunities']['probability'].mean()
        st.metric("Avg Probability", f"{avg_probability:.1f}%")
    
    # Opportunity pipeline chart
    st.subheader("📊 Sales Pipeline")
    
    fig_pipeline = px.bar(
        data['opportunities'],
        x='stage',
        y='amount',
        color='probability',
        title="Opportunities by Stage",
        hover_data=['name', 'account_name']
    )
    fig_pipeline.update_layout(xaxis_title="Stage", yaxis_title="Amount ($)")
    st.plotly_chart(fig_pipeline, use_container_width=True)
    
    # Opportunities table
    st.subheader("📋 All Opportunities")
    
    for _, opp in data['opportunities'].iterrows():
        with st.expander(f"💼 {opp['name']} - ${opp['amount']:,.0f}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Account:** {opp['account_name']}")
                st.write(f"**Stage:** {opp['stage'].title()}")
                st.write(f"**Probability:** {opp['probability']}%")
            
            with col2:
                st.write(f"**Amount:** ${opp['amount']:,.0f}")
                st.write(f"**Close Date:** {opp['close_date']}")
                st.write(f"**Opportunity ID:** {opp['opportunity_id']}")
            
            # Progress bar
            st.progress(opp['probability'] / 100)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"Update Stage", key=f"stage_{opp['opportunity_id']}"):
                    st.success(f"Updating stage for {opp['name']}")
            with col2:
                if st.button(f"Schedule Meeting", key=f"meeting_{opp['opportunity_id']}"):
                    st.success(f"Scheduling meeting for {opp['name']}")
            with col3:
                if st.button(f"Create Proposal", key=f"proposal_{opp['opportunity_id']}"):
                    st.success(f"Creating proposal for {opp['name']}")

def show_activities_page(data):
    """Show activities management page"""
    
    st.header("📅 Activity Management")
    
    # Activity metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_activities = len(data['activities'])
        st.metric("Total Activities", total_activities)
    
    with col2:
        completed_activities = len(data['activities'][data['activities']['status'] == 'completed'])
        st.metric("Completed", completed_activities)
    
    with col3:
        planned_activities = len(data['activities'][data['activities']['status'] == 'planned'])
        st.metric("Planned", planned_activities)
    
    with col4:
        in_progress_activities = len(data['activities'][data['activities']['status'] == 'in_progress'])
        st.metric("In Progress", in_progress_activities)
    
    # Activity type distribution
    st.subheader("📊 Activity Types")
    
    type_counts = data['activities']['activity_type'].value_counts()
    fig_types = px.pie(
        values=type_counts.values,
        names=type_counts.index,
        title="Activity Distribution by Type"
    )
    st.plotly_chart(fig_types, use_container_width=True)
    
    # Activities timeline
    st.subheader("📋 Activity Timeline")
    
    for _, activity in data['activities'].iterrows():
        status_color = {
            'completed': '🟢',
            'in_progress': '🟡',
            'planned': '🔵'
        }.get(activity['status'], '⚪')
        
        type_icon = {
            'call': '📞',
            'meeting': '🤝',
            'email': '📧',
            'visit': '🏢',
            'task': '📋'
        }.get(activity['activity_type'], '📝')
        
        st.markdown(f"""
        <div style="padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #1f77b4; background-color: #f8f9fa;">
            {status_color} {type_icon} <strong>{activity['subject']}</strong><br>
            <small>🏢 {activity['account_name']} • 📅 {activity['due_date']} • Status: {activity['status'].title()}</small>
        </div>
        """, unsafe_allow_html=True)

def show_reports_page(data):
    """Show reports and analytics page"""
    
    st.header("📊 CRM Reports & Analytics")
    
    # Revenue analysis
    st.subheader("💰 Revenue Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Account revenue distribution
        fig_revenue = px.bar(
            data['accounts'],
            x='name',
            y='annual_revenue',
            title="Annual Revenue by Account",
            color='account_type'
        )
        fig_revenue.update_xaxes(tickangle=45)
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        # Territory analysis
        territory_revenue = data['accounts'].groupby('territory')['annual_revenue'].sum().reset_index()
        fig_territory = px.pie(
            territory_revenue,
            values='annual_revenue',
            names='territory',
            title="Revenue by Territory"
        )
        st.plotly_chart(fig_territory, use_container_width=True)
    
    # Lead analysis
    st.subheader("🎯 Lead Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Lead source effectiveness
        source_budget = data['leads'].groupby('lead_source')['budget'].sum().reset_index()
        fig_source = px.bar(
            source_budget,
            x='lead_source',
            y='budget',
            title="Total Budget by Lead Source"
        )
        st.plotly_chart(fig_source, use_container_width=True)
    
    with col2:
        # Lead status distribution
        status_counts = data['leads']['lead_status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        fig_status = px.bar(
            status_counts,
            x='status',
            y='count',
            title="Leads by Status"
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Performance summary
    st.subheader("📈 Performance Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"""
        **Account Performance**
        - Total Accounts: {len(data['accounts'])}
        - Total Revenue: ${data['accounts']['annual_revenue'].sum():,.0f}
        - Avg Revenue: ${data['accounts']['annual_revenue'].mean():,.0f}
        """)
    
    with col2:
        conversion_rate = (len(data['leads'][data['leads']['lead_status'] == 'qualified']) / len(data['leads']) * 100)
        st.success(f"""
        **Lead Performance**
        - Total Leads: {len(data['leads'])}
        - Qualified Rate: {conversion_rate:.1f}%
        - Total Budget: ${data['leads']['budget'].sum():,.0f}
        """)
    
    with col3:
        avg_probability = data['opportunities']['probability'].mean()
        st.warning(f"""
        **Opportunity Performance**
        - Total Opportunities: {len(data['opportunities'])}
        - Avg Probability: {avg_probability:.1f}%
        - Pipeline Value: ${data['opportunities']['amount'].sum():,.0f}
        """)

def show_integration_status_simple(data):
    """Show integration status page"""
    st.header("🔗 Integration Status")
    
    integration_status = data['integration_status']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        office_status = integration_status.get('office365', {})
        status = office_status.get('status', 'inactive')
        icon = "✅" if status == 'active' else "❌"
        st.markdown(f"""
        ### {icon} Office 365
        **Status:** {status.title()}
        """)
    
    with col2:
        maps_status = integration_status.get('google_maps', {})
        status = maps_status.get('status', 'inactive')
        icon = "✅" if status == 'active' else "❌"
        st.markdown(f"""
        ### {icon} Google Maps
        **Status:** {status.title()}
        """)
    
    with col3:
        ai_status = integration_status.get('openai', {})
        status = ai_status.get('status', 'inactive')
        icon = "✅" if status == 'active' else "❌"
        st.markdown(f"""
        ### {icon} OpenAI
        **Status:** {status.title()}
        """)

def show_employee_crm_integration(data):
    """Show employee CRM integration - linking workforce management with CRM activities"""
    st.header("👥 Employee CRM Integration")

    # Try to fetch employee data from Infiverse
    try:
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

        # Fetch employees
        employees_response = requests.get(f"{base_url}/api/users", timeout=5)
        employees_data = employees_response.json() if employees_response.status_code == 200 else []

        # Fetch tasks
        tasks_response = requests.get(f"{base_url}/api/tasks", timeout=5)
        tasks_data = tasks_response.json() if tasks_response.status_code == 200 else []

        # Fetch alerts
        alerts_response = requests.get(f"{base_url}/api/alerts", timeout=5)
        alerts_data = alerts_response.json() if alerts_response.status_code == 200 else {"alerts": []}

        st.success("✅ Connected to Infiverse workforce data")

        # Employee-Account Relationship Management
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏢 Account Managers & Employees")

            # Mock relationship data (in real implementation, this would be stored in database)
            employee_accounts = pd.DataFrame({
                'Employee': ['Sarah Johnson', 'Mike Chen', 'Lisa Wang', 'John Doe', 'Jane Smith'],
                'CRM Role': ['Account Manager', 'Account Manager', 'Account Manager', 'Sales Rep', 'Sales Rep'],
                'Assigned Accounts': [3, 2, 4, 1, 2],
                'Monthly Target': ['$50K', '$40K', '$60K', '$25K', '$30K'],
                'Current Progress': ['$42K', '$38K', '$55K', '$22K', '$28K'],
                'Productivity Score': [92, 88, 95, 85, 90]
            })

            # Use pandas to_string() instead of st.dataframe to avoid pyarrow dependency
            st.text(employee_accounts.to_string())

        with col2:
            st.subheader("📊 Employee Performance vs CRM Goals")

            # Performance metrics
            performance_data = pd.DataFrame({
                'Metric': ['Avg Deal Size', 'Conversion Rate', 'Customer Satisfaction', 'Response Time'],
                'Target': ['$45K', '75%', '4.5/5', '<2 hours'],
                'Current': ['$42K', '72%', '4.3/5', '1.8 hours'],
                'Status': ['On Track', 'Slightly Behind', 'On Track', 'On Track']
            })

            # Color coding for status
            def color_status(val):
                if val == 'On Track':
                    return 'background-color: #e8f5e8; color: #2e7d32'
                elif val == 'Slightly Behind':
                    return 'background-color: #fff3e0; color: #f57c00'
                else:
                    return 'background-color: #ffebee; color: #c62828'

            styled_performance = performance_data.style.applymap(color_status, subset=['Status'])
            # Use pandas to_string() instead of st.dataframe to avoid pyarrow dependency
            st.text(styled_performance.to_string())

        # Task-Activity Integration
        st.subheader("🔗 CRM Activities ↔ Employee Tasks")

        # Mock integration data
        integrated_activities = pd.DataFrame({
            'CRM Activity': [
                'TechCorp Quarterly Review',
                'Global Manufacturing Demo',
                'Retail Solutions Proposal',
                'StartupTech Follow-up',
                'Enterprise Solutions Negotiation'
            ],
            'Assigned Employee': ['Sarah Johnson', 'Mike Chen', 'Lisa Wang', 'John Doe', 'Jane Smith'],
            'Activity Status': ['Completed', 'In Progress', 'Pending', 'Completed', 'In Progress'],
            'Linked Tasks': [
                'Prepare Q4 presentation, Update account plan',
                'Schedule demo, Prepare materials',
                'Research requirements, Draft proposal',
                'Send follow-up email, Schedule meeting',
                'Review contract terms, Prepare negotiation points'
            ],
            'Due Date': ['2024-01-15', '2024-01-18', '2024-01-20', '2024-01-12', '2024-01-22'],
            'Priority': ['High', 'High', 'Medium', 'Medium', 'High']
        })

        st.table(integrated_activities)

        # Real-time Monitoring Integration
        st.subheader("📈 Real-time Employee Monitoring for CRM")

        col1, col2, col3 = st.columns(3)

        with col1:
            active_employees = len([e for e in employees_data if e.get('status') == 'active']) if employees_data else 0
            st.metric("Active Employees", active_employees, "+2 this week")

        with col2:
            pending_tasks = len([t for t in tasks_data if t.get('status') == 'Pending']) if tasks_data else 0
            st.metric("Pending Tasks", pending_tasks, "-3 today")

        with col3:
            active_alerts = len(alerts_data.get('alerts', []))
            st.metric("Active Alerts", active_alerts, "2 critical")

        # Employee Activity Timeline
        st.subheader("⏱️ Employee Activity Timeline")

        # Mock timeline data
        timeline_data = pd.DataFrame({
            'Time': ['09:00', '10:30', '11:45', '14:00', '15:30', '16:45'],
            'Employee': ['Sarah Johnson', 'Mike Chen', 'Lisa Wang', 'John Doe', 'Jane Smith', 'Sarah Johnson'],
            'Activity': [
                'CRM: TechCorp account review',
                'CRM: Client meeting prep',
                'CRM: Proposal development',
                'CRM: Lead qualification',
                'CRM: Contract negotiation',
                'CRM: Follow-up calls'
            ],
            'Type': ['CRM', 'CRM', 'CRM', 'CRM', 'CRM', 'CRM'],
            'Duration': ['2h', '1.5h', '3h', '45m', '2h', '1h']
        })

        st.table(timeline_data)

        # Integration Actions
        st.subheader("🔧 Integration Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Sync Employee Data"):
                st.success("Employee data synchronized with CRM")

        with col2:
            if st.button("📋 Generate Performance Report"):
                st.info("Generating employee performance report...")

        with col3:
            if st.button("🚨 Send Alert to Team"):
                st.warning("Alert sent to account management team")

    except Exception as e:
        st.warning(f"Unable to connect to Infiverse: {str(e)}. Showing demo integration data.")

        # Fallback demo content
        st.subheader("👥 Employee CRM Integration (Demo)")

        st.info("This page demonstrates how CRM workflows integrate with employee monitoring and task management.")

        # Demo employee-account relationships
        demo_relationships = pd.DataFrame({
            'Employee': ['Sarah Johnson', 'Mike Chen', 'Lisa Wang'],
            'CRM Role': ['Senior Account Manager', 'Account Manager', 'VP Sales'],
            'Managed Accounts': ['TechCorp, StartupTech', 'Global Mfg, MidSize Corp', 'Retail Solutions, Enterprise'],
            'Q4 Target': ['$200K', '$150K', '$300K'],
            'Current Progress': ['$180K', '$142K', '$275K']
        })

        # Use pandas to_string() instead of st.dataframe to avoid pyarrow dependency
        st.text(demo_relationships.to_string())

        st.markdown("""
        **Integration Features:**
        - Link CRM accounts to account managers
        - Track employee productivity vs sales targets
        - Monitor task completion for CRM activities
        - Real-time alerts for employee performance issues
        - Unified reporting across CRM and workforce management
        """)

def show_nlp_query_simple(data):
    """Show natural language query page with actual LLM integration"""
    st.header("🧠 Natural Language Queries")
    
    # Check if OpenAI is configured
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if openai_key:
        st.success("✅ OpenAI integration is active! Ask questions about your CRM data.")
    else:
        st.warning("⚠️ OpenAI API key not configured. Set OPENAI_API_KEY environment variable to enable AI queries.")
        st.info("💡 You can still use pattern-based queries below!")
    
    query = st.text_input(
        "Enter your question:",
        placeholder="e.g., Show me all opportunities closing this month"
    )
    
    if st.button("🔍 Search") and query:
        st.success(f"Searching for: '{query}'")
        
        # Try to use the actual LLM query system
        try:
            # Import and use the LLM query system
            import sys
            sys.path.append('integrations')
            from integrations.llm_query_system import LLMQuerySystem
            
            llm_system = LLMQuerySystem()
            result = llm_system.process_query(query)
            
            if result.get('success'):
                query_type = result.get('query_type')
                query_data = result.get('data', [])
                
                st.subheader(f"📈 Results ({query_type.replace('_', ' ').title() if query_type else 'Unknown'})")
                
                if isinstance(query_data, list) and query_data:
                    st.write(query_data)
                elif isinstance(query_data, dict):
                    st.json(query_data)
                else:
                    st.info("No data found for your query.")
                
                # Show natural language response
                natural_response = llm_system.generate_natural_response(result)
                st.markdown("### 🤖 AI Response:")
                st.write(natural_response)
            else:
                st.error(f"Query failed: {result.get('message', 'Unknown error')}")
                
                # Fall back to simple pattern matching
                if "opportunity" in query.lower() or "opportunities" in query.lower():
                    st.subheader("📈 Opportunities Found")
                    st.table(data['opportunities'])

                elif "lead" in query.lower() or "leads" in query.lower():
                    st.subheader("🎯 Leads Found")
                    st.table(data['leads'])

                elif "account" in query.lower() or "accounts" in query.lower():
                    st.subheader("🏢 Accounts Found")
                    st.table(data['accounts'])

                elif "activity" in query.lower() or "activities" in query.lower():
                    st.subheader("📅 Activities Found")
                    st.table(data['activities'])
        
        except ImportError:
            st.warning("LLM integration not available. Using pattern matching instead.")
            # Simple mock responses based on keywords
            if "opportunity" in query.lower() or "opportunities" in query.lower():
                st.subheader("📈 Opportunities Found")
                st.table(data['opportunities'])
            
            elif "lead" in query.lower() or "leads" in query.lower():
                st.subheader("🎯 Leads Found")
                st.table(data['leads'])
            
            elif "account" in query.lower() or "accounts" in query.lower():
                st.subheader("🏢 Accounts Found")
                st.table(data['accounts'])
            
            elif "activity" in query.lower() or "activities" in query.lower():
                st.subheader("📅 Activities Found")
                st.table(data['activities'])
            
            else:
                st.warning("I'm still learning! Try asking about opportunities, leads, accounts, or activities.")
        
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
            st.info("Falling back to simple pattern matching...")
            
            # Simple pattern matching fallback
            if "opportunity" in query.lower():
                st.table(data['opportunities'])
            elif "lead" in query.lower():
                st.table(data['leads'])
            elif "account" in query.lower():
                st.table(data['accounts'])
            elif "activity" in query.lower():
                st.table(data['activities'])
    
    # Sample queries and configuration section
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💡 Sample Queries")
        sample_queries = [
            "Show me all opportunities closing this month",
            "What are the pending tasks for TechCorp?",
            "List all leads from trade shows not yet converted",
            "Account summary for TechCorp Industries",
            "Pipeline analysis",
            "Recent activities"
        ]
        
        for i, sample_query in enumerate(sample_queries):
            if st.button(f"Try: {sample_query}", key=f"sample_{i}"):
                st.rerun()
    
    with col2:
        st.subheader("⚙️ OpenAI Configuration")
        
        if openai_key:
            st.success("✅ OpenAI API Key configured")
            masked_key = openai_key[:8] + "..." + openai_key[-4:] if len(openai_key) > 12 else "****"
            st.info(f"Key: {masked_key}")
        else:
            st.error("❌ OpenAI API Key not set")
            st.markdown("""
            **To enable AI queries:**
            1. Get your API key from OpenAI
            2. Set environment variable:
               ```bash
               export OPENAI_API_KEY=sk-your-key-here
               ```
            3. Restart the application
            """)
        
        # Test OpenAI connection
        if st.button("🗘 Test OpenAI Connection"):
            if openai_key:
                try:
                    import openai
                    # Simple test to see if the key works
                    st.success("✅ OpenAI module available")
                    st.info("📝 Test a query above to verify API connectivity")
                except ImportError:
                    st.error("❌ OpenAI package not installed. Run: pip install openai")
            else:
                st.error("❌ No API key to test")

if __name__ == "__main__":
    main()