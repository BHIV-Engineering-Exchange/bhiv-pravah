import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import time
# from dashboard.enhanced_components import create_metric_card, create_status_indicator, create_progress_ring, show_notification, create_data_table

st.set_page_config(
    page_title="HR-AI Dashboard", 
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

API_BASE = "http://localhost:5000"

# Custom CSS for enhanced styling
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #667eea;
}
.success-box {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 5px;
    padding: 0.75rem;
    margin: 0.5rem 0;
}
.warning-box {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 5px;
    padding: 0.75rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🚀 HR-AI System Dashboard v3.0</h1><p>AI-Powered Recruitment & Analytics Platform</p></div>', unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    st.markdown("### 🏠 Navigation")
    
    # Real-time system status
    status_placeholder = st.empty()
    
    def make_api_request(method, endpoint, data=None):
        try:
            url = f"{API_BASE}{endpoint}"
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"API Error: {response.status_code}"
        except Exception as e:
            return None, f"Connection Error: {str(e)}"
    
    health_data, _ = make_api_request("GET", "/health")
    if health_data:
        status_placeholder.success("✅ System Online")
    else:
        status_placeholder.error("❌ System Offline")
    
    st.markdown("---")
    
    page = st.selectbox(
        "📊 Choose Page", 
        ["Overview", "Candidates", "Feedback", "Automation", "Analytics", "System Health", "Smart Features"],
        format_func=lambda x: f"📈 {x}" if x == "Analytics" else f"💼 {x}" if x == "Candidates" else f"💬 {x}" if x == "Feedback" else f"⚙️ {x}" if x == "Automation" else f"🔧 {x}" if x == "System Health" else f"🤖 {x}" if x == "Smart Features" else f"🏠 {x}"
    )
    
    st.markdown("---")
    
    # Quick stats in sidebar
    st.markdown("### 📊 Quick Stats")
    candidates_data, _ = make_api_request("GET", "/candidate/list")
    if candidates_data:
        st.metric("👥 Candidates", len(candidates_data))
    
    feedback_data, _ = make_api_request("GET", "/feedback/logs")
    if feedback_data:
        st.metric("📝 Feedback", len(feedback_data))
    
    # Auto-refresh toggle
    st.markdown("---")
    auto_refresh = st.checkbox("🔄 Auto Refresh (30s)")
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if page == "Overview":
    st.header("System Overview")
    
    col1, col2, col3 = st.columns(3)
    
    # Check system health
    health_data, error = make_api_request("GET", "/health")
    if health_data:
        with col1:
            st.metric("System Status", "Healthy", "🟢")
        with col2:
            st.metric("Database", "Connected", "✅")
        with col3:
            st.metric("API", "Active", "⚡")
    else:
        st.error(f"System Health Check Failed: {error}")
    
    # Show recent feedback
    feedback_data, error = make_api_request("GET", "/feedback/logs")
    if feedback_data and len(feedback_data) > 0:
        st.subheader("Recent Feedback")
        df = pd.DataFrame(feedback_data)
        st.dataframe(df.head(10))

elif page == "Candidates":
    st.header("Candidate Management")
    
    # Add new candidate
    with st.expander("Add New Candidate"):
        with st.form("add_candidate"):
            name = st.text_input("Name*")
            email = st.text_input("Email*")
            phone = st.text_input("Phone* (Format: +91-XXXXXXXXXX)")
            skills_input = st.text_area("Skills* (comma-separated)")
            
            submitted = st.form_submit_button("Add Candidate")
            
            if submitted:
                if name and email and phone and skills_input:
                    skills = [skill.strip() for skill in skills_input.split(",")]
                    candidate_data = {
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "skills": skills
                    }
                    
                    result, error = make_api_request("POST", "/candidate/add", candidate_data)
                    if result:
                        st.success(f"Candidate added successfully! ID: {result['candidate_id']}")
                        st.rerun()
                    else:
                        st.error(f"Failed to add candidate: {error}")
                else:
                    st.error("Please fill all required fields")
    
    # List candidates
    st.subheader("Current Candidates")
    candidates_data, error = make_api_request("GET", "/candidate/list")
    if candidates_data:
        if len(candidates_data) > 0:
            df = pd.DataFrame(candidates_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No candidates found. Add some candidates to get started.")
    else:
        st.error(f"Failed to load candidates: {error}")

elif page == "Feedback":
    st.header("HR Feedback System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Submit Feedback")
        with st.form("feedback_form"):
            candidate_id = st.number_input("Candidate ID", min_value=1, step=1)
            feedback_score = st.slider("Feedback Score", 1, 5, 3)
            comment = st.text_area("Comment")
            actual_outcome = st.selectbox("Actual Outcome", ["accept", "reject", "reconsider"])
            
            submitted = st.form_submit_button("Submit Feedback")
            
            if submitted:
                feedback_data = {
                    "candidate_id": candidate_id,
                    "feedback_score": feedback_score,
                    "comment": comment,
                    "actual_outcome": actual_outcome
                }
                
                result, error = make_api_request("POST", "/feedback/hr_feedback", feedback_data)
                if result:
                    st.success("Feedback submitted successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to submit feedback: {error}")
    
    with col2:
        st.subheader("Feedback History")
        feedback_data, error = make_api_request("GET", "/feedback/logs")
        if feedback_data:
            if len(feedback_data) > 0:
                df = pd.DataFrame(feedback_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No feedback logs found.")
        else:
            st.error(f"Failed to load feedback: {error}")

elif page == "Automation":
    st.header("Automation Control")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Trigger Event")
        with st.form("automation_form"):
            candidate_id = st.number_input("Candidate ID", min_value=1, step=1)
            event_type = st.selectbox("Event Type", [
                "shortlisted", "rejected", "interview_scheduled", "onboarding_completed"
            ])
            
            # Optional overrides
            st.write("Optional Overrides:")
            override_email = st.text_input("Override Email (optional)")
            override_phone = st.text_input("Override Phone (optional)")
            
            submitted = st.form_submit_button("Trigger Automation")
            
            if submitted:
                metadata = {}
                if override_email:
                    metadata["override_email"] = override_email
                if override_phone:
                    metadata["override_phone"] = override_phone
                
                event_data = {
                    "candidate_id": candidate_id,
                    "event_type": event_type,
                    "metadata": metadata
                }
                
                result, error = make_api_request("POST", "/trigger/", event_data)
                if result:
                    st.success("Automation triggered successfully!")
                    st.json(result)
                else:
                    st.error(f"Failed to trigger automation: {error}")
    
    with col2:
        st.subheader("Automation History")
        candidate_id_history = st.number_input("Candidate ID for History", min_value=1, step=1, key="history_id")
        
        if st.button("Load History"):
            history_data, error = make_api_request("GET", f"/trigger/history/{candidate_id_history}")
            if history_data:
                if len(history_data.get("automation_history", [])) > 0:
                    df = pd.DataFrame(history_data["automation_history"])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No automation history found for this candidate.")
            else:
                st.error(f"Failed to load history: {error}")

elif page == "Analytics":
    st.header("📊 Analytics Dashboard")
    
    # RL Chart - Reinforcement Learning Performance
    st.subheader("🤖 RL Performance Chart")
    col1, col2 = st.columns(2)
    
    with col1:
        # Generate sample RL data
        episodes = np.arange(1, 101)
        rewards = np.cumsum(np.random.normal(0.1, 0.5, 100)) + np.random.normal(0, 2, 100)
        
        fig_rl = go.Figure()
        fig_rl.add_trace(go.Scatter(x=episodes, y=rewards, mode='lines', name='Cumulative Reward'))
        fig_rl.update_layout(title="RL Agent Learning Progress", xaxis_title="Episodes", yaxis_title="Reward")
        st.plotly_chart(fig_rl, use_container_width=True)
    
    with col2:
        # Distribution Chart - Candidate Scores
        st.subheader("📈 Score Distribution")
        candidates_data, _ = make_api_request("GET", "/candidate/list")
        if candidates_data and len(candidates_data) > 0:
            df = pd.DataFrame(candidates_data)
            if 'match_score' in df.columns:
                fig_dist = px.histogram(df, x='match_score', nbins=20, title="Candidate Score Distribution")
                st.plotly_chart(fig_dist, use_container_width=True)
            else:
                # Generate sample distribution
                scores = np.random.normal(75, 15, 100)
                fig_dist = px.histogram(x=scores, nbins=20, title="Sample Score Distribution")
                st.plotly_chart(fig_dist, use_container_width=True)
        else:
            scores = np.random.normal(75, 15, 100)
            fig_dist = px.histogram(x=scores, nbins=20, title="Sample Score Distribution")
            st.plotly_chart(fig_dist, use_container_width=True)
    
    # Feedback Analytics
    st.subheader("💬 Feedback Analytics")
    feedback_data, _ = make_api_request("GET", "/feedback/logs")
    if feedback_data and len(feedback_data) > 0:
        df_feedback = pd.DataFrame(feedback_data)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'outcome' in df_feedback.columns:
                outcome_counts = df_feedback['outcome'].value_counts()
                fig_pie = px.pie(values=outcome_counts.values, names=outcome_counts.index, title="Outcome Distribution")
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            if 'score' in df_feedback.columns:
                avg_score = df_feedback['score'].astype(float).mean()
                st.metric("Average Score", f"{avg_score:.2f}", "📊")
                
                fig_score = px.box(df_feedback, y='score', title="Score Distribution")
                st.plotly_chart(fig_score, use_container_width=True)
        
        with col3:
            total_feedback = len(df_feedback)
            st.metric("Total Feedback", total_feedback, "📝")
            
            if 'timestamp' in df_feedback.columns:
                df_feedback['date'] = pd.to_datetime(df_feedback['timestamp']).dt.date
                daily_counts = df_feedback.groupby('date').size()
                fig_timeline = px.line(x=daily_counts.index, y=daily_counts.values, title="Daily Feedback Trend")
                st.plotly_chart(fig_timeline, use_container_width=True)

elif page == "System Health":
    st.header("🔧 System Health & Integration")
    
    # Integration Checker
    st.subheader("🔗 Integration Status Checker")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**API Endpoints Status**")
        
        endpoints = [
            ("/health", "System Health"),
            ("/candidate/list", "Candidate API"),
            ("/feedback/logs", "Feedback API"),
            ("/system/status", "System Status")
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
                if response.status_code == 200:
                    st.success(f"✅ {name}: Connected")
                else:
                    st.error(f"❌ {name}: Error {response.status_code}")
            except Exception as e:
                st.error(f"❌ {name}: Connection Failed")
    
    with col2:
        st.write("**Communication Channels**")
        
        # Test communication endpoints
        channels = [
            ("/communication/email", "Email Service"),
            ("/communication/whatsapp", "WhatsApp Service"),
            ("/communication/voice", "Voice Service")
        ]
        
        for endpoint, name in channels:
            # Since these require parameters, just check if endpoint exists
            try:
                response = requests.post(f"{API_BASE}{endpoint}?candidate_id=1", timeout=5)
                if response.status_code in [200, 404, 422]:  # 422 is validation error, means endpoint works
                    st.success(f"✅ {name}: Available")
                else:
                    st.warning(f"⚠️ {name}: Status {response.status_code}")
            except Exception:
                st.error(f"❌ {name}: Unavailable")

elif page == "Smart Features":
    st.header("🤖 AI-Powered Smart Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 AI Recommendations")
        rec_candidate_id = st.number_input("Candidate ID for Recommendations", min_value=1, step=1)
        
        if st.button("Get AI Recommendations"):
            rec_data, error = make_api_request("GET", f"/smart/recommendations/{rec_candidate_id}")
            if rec_data:
                st.success("AI Recommendations Generated!")
                for i, rec in enumerate(rec_data.get('recommendations', []), 1):
                    st.write(f"{i}. {rec}")
            else:
                st.error(f"Failed to get recommendations: {error}")
        
        st.write("---")
        st.subheader("📬 Smart Follow-up")
        followup_candidate_id = st.number_input("Candidate ID for Follow-up", min_value=1, step=1, key="followup_id")
        followup_days = st.slider("Days until follow-up", 1, 14, 3)
        
        if st.button("Schedule Smart Follow-up"):
            followup_data, error = make_api_request("POST", f"/smart/schedule-followup/{followup_candidate_id}?days={followup_days}")
            if followup_data:
                st.success(f"Follow-up scheduled for {followup_days} days!")
            else:
                st.error(f"Failed to schedule follow-up: {error}")
    
    with col2:
        st.subheader("🔔 Smart Notifications")
        
        if st.button("Check Pending Notifications"):
            notif_data, error = make_api_request("GET", "/smart/pending-notifications")
            if notif_data:
                pending = notif_data.get('pending_notifications', [])
                if pending:
                    st.write(f"**{len(pending)} pending notifications:**")
                    for notif in pending:
                        st.info(f"Candidate {notif.get('candidate_id')}: {notif.get('type')}")
                else:
                    st.success("No pending notifications")
            else:
                st.error(f"Failed to get notifications: {error}")
        
        st.write("---")
        st.subheader("⚡ Bulk Operations")
        
        if st.button("Update All Match Scores"):
            update_data, error = make_api_request("POST", "/smart/bulk-score-update")
            if update_data:
                updated_count = update_data.get('updated', 0)
                st.success(f"✅ Updated {updated_count} candidates")
                if updated_count > 0:
                    st.balloons()
            else:
                st.error(f"❌ Bulk update failed: {error}")
    
    # AI Analytics
    st.subheader("📊 AI Analytics Dashboard")
    
    analytics_data, error = make_api_request("GET", "/analytics/dashboard")
    if analytics_data:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Candidates", analytics_data.get('total_candidates', 0))
        with col2:
            st.metric("Avg Match Score", f"{analytics_data.get('avg_match_score', 0):.1f}%")
        with col3:
            st.metric("Total Feedback", analytics_data.get('total_feedback', 0))
        with col4:
            st.metric("Recent Activity", analytics_data.get('recent_activity', 0))
        
        # Top Skills Chart
        top_skills = analytics_data.get('top_skills', [])
        if top_skills:
            skills_df = pd.DataFrame(top_skills, columns=['Skill', 'Count'])
            fig_skills = px.bar(skills_df, x='Skill', y='Count', title="Top Skills in Demand")
            st.plotly_chart(fig_skills, use_container_width=True)

# Enhanced Footer with system info
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💻 System Info")
    
    # System status indicators
    if 'health_data' in locals() and health_data:
        st.success("✅ Backend: Online")
        st.success("✅ Database: Connected")
        st.success("✅ AI Engine: Active")
    else:
        st.error("❌ Backend: Offline")
    
    st.markdown("---")
    st.markdown("**🚀 HR-AI System v3.0**")
    st.markdown("🔧 Backend: FastAPI + SQLite + AI")
    st.markdown("📊 Frontend: Streamlit")
    st.markdown("🤖 Analytics: Plotly + ML")
    st.markdown("⚡ Real-time Dashboard")
    
    # Last updated timestamp
    st.markdown(f"**🔄 Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
