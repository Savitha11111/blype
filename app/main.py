# app/main.py

import streamlit as st
import pandas as pd
from app.utils import parse_uploaded_file
from app.jira import (
    get_authorization_url,
    exchange_code_for_token,
    get_cloud_id,
    create_jira_issue,
)

st.set_page_config(page_title="Kanban Task Uploader", layout="wide")
st.title("📋 Kanban Task Uploader")
st.markdown(
    "Upload a `.csv` or `.xlsx` file with your tasks. Map columns and preview your board before pushing to Jira."
)

uploaded_file = st.file_uploader("📂 Upload File", type=["csv", "xlsx"])

if uploaded_file:
    df = parse_uploaded_file(uploaded_file)
    if df is not None:
        st.success("✅ File uploaded and parsed successfully!")
        st.write("### 📄 Preview:")
        st.dataframe(df.head())

        title_col = st.selectbox("📝 Select column for Task Title", df.columns)
        desc_col = st.selectbox("🗒 Select column for Task Description", df.columns)

        st.markdown("---")
        st.write("### 🧾 Sample Tasks:")
        for i in range(min(5, len(df))):
            st.markdown(f"**{i+1}. {df[title_col][i]}**")
            st.caption(df[desc_col][i])

        # Jira login logic
        if "jira_token" not in st.session_state:
            if st.button("🔐 Login with Jira"):
                st.markdown(
                    f"[Click here to authorize Jira]({get_authorization_url()})"
                )
        else:
            st.success("✅ Logged in to Jira")

        # Handle callback
        query_params = st.experimental_get_query_params()
        if "code" in query_params and "jira_token" not in st.session_state:
            try:
                code = query_params["code"][0]
                token_data = exchange_code_for_token(code)
                st.session_state["jira_token"] = token_data["access_token"]
                st.session_state["cloud_id"] = get_cloud_id(token_data["access_token"])
                st.success("✅ Authorization successful!")
            except Exception as e:
                st.error(f"❌ OAuth failed: {e}")

        # Task creation button
        if "jira_token" in st.session_state:
            project_key = st.text_input("📌 Enter Jira Project Key", value="KAN")
            if st.button("🚀 Create Tasks in Jira"):
                with st.spinner("Creating tasks..."):
                    try:
                        token = st.session_state["jira_token"]
                        cloud_id = st.session_state["cloud_id"]
                        for _, row in df.iterrows():
                            summary = str(row[title_col])
                            description = str(row[desc_col])
                            create_jira_issue(
                                token, cloud_id, project_key, summary, description
                            )
                        st.success("✅ All tasks created successfully!")
                    except Exception as e:
                        st.error(f"❌ Error creating tasks: {e}")
    else:
        st.error("❌ Failed to parse file. Please upload a valid CSV or Excel file.")
