import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

st.set_page_config(
    page_title="HR-AI Dashboard Pro", 
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.metric-card {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 5px solid #667eea;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin: 0.5rem 0;
}
.success-card {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #00d4aa;
}
.warning-card {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #ff9500;
}
.sidebar-metric {
    background: #f8f9fa;
    padding: 0.5rem;
    border-radius: 5px;
    margin: 0.25rem 0;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

API_BASE = "http://localhost:5000"

def make_api_request(method, endpoint, data=None):
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

# Enhanced Header
st.markdown('''
<div class="main-header">
    <h1>🚀 HR-AI System Dashboard Pro</h1>
    <p>Next-Generation AI-Powered Recruitment & Analytics Platform</p>
    <p>Real-time • Intelligent • Automated</p>
</div>
''', unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    st.markdown("### 🎛️ Control Center")
    
    # Real-time status
    health_data, _ = make_api_request("GET", "/health")
    if health_data:
        st.markdown('<div class="success-card">🟢 System Online</div>', unsafe_allow_html=True)
        
        # Performance metrics in sidebar
        perf = health_data.get('performance', {})
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="sidebar-metric">CPU<br><b>{perf.get("cpu_percent", 0):.1f}%</b></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="sidebar-metric">Memory<br><b>{perf.get("memory_percent", 0):.1f}%</b></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="warning-card">🔴 System Offline</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation with icons
    pages = {
        "🏠 Dashboard": "dashboard",
        "👥 Candidates": "candidates", 
        "💬 Feedback": "feedback",
        "⚡ Automation": "automation",
        "📊 Analytics": "analytics",
        "🤖 AI Features": "ai_features",
        "🔧 System": "system"
    }
    
    selected_page = st.selectbox("Navigate to:", list(pages.keys()))
    page = pages[selected_page]
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    if st.button("📊 Update Scores"):
        update_data, _ = make_api_request("POST", "/smart/bulk-score-update")
        if update_data:
            st.success(f"✅ Updated {update_data.get('updated', 0)} scores")
    
    # Auto-refresh
    auto_refresh = st.checkbox("🔄 Auto Refresh (30s)")
    if auto_refresh:
        st.rerun()

# Main Content
if page == "dashboard":
    # Enhanced Dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    # Get data
    candidates_data, _ = make_api_request("GET", "/candidate/list")
    feedback_data, _ = make_api_request("GET", "/feedback/logs")
    analytics_data, _ = make_api_request("GET", "/analytics/dashboard")
    
    # Enhanced metrics
    with col1:
        total_candidates = len(candidates_data) if candidates_data else 0
        st.markdown(f'''
        <div class="metric-card">
            <h3>👥 Candidates</h3>
            <h2>{total_candidates}</h2>
            <p>Total registered</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        avg_score = analytics_data.get('avg_match_score', 0) if analytics_data else 0
        st.markdown(f'''
        <div class="metric-card">
            <h3>🎯 Avg Score</h3>
            <h2>{avg_score:.1f}%</h2>
            <p>Match accuracy</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        total_feedback = len(feedback_data) if feedback_data else 0
        st.markdown(f'''
        <div class="metric-card">
            <h3>💬 Feedback</h3>
            <h2>{total_feedback}</h2>
            <p>Total reviews</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        if health_data:
            response_time = health_data.get('performance', {}).get('response_time_ms', 0)
            st.markdown(f'''
            <div class="metric-card">
                <h3>⚡ Response</h3>
                <h2>{response_time:.0f}ms</h2>
                <p>API speed</p>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Enhanced charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Candidate Pipeline")
        if candidates_data:
            scores = [c.get('match_score', 0) for c in candidates_data]
            fig = px.histogram(
                x=scores, 
                nbins=15, 
                title="Score Distribution",
                color_discrete_sequence=['#667eea']
            )
            fig.update_layout(
                height=350,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Success Metrics")
        if feedback_data:
            df = pd.DataFrame(feedback_data)
            if 'outcome' in df.columns:
                outcome_counts = df['outcome'].value_counts()
                fig = px.pie(
                    values=outcome_counts.values, 
                    names=outcome_counts.index,
                    title="Hiring Outcomes",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

elif page == "candidates":
    st.markdown("## 👥 Candidate Management")
    
    # Add candidate form
    with st.expander("➕ Add New Candidate", expanded=False):
        with st.form("add_candidate"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("👤 Name")
                email = st.text_input("📧 Email")
            with col2:
                phone = st.text_input("📱 Phone (+91-XXXXXXXXXX)")
                skills = st.text_area("💼 Skills (comma-separated)")
            
            if st.form_submit_button("🚀 Add Candidate", use_container_width=True):
                if name and email and phone and skills:
                    candidate_data = {
                        "name": name,
                        "email": email, 
                        "phone": phone,
                        "skills": [s.strip() for s in skills.split(",")]
                    }
                    result, error = make_api_request("POST", "/candidate/add", candidate_data)
                    if result:
                        st.success(f"✅ Candidate added! ID: {result['candidate_id']}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {error}")
    
    # Enhanced candidate list
    candidates_data, error = make_api_request("GET", "/candidate/list")
    if candidates_data:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("🔍 Search candidates")
        with col2:
            min_score = st.slider("📊 Min Score", 0, 100, 0)
        with col3:
            all_skills = list(set(skill for c in candidates_data for skill in c.get('skills', [])))
            skill_filter = st.selectbox("💼 Skill Filter", ["All"] + all_skills)
        
        # Apply filters
        df = pd.DataFrame(candidates_data)
        if search:
            mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
            df = df[mask]
        
        if 'match_score' in df.columns:
            df = df[df['match_score'] >= min_score]
        
        if skill_filter != "All":
            df = df[df['skills'].apply(lambda x: skill_filter in x if isinstance(x, list) else False)]
        
        # Display results
        st.markdown(f"### 📋 Results ({len(df)} candidates)")
        if len(df) > 0:
            # Enhanced table display
            for _, candidate in df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**👤 {candidate.get('name', 'N/A')}**")
                        st.markdown(f"📧 {candidate.get('email', 'N/A')}")
                    
                    with col2:
                        skills = candidate.get('skills', [])
                        if isinstance(skills, list):
                            st.markdown(f"💼 {', '.join(skills[:3])}")
                        st.markdown(f"📱 {candidate.get('phone', 'N/A')}")
                    
                    with col3:
                        score = candidate.get('match_score', 0)
                        color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
                        st.markdown(f"{color} **{score:.1f}%**")
                    
                    with col4:
                        if st.button(f"👁️ View", key=f"view_{candidate.get('id')}"):
                            st.info(f"Candidate ID: {candidate.get('id')}")
                    
                    st.markdown("---")
        else:
            st.info("🔍 No candidates match your filters")

elif page == "ai_features":
    st.markdown("## 🤖 AI-Powered Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 AI Recommendations")
        candidate_id = st.number_input("Candidate ID", min_value=1, step=1)
        
        if st.button("🧠 Get AI Insights", use_container_width=True):
            rec_data, error = make_api_request("GET", f"/smart/recommendations/{candidate_id}")
            if rec_data:
                st.success("🎯 AI Analysis Complete!")
                recommendations = rec_data.get('recommendations', [])
                for i, rec in enumerate(recommendations, 1):
                    st.markdown(f"**{i}.** {rec}")
            else:
                st.error(f"❌ {error}")
    
    with col2:
        st.markdown("### 📊 Bulk Operations")
        
        if st.button("🔄 Update All Scores", use_container_width=True):
            with st.spinner("🤖 AI processing..."):
                update_data, error = make_api_request("POST", "/smart/bulk-score-update")
                if update_data:
                    updated = update_data.get('updated', 0)
                    st.success(f"✅ Updated {updated} candidates")
                    if updated > 0:
                        st.balloons()
                else:
                    st.error(f"❌ {error}")
    
    # AI Analytics
    st.markdown("### 📈 AI Analytics")
    
    predictions_data, _ = make_api_request("GET", "/analytics/predictions")
    if predictions_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔮 Hiring Forecast:**")
            forecast = predictions_data.get('hiring_forecast', 'No data')
            st.info(forecast)
        
        with col2:
            st.markdown("**📊 Success Predictions:**")
            success_prob = predictions_data.get('success_probability', {})
            for cid, data in list(success_prob.items())[:3]:
                name = data.get('name', f'Candidate {cid}')
                prob = data.get('probability', 0)
                st.markdown(f"• **{name}**: {prob}% match")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🚀 HR-AI System Pro v3.0**")
with col2:
    st.markdown(f"**🕐 Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
with col3:
    if health_data:
        st.markdown("**✅ All Systems Operational**")
    else:
        st.markdown("**⚠️ System Check Required**")