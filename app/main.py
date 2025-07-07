# app/main.py

import streamlit as st
import pandas as pd
from app.utils import parse_uploaded_file

st.set_page_config(page_title="Kanban Task Uploader", layout="wide")

st.title("📋 Kanban Task Uploader")
st.markdown("Upload a `.csv` or `.xlsx` file with your tasks. Map columns and preview your board before pushing to Jira.")

uploaded_file = st.file_uploader("📂 Upload File", type=["csv", "xlsx"])

if uploaded_file:
    df = parse_uploaded_file(uploaded_file)
    if df is not None:
        st.success("File uploaded and parsed successfully!")
        st.write("### Preview:")
        st.dataframe(df.head())

        title_col = st.selectbox("📝 Select the column to use as Task Title", df.columns)
        desc_col = st.selectbox("🗒 Select the column to use as Description", df.columns)

        st.markdown("---")
        st.write("### 🧾 Sample Tasks:")

        for i in range(min(5, len(df))):
            st.markdown(f"**{i+1}. {df[title_col][i]}**")
            st.caption(df[desc_col][i])
    else:
        st.error("Failed to parse file. Please upload a valid CSV or Excel file.")
