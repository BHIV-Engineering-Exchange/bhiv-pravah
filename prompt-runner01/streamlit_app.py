"""
Prompt Runner — Streamlit UI
=============================
Frontend for the Groq-powered Prompt Runner API (port 8001).

Run:
    streamlit run streamlit_app.py
"""

import json

import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8001"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Prompt Runner",
    page_icon="⚡",
    layout="centered",
)

st.title("⚡ Prompt Runner")
st.caption("Converts any prompt into a structured JSON instruction via Groq API.")

# ---------------------------------------------------------------------------
# Sidebar — health / models
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("API Status")
    try:
        h = requests.get(f"{API_BASE}/health", timeout=3).json()
        if h.get("groq_available"):
            st.success("Groq API — connected")
        else:
            st.error("Groq API — key not configured")
        models = h.get("models", [])
        if models:
            st.markdown("**Available models:**")
            for m in models:
                st.markdown(f"- `{m}`")
    except requests.exceptions.ConnectionError:
        st.error("API server not reachable.\nStart it with:\n```\nuvicorn api:app --port 8001\n```")
    except Exception as e:
        st.warning(f"Health check failed: {e}")

# ---------------------------------------------------------------------------
# Main input
# ---------------------------------------------------------------------------

prompt = st.text_area(
    "Enter your prompt",
    placeholder="e.g. Create a workflow to manage early stage diabetes patients",
    height=120,
)

model_override = st.text_input(
    "Model override (optional)",
    placeholder="Leave blank for default (llama-3.3-70b-versatile)",
)

generate = st.button("Generate Instruction", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Generate & display
# ---------------------------------------------------------------------------

if generate:
    if not prompt.strip():
        st.warning("Please enter a prompt.")
        st.stop()

    payload: dict = {"prompt": prompt.strip()}
    if model_override.strip():
        payload["model"] = model_override.strip()

    with st.spinner("Calling Groq API…"):
        try:
            resp = requests.post(
                f"{API_BASE}/generate",
                json=payload,
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()

                st.success("Instruction generated")
                st.divider()

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Module", data.get("module", "—"))
                    st.metric("Intent", data.get("intent", "—"))
                with col2:
                    st.metric("Topic", data.get("topic", "—"))
                    st.metric("Output Format", data.get("output_format", "—"))

                st.markdown("#### Tasks")
                tasks = data.get("tasks", [])
                for i, task in enumerate(tasks, 1):
                    st.markdown(f"{i}. `{task}`")

                st.divider()
                st.markdown("#### Raw JSON")
                st.code(json.dumps(data, indent=2), language="json")

            elif resp.status_code == 503:
                st.error("GROQ_API_KEY is not configured on the server. Set it as an environment variable and restart the API.")
            else:
                st.error(f"API error {resp.status_code}: {resp.text}")

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot reach the API server at `http://127.0.0.1:8001`.\n\n"
                "Start it first:\n```\nuvicorn api:app --host 127.0.0.1 --port 8001\n```"
            )
        except Exception as e:
            st.error(f"Unexpected error: {e}")
