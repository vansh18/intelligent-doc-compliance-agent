import streamlit as st
import os
from typing import List, Dict, Any
import json
from datetime import datetime
import time
import base64

from ingestion.document_loader import process_multiple_documents
from compliance.rule_generator import ComplianceRuleGenerator
from compliance.compliance_agent import ComplianceAgent
from reports.report_generator import ComplianceReportGenerator

st.set_page_config(
    page_title="Document Compliance Checker",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .status-box {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border-left: 5px solid #4CAF50;
    }
    .error-box {
        border-left: 5px solid #f44336;
    }
    .processing-box {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border-left: 5px solid #2563eb;
    }
    .rule-box {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border-left: 5px solid #9c27b0;
    }
    </style>
    """, unsafe_allow_html=True)

def save_uploaded_files(uploaded_files: List[Any]) -> List[str]:
    """Save uploaded files to a temporary directory and return their paths."""
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    file_paths = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_paths.append(file_path)
    
    return file_paths

def cleanup_temp_files(file_paths: List[str]):
    """Clean up temporary uploaded files."""
    for path in file_paths:
        try:
            os.remove(path)
        except:
            pass

def main():
    st.title("📄 Document Compliance Checker")
    
    if 'processed_docs' not in st.session_state:
        st.session_state.processed_docs = None
    if 'rules' not in st.session_state:
        st.session_state.rules = []
    if 'validation_results' not in st.session_state:
        st.session_state.validation_results = None
    
    st.markdown("### 1. Upload Documents")
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload your documents (PDF, JPG, PNG)",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("Process Documents"):
                with st.spinner("Processing documents..."):

                    file_paths = save_uploaded_files(uploaded_files)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        st.session_state.processed_docs = process_multiple_documents(file_paths)

                        progress_bar.progress(100)
                        status_text.markdown(
                            f'<div class="status-box">✅ Successfully processed {len(st.session_state.processed_docs)} documents</div>',
                            unsafe_allow_html=True
                        )
                        
                    except Exception as e:
                        status_text.markdown(
                            f'<div class="status-box error-box">❌ Error processing documents: {str(e)}</div>',
                            unsafe_allow_html=True
                        )
                    finally:
                        cleanup_temp_files(file_paths)
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 2. Define Compliance Rules")
    with st.container():
        st.markdown('<div class="rule-section">', unsafe_allow_html=True)

        rule_text = st.text_area(
            "Enter your compliance rule in natural language",
            height=100,
            placeholder="Example: Total amount should not exceed 10000 USD"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if rule_text and st.button("Add Rule"):
                with st.spinner("Generating compliance rule..."):
                    try:
                        rule_generator = ComplianceRuleGenerator()
                        rule = rule_generator.generate_rule(rule_text)
                        st.session_state.rules.append(rule)
                        
                        st.markdown(
                            f'<div class="status-box">✅ Rule added successfully</div>',
                            unsafe_allow_html=True
                        )
                        
                    except Exception as e:
                        st.markdown(
                            f'<div class="status-box error-box">❌ Error generating rule: {str(e)}</div>',
                            unsafe_allow_html=True
                        )
        
        with col2:
            if st.session_state.rules and st.button("Clear All Rules"):
                try:
                    rule_generator = ComplianceRuleGenerator()
                    rule_generator.clear_rules()
                    st.session_state.rules = []
                    st.markdown(
                        f'<div class="status-box">✅ All rules cleared</div>',
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.markdown(
                        f'<div class="status-box error-box">❌ Error clearing rules: {str(e)}</div>',
                        unsafe_allow_html=True
                    )

        if st.session_state.rules:
            st.markdown("### Added Rules")
            for i, rule in enumerate(st.session_state.rules, 1):
                with st.expander(f"Rule {i}: {rule['name']}"):
                    st.markdown(f"**Description:** {rule['description']}")
                    st.markdown(f"**Category:** {rule['category']}")
                    st.markdown(f"**Field:** {rule['field']}")
                    st.markdown(f"**Severity:** {rule['severity']}")
                    st.markdown(f"**Applicable Documents:** {', '.join(rule['applicable_documents'])}")

                    if st.button(f"Delete Rule {i}", key=f"delete_{i}"):
                        try:
                            rule_generator = ComplianceRuleGenerator()
                            rule_generator.clear_rules() 
                            st.session_state.rules.pop(i-1) 
                          
                            for remaining_rule in st.session_state.rules:
                                rule_generator.generate_rule(json.dumps(remaining_rule))
                            st.experimental_rerun()
                        except Exception as e:
                            st.markdown(
                                f'<div class="status-box error-box">❌ Error deleting rule: {str(e)}</div>',
                                unsafe_allow_html=True
                            )
        
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.processed_docs and st.session_state.rules:
        st.markdown("### 3. Run Compliance Check")
        if st.button("Validate Documents"):
            with st.spinner("Running compliance validation..."):
                try:
                    compliance_agent = ComplianceAgent()
                    st.session_state.validation_results = compliance_agent.validate_documents(
                        st.session_state.processed_docs
                    )
                    
                    st.markdown(
                        f'<div class="status-box">✅ Validation completed successfully</div>',
                        unsafe_allow_html=True
                    )
                    
                except Exception as e:
                    st.markdown(
                        f'<div class="status-box error-box">❌ Error during validation: {str(e)}</div>',
                        unsafe_allow_html=True
                    )
    if st.session_state.validation_results:
        st.markdown("### 4. Generate Report")
        if st.button("Generate Report"):
            with st.spinner("Generating compliance report..."):
                try:
                    reports_dir = os.path.join(os.getcwd(), "reports")
                    os.makedirs(reports_dir, exist_ok=True)
                    report_generator = ComplianceReportGenerator()
                    report_html = report_generator.generate_report(st.session_state.validation_results)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    report_path = os.path.join(reports_dir, f"compliance_report_{timestamp}.html")
                    
                    with open(report_path, "w", encoding="utf-8") as f:
                        f.write(report_html)
                    
                    st.markdown(
                        f'<div class="status-box">✅ Report generated successfully</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown("### Report Preview")
                    st.markdown(
                        f'<iframe src="data:text/html;base64,{base64.b64encode(report_html.encode()).decode()}" width="100%" height="800" style="border: none;"></iframe>',
                        unsafe_allow_html=True
                    )
                    
                    with open(report_path, "rb") as f:
                        st.download_button(
                            "Download Report",
                            f,
                            file_name=os.path.basename(report_path),
                            mime="text/html"
                        )
                    
                except Exception as e:
                    st.markdown(
                        f'<div class="status-box error-box">❌ Error generating report: {str(e)}</div>',
                        unsafe_allow_html=True
                    )

if __name__ == "__main__":
    main()
