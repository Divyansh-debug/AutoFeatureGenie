import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(page_title="AutoFeatureGenie - Upload CSV", layout="centered")
st.markdown("<h1 style='text-align: center;'>🧠 AutoFeatureGenie - Upload CSV</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload your dataset (CSV)", type=["csv"])

if uploaded_file is not None:
    st.success("File selected!")
    st.write(f"📄 {uploaded_file.name} ({round(uploaded_file.size/1e6, 2)}MB)")

    if st.button("Upload to backend"):
        st.session_state["feature_error"] = None  # Reset old errors
        with st.spinner("Uploading and analyzing..."):
            try:
                res = requests.post(
                    "http://localhost:8000/upload/",
                    files={"file": uploaded_file},
                    timeout=30  # Add 30 second timeout
                )
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure it's running on http://localhost:8000")
                st.stop()
            except requests.exceptions.Timeout:
                st.error("❌ Upload timed out. Try with a smaller file.")
                st.stop()
            except Exception as e:
                st.error(f"❌ Upload error: {str(e)}")
                st.stop()

        if res.status_code == 200:
            data = res.json()
            st.session_state["uploaded"] = True
            st.session_state["filename"] = data["filename"]
            st.session_state["eda"] = data["eda_summary"]
        else:
            st.error(f"❌ Upload failed. Status: {res.status_code}")
            st.code(f"Response: {res.text}")

if st.session_state.get("uploaded", False):
    eda = st.session_state["eda"]
    st.success(f"Uploaded: {st.session_state['filename']} ({eda['shape'][0]} rows)")

    st.subheader("📊 EDA Summary")
    st.write(f"**Shape:** {eda['shape']}")
    st.write(f"**Columns:** {', '.join(eda['columns'])}")
    st.write(f"**Likely Target Column:** `{eda['likely_target_column']}`")

    st.subheader("🧾 Column-wise Info")
    for col, info in eda["column_info"].items():
        with st.expander(col):
            st.json(info)

    if st.button("Get Feature Suggestions"):
        with st.spinner("Thinking of features..."):
            res = requests.get(
                "http://localhost:8000/feature-suggestions/",
                params={"filename": st.session_state['filename']}
            )

        if res.status_code == 200:
            suggestions = res.json()["suggestions"]
            st.session_state["feature_error"] = None

            st.subheader("🧠 Feature Engineering Suggestions")
            if suggestions and "error" in suggestions[0]:
                st.error(f"❌ GEMINI Error: {suggestions[0]['error']}")
                # Handle both error response formats
                if "details" in suggestions[0]:
                    st.code(suggestions[0]["details"])
                elif "raw_output" in suggestions[0]:
                    st.code(suggestions[0]["raw_output"])
                else:
                    st.code(str(suggestions[0]))
            else:
                for s in suggestions:
                    col_name = s.get("column", "⚠️ Unknown Column or Error")
                    with st.expander(col_name):
                        st.json(s)
        else:
            st.session_state["feature_error"] = f"Status: {res.status_code}\nDetails: {res.text}"

if st.session_state.get("feature_error"):
    st.error("❌ Failed to fetch feature suggestions.")
    st.code(st.session_state["feature_error"])
