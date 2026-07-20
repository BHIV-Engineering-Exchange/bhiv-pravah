import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

def create_metric_card(title, value, delta=None, icon="📊"):
    """Create enhanced metric card with styling"""
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown(f"<div style='font-size: 2rem; text-align: center;'>{icon}</div>", unsafe_allow_html=True)
    with col2:
        st.metric(title, value, delta)

def create_status_indicator(status, label):
    """Create status indicator with color coding"""
    color = "🟢" if status else "🔴"
    st.markdown(f"{color} **{label}**: {'Online' if status else 'Offline'}")

def create_progress_ring(value, max_value, label):
    """Create circular progress indicator"""
    percentage = (value / max_value) * 100 if max_value > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = percentage,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': label},
        delta = {'reference': 80},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}}))
    
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_timeline_chart(data):
    """Create interactive timeline chart"""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    fig = px.timeline(df, x_start="start", x_end="end", y="task", color="status")
    fig.update_layout(height=300)
    return fig

def create_heatmap(data, title="Activity Heatmap"):
    """Create activity heatmap"""
    if not data:
        return None
    
    fig = px.imshow(data, title=title, color_continuous_scale='viridis')
    fig.update_layout(height=300)
    return fig

def show_notification(message, type="info"):
    """Show styled notification"""
    if type == "success":
        st.success(f"✅ {message}")
    elif type == "warning":
        st.warning(f"⚠️ {message}")
    elif type == "error":
        st.error(f"❌ {message}")
    else:
        st.info(f"ℹ️ {message}")

def create_data_table(data, title="Data Table"):
    """Create enhanced data table with search and filters"""
    if not data:
        st.info("No data available")
        return
    
    df = pd.DataFrame(data)
    
    # Add search functionality
    search_term = st.text_input(f"🔍 Search {title}")
    if search_term:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        df = df[mask]
    
    # Display table with styling
    st.dataframe(
        df,
        use_container_width=True,
        height=400
    )
    
    return df