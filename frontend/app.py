"""Streamlit frontend for AutoFeatureGenie"""
import streamlit as st
import pandas as pd
import requests
import json
import time

# Page configuration
st.set_page_config(
    page_title="AutoFeatureGenie - Upload CSV",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>🧠 AutoFeatureGenie - Upload CSV</h1>", unsafe_allow_html=True)

# Sidebar for connection testing and info
with st.sidebar:
    st.subheader("🔧 Connection Status")
    
    if st.button("Test Backend Connection"):
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                st.success("✅ Backend is running!")
                st.info(f"Version: {data.get('version', 'Unknown')}")
                if data.get('uptime'):
                    st.info(f"Uptime: {data['uptime']:.1f}s")
            else:
                st.error(f"❌ Backend error: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend")
            st.info("💡 Make sure backend is running:\n`uvicorn backend.main:app --reload`")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    st.subheader("ℹ️ About")
    st.info("""
    **AutoFeatureGenie** helps you:
    - Analyze your datasets
    - Get AI-powered feature suggestions
    - Improve your ML models
    """)

# Domain selection
domain = st.selectbox(
    "Select your domain",
    ["telecom", "finance", "healthcare", "ecommerce", "general"],
    help="Domain context helps generate better feature suggestions"
)

# File uploader
uploaded_file = st.file_uploader(
    "Upload your dataset (CSV)",
    type=["csv"],
    help="Maximum file size: 100MB"
)

if uploaded_file is not None:
    file_size_mb = round(uploaded_file.size / 1e6, 2)
    
    # File size validation
    max_size_mb = 100
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        st.error(f"❌ File too large! Maximum size is {max_size_mb}MB. Your file is {file_size_mb}MB")
        st.stop()
    
    st.success("✅ File selected!")
    st.write(f"📄 **{uploaded_file.name}** ({file_size_mb}MB)")
    
    if st.button("Upload to backend", type="primary"):
        st.session_state["feature_error"] = None
        
        # Progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔄 Connecting to backend...")
            progress_bar.progress(10)
            time.sleep(0.3)
            
            status_text.text("📤 Uploading file...")
            progress_bar.progress(30)
            
            # Upload file
            res = requests.post(
                "http://localhost:8000/upload/",
                files={"file": uploaded_file},
                timeout=60  # Increased timeout for large files
            )
            
            progress_bar.progress(60)
            status_text.text("🔍 Analyzing data...")
            
            if res.status_code == 200:
                data = res.json()
                st.session_state["uploaded"] = True
                st.session_state["filename"] = data["filename"]
                st.session_state["eda"] = data["eda_summary"]
                st.session_state["domain"] = domain
                
                progress_bar.progress(100)
                status_text.text("✅ Upload successful!")
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
                st.success(f"✅ File uploaded successfully! ({data['rows']} rows)")
                st.rerun()
            elif res.status_code == 413:
                progress_bar.empty()
                status_text.empty()
                st.error("❌ File too large! Maximum size is 100MB")
            elif res.status_code == 400:
                progress_bar.empty()
                status_text.empty()
                try:
                    error_data = res.json()
                    st.error(f"❌ Invalid file: {error_data.get('detail', 'Unknown error')}")
                except:
                    st.error(f"❌ Invalid file: {res.text}")
            else:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Upload failed. Status: {res.status_code}")
                try:
                    error_data = res.json()
                    st.code(json.dumps(error_data, indent=2))
                except:
                    st.code(res.text)
                    
        except requests.exceptions.ConnectionError:
            progress_bar.empty()
            status_text.empty()
            st.error("❌ Cannot connect to backend")
            st.info("💡 To start the backend, run:\n```bash\nuvicorn backend.main:app --reload\n```")
        except requests.exceptions.Timeout:
            progress_bar.empty()
            status_text.empty()
            st.error("❌ Upload timed out. The file might be too large or the backend is slow.")
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Upload error: {str(e)}")

# Display EDA results
if st.session_state.get("uploaded", False):
    eda = st.session_state["eda"]
    filename = st.session_state["filename"]
    
    st.divider()
    st.success(f"📊 **{filename}** - {eda['shape'][0]} rows × {eda['shape'][1]} columns")
    
    # EDA Summary Section
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", eda['shape'][0])
    with col2:
        st.metric("Columns", eda['shape'][1])
    with col3:
        target_col = eda.get('likely_target_column', 'None')
        st.metric("Target Column", target_col if target_col else "None")
    
    st.subheader("📊 Column Information")
    
    # Column info in expandable sections
    for col, info in eda["column_info"].items():
        with st.expander(f"📋 {col} ({info['dtype']})"):
            col_info_col1, col_info_col2 = st.columns(2)
            with col_info_col1:
                st.write(f"**Data Type:** {info['dtype']}")
                st.write(f"**Missing Values:** {info['missing_values']}")
                st.write(f"**Unique Values:** {info['unique_values']}")
            with col_info_col2:
                if 'mean' in info:
                    st.write(f"**Mean:** {info['mean']:.2f}")
                    st.write(f"**Std:** {info['std']:.2f}")
                    st.write(f"**Min:** {info['min']:.2f}")
                    st.write(f"**Max:** {info['max']:.2f}")
    
    st.divider()
    
    # Feature Suggestions Section
    if st.button("🧠 Get Feature Suggestions", type="primary"):
        with st.spinner("🤔 AI is thinking of creative features..."):
            try:
                res = requests.get(
                    "http://localhost:8000/feature-suggestions/",
                    params={
                        "filename": filename,
                        "domain": st.session_state["domain"]
                    },
                    timeout=120  # Longer timeout for AI processing
                )
                
                if res.status_code == 200:
                    data = res.json()
                    suggestions = data["suggestions"]
                    st.session_state["feature_error"] = None
                    st.session_state["suggestions"] = suggestions
                    
                    if data.get("processing_time"):
                        st.info(f"⏱️ Generated in {data['processing_time']:.2f} seconds")
                    
                    st.subheader("🧠 Feature Engineering Suggestions")
                    
                    if suggestions and isinstance(suggestions, list) and len(suggestions) > 0:
                        first_suggestion = suggestions[0]
                        # Check if it's an error response
                        if isinstance(first_suggestion, dict) and ("error" in first_suggestion or "details" in first_suggestion):
                            error_msg = first_suggestion.get("error")
                            # Handle None or empty error messages
                            if not error_msg or error_msg is None:
                                error_msg = "Unknown error occurred"
                            
                            st.error(f"❌ Error: {error_msg}")
                            
                            # Show error details if available
                            if first_suggestion.get("details"):
                                with st.expander("Error Details"):
                                    st.code(first_suggestion["details"])
                            elif first_suggestion.get("raw_output"):
                                with st.expander("Raw Output"):
                                    st.code(first_suggestion["raw_output"])
                            elif first_suggestion.get("raw"):
                                with st.expander("Raw Response"):
                                    st.code(first_suggestion["raw"])
                        # Check if it's a valid suggestion (has required fields)
                        elif isinstance(first_suggestion, dict) and first_suggestion.get("column") and first_suggestion.get("idea"):
                            st.success(f"✨ Generated {len(suggestions)} feature suggestions!")
                            
                            for idx, s in enumerate(suggestions, 1):
                                with st.expander(f"💡 {idx}. {s.get('column', 'Feature')}"):
                                    st.write(f"**Idea:** {s.get('idea', 'N/A')}")
                                    st.write(f"**Reason:** {s.get('reason', 'N/A')}")
                                    
                                    if s.get('code_snippet'):
                                        st.write("**Code:**")
                                        st.code(s.get('code_snippet'), language='python')
                                    
                                    if s.get('expected_impact'):
                                        st.info(f"**Expected Impact:** {s['expected_impact']}")
                                    
                                    if s.get('complexity'):
                                        complexity_color = {
                                            'low': '🟢',
                                            'medium': '🟡',
                                            'high': '🔴'
                                        }.get(s['complexity'].lower(), '⚪')
                                        st.write(f"**Complexity:** {complexity_color} {s['complexity']}")
                elif res.status_code == 404:
                    st.error("❌ File not found. Please upload again.")
                else:
                    st.error(f"❌ Failed to fetch suggestions. Status: {res.status_code}")
                    try:
                        error_data = res.json()
                        st.code(json.dumps(error_data, indent=2))
                    except:
                        st.code(res.text)
                        
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend")
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out. The AI processing is taking longer than expected.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Display cached suggestions if available
    if st.session_state.get("suggestions"):
        suggestions = st.session_state["suggestions"]
        if suggestions and not (isinstance(suggestions, list) and len(suggestions) > 0 and "error" in suggestions[0]):
            st.divider()
            st.subheader("💾 Cached Suggestions")
            st.info("Click 'Get Feature Suggestions' again to regenerate")

# Display any persistent errors
if st.session_state.get("feature_error"):
    st.error("❌ Failed to fetch feature suggestions.")
    st.code(st.session_state["feature_error"])
