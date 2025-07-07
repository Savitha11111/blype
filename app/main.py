# main.py

import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from utils import parse_uploaded_file
from jira import (
    get_authorization_url, exchange_code_for_token,
    get_cloud_id, get_all_projects, create_jira_issue
)

load_dotenv()

# Streamlit UI setup
st.set_page_config(page_title="📘 Jira Task Manager", layout="wide")
st.title("📘 Jira Task Manager & Uploader")

query_params = st.query_params

# --- OAuth Handling ---
if "jira_token" not in st.session_state:
    if "code" in query_params:
        try:
            code = query_params["code"]
            token_data = exchange_code_for_token(code)
            access_token = token_data["access_token"]
            cloud_id = get_cloud_id(access_token)

            st.session_state["jira_token"] = access_token
            st.session_state["cloud_id"] = cloud_id

            # Remove code from URL to avoid future errors
            st.query_params.clear()

            st.success("✅ Authorized successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ OAuth failed: {e}")
            st.stop()

# --- Require Auth ---
if "jira_token" not in st.session_state:
    st.warning("🔐 Please log in with Jira to continue.")
    st.markdown(f"[🔑 Click here to authorize Jira]({get_authorization_url()})", unsafe_allow_html=True)
    st.stop()

# --- Token and Cloud ID ---
token = st.session_state["jira_token"]
cloud_id = st.session_state["cloud_id"]

# --- Logout and Refresh ---
with st.sidebar:
    st.markdown("## Settings")
    if st.button("🔓 Logout"):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

    if st.button("🔄 Refresh"):
        st.rerun()

# --- Project Loading ---
try:
    projects = get_all_projects(token, cloud_id)
    if not projects:
        st.warning("No Jira projects found.")
        st.stop()
except Exception as e:
    st.error(f"❌ Failed to load projects: {e}")
    st.stop()

project_map = {f"{p['name']} ({p['key']})": p["key"] for p in projects}
selected_project = st.selectbox("📁 Select a Project", list(project_map.keys()))
project_key = project_map[selected_project]

# --- Task Input Tabs ---
st.subheader("📝 Add New Tasks")

tab1, tab2 = st.tabs(["📁 Upload File", "✍️ Paste Tasks"])

# --- Tab 1: Upload ---
with tab1:
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if uploaded_file:
        df = parse_uploaded_file(uploaded_file)
        if df is not None:
            st.success("✅ File parsed successfully!")
            st.dataframe(df)

            title_col = st.selectbox("Task Title Column", df.columns)
            desc_col = st.selectbox("Task Description Column", df.columns)
            extra_cols = [col for col in df.columns if col not in [title_col, desc_col]]

            if st.button("🚀 Create Tasks from File"):
                with st.spinner("Creating tasks..."):
                    for _, row in df.iterrows():
                        title = str(row[title_col])
                        desc = str(row[desc_col])
                        if extra_cols:
                            desc += "\n\n" + "\n".join([f"**{col}:** {row[col]}" for col in extra_cols])
                        create_jira_issue(token, cloud_id, project_key, title, desc)
                    st.success("🎉 Tasks created!")

# --- Tab 2: Paste ---
with tab2:
    pasted = st.text_area("Paste tasks (Format: Task, Description)", height=200,
                          placeholder="Fix bug, Adjust logic for login\nWrite tests, Add tests for edge cases")

    if pasted:
        try:
            rows = [line.split(",", 1) for line in pasted.strip().splitlines() if "," in line]
            df_manual = pd.DataFrame(rows, columns=["Task", "Description"])
            st.dataframe(df_manual)

            if st.button("🚀 Create Pasted Tasks"):
                with st.spinner("Creating tasks..."):
                    for _, row in df_manual.iterrows():
                        create_jira_issue(token, cloud_id, project_key, row["Task"], row["Description"])
                    st.success("✅ Tasks from pasted input created!")
        except Exception as e:
            st.error(f"❌ Failed to parse pasted tasks: {e}")
