import os
import streamlit as st
import requests
import json
from typing import Dict, List

# Load API URL from environment or default
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Session steps
START, RESEARCH, CLARIFY, GENERATE, MODIFY = "start", "research", "clarify", "generate", "modify"

st.set_page_config(
    page_title="Enhanced Interactive Learning Assistant", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = START
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "report" not in st.session_state:
    st.session_state.report = ""
if "documents" not in st.session_state:
    st.session_state.documents = []

# Sidebar navigation
st.sidebar.title("Learning Assistant")
st.sidebar.markdown("---")

if "session_id" in st.session_state:
    st.sidebar.success(f"Session: {st.session_state.session_id}")

# Allow navigation between steps when applicable
current_step = st.session_state.step
if current_step != START:
    step_names = {
        RESEARCH: "1. Research",
        CLARIFY: "2. Clarification",
        GENERATE: "3. Report",
        MODIFY: "4. Customization"
    }
    
    if "documents" in st.session_state and st.session_state.documents:
        if st.sidebar.button("← Back to Research", key="nav_research"):
            st.session_state.step = RESEARCH
            st.rerun()
    
    if "report" in st.session_state and st.session_state.report:
        if st.sidebar.button("View Report", key="nav_report"):
            st.session_state.step = GENERATE
            st.rerun()

# Show topic in sidebar when available
if "topic" in st.session_state:
    st.sidebar.markdown(f"**Topic:** {st.session_state.topic}")

# START: Topic & Objectives
if st.session_state.step == START:
    st.title("Welcome to the Enhanced Interactive Learning Assistant")
    st.markdown("""
    This assistant helps you learn about any topic through:
    
    1. **Comprehensive Research** across web content, academic papers, and videos
    2. **Personalized Content** tailored to your knowledge level and learning style
    3. **Interactive Learning Experience** with customizable reports
    
    Let's get started with your learning journey!
    """)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        raw_topic = st.text_input("What would you like to learn about?", key="raw_topic", 
                              placeholder="Enter a topic (e.g., 'Machine Learning', 'Quantum Physics')")
        
        raw_objectives = st.text_area("What are your learning objectives?", key="raw_objectives",
                                 placeholder="Enter objectives, separated by commas (e.g., 'Understand basic concepts, Learn practical applications')")
        
        if st.button("Start Research", type="primary"):
            if not raw_topic:
                st.warning("Please enter a topic to begin.")
            else:
                with st.spinner("Researching your topic..."):
                    st.session_state.topic = raw_topic.strip()
                    st.session_state.objectives = [o.strip() for o in raw_objectives.split(',') if o.strip()]
                    
                    if not st.session_state.objectives:
                        st.session_state.objectives = ["Understand basic concepts", "Learn practical applications"]
                    
                    payload = {"topic": st.session_state.topic, "objectives": st.session_state.objectives}
                    try:
                        resp = requests.post(f"{API_URL}/research", json=payload)
                        resp.raise_for_status()
                        research_data = resp.json()
                        
                        if research_data:
                            st.session_state.session_id = research_data.get("session_id")
                            st.session_state.documents = research_data.get("documents", [])
                            st.session_state.step = CLARIFY
                            st.session_state.answers = {"topic": st.session_state.topic}
                            st.rerun()
                    except Exception as e:
                        st.error(f"API call failed: {str(e)}")
                        research_data = {}
    
    with col2:
        st.markdown("""
        ### Example Topics
        - Machine Learning Algorithms
        - Renewable Energy Technologies
        - Blockchain and Cryptocurrencies
        - Modern Art Movements
        - Quantum Computing
        - Climate Change Mitigation
        - Ancient Civilizations
        """)

# RESEARCH: Show research results
elif st.session_state.step == RESEARCH:
    st.title(f"Research Results: {st.session_state.topic}")
    
    if not st.session_state.documents:
        st.warning("No research results found. Please try a different topic.")
        if st.button("Start Over"):
            st.session_state.step = START
            st.rerun()
    else:
        st.markdown(f"We found **{len(st.session_state.documents)}** relevant sources on '{st.session_state.topic}'.")
        
        web_docs = [d for d in st.session_state.documents if d.get("type") == "web"]
        arxiv_docs = [d for d in st.session_state.documents if d.get("type") == "arxiv"]
        video_docs = [d for d in st.session_state.documents if d.get("type") == "video"]
        
        tabs = st.tabs(["Web Content", "Academic Papers", "Video Transcripts"])
        
        with tabs[0]:
            if web_docs:
                for i, doc in enumerate(web_docs):
                    with st.expander(f"Source {i+1}: {doc['source'][:50]}..."):
                        st.markdown(doc['text'][:300] + "..." if len(doc['text']) > 300 else doc['text'])
            else:
                st.info("No web content found.")
        
        with tabs[1]:
            if arxiv_docs:
                for i, doc in enumerate(arxiv_docs):
                    with st.expander(f"Paper {i+1}: {doc['source']}"):
                        st.markdown(doc['text'][:300] + "..." if len(doc['text']) > 300 else doc['text'])
            else:
                st.info("No academic papers found.")
        
        with tabs[2]:
            if video_docs:
                for i, doc in enumerate(video_docs):
                    with st.expander(f"Video {i+1}: {doc['source']}"):
                        st.markdown(doc['text'][:300] + "..." if len(doc['text']) > 300 else doc['text'])
            else:
                st.info("No video transcripts found.")
        
        if st.button("Continue to Personalization", type="primary"):
            st.session_state.step = CLARIFY
            st.rerun()

# CLARIFY: Ask follow-up questions
elif st.session_state.step == CLARIFY:
    st.title(f"Personalize Your Learning: {st.session_state.topic}")
    
    st.markdown("""
    To tailor your learning experience, please answer a few questions about your preferences and background.
    This will help us create a report that matches your learning style and needs.
    """)
    
    with st.expander("Preview Research Sources", expanded=False):
        if not st.session_state.documents:
            st.info("No research snippets found. Make sure the research step returned results.")
        else:
            for i, doc in enumerate(st.session_state.documents[:3]):
                st.markdown(f"- **Source {i+1}**: {doc['source'][:50]}...")
    
    try:
        resp = requests.post(f"{API_URL}/clarify", json={"answers": {"topic": st.session_state.topic}})
        resp.raise_for_status()
        resp_data = resp.json()
        questions = resp_data.get("questions", [])
    except Exception as e:
        st.error(f"API call failed: {str(e)}")
        questions = []
    
    with st.form("personalization_form"):
        if "answers" not in st.session_state:
            st.session_state.answers = {"topic": st.session_state.topic}
        
        for q in questions:
            if "options" in q:
                st.session_state.answers[q["id"]] = st.selectbox(
                    q["question"], 
                    options=q["options"], 
                    key=f"select_{q['id']}")
            else:
                st.session_state.answers[q["id"]] = st.text_input(
                    q["question"], 
                    key=f"text_{q['id']}")
        
        submitted = st.form_submit_button("Generate My Learning Report", type="primary")
        
        if submitted:
            payload = {
                "answers": st.session_state.answers,
                "session_id": st.session_state.session_id
            }
            
            with st.spinner("Analyzing preferences..."):
                try:
                    resp = requests.post(f"{API_URL}/analyze_preferences", json=payload)
                    resp.raise_for_status()
                    prefs = resp.json()
                    st.session_state.preferences = prefs.get("preferences", {})
                except Exception as e:
                    st.error(f"API call failed: {str(e)}")
                    st.session_state.preferences = {}
            
            with st.spinner("Generating your personalized report..."):
                report_payload = {
                    "session_id": st.session_state.session_id,
                    "preferences": {
                        **st.session_state.answers,
                        **st.session_state.preferences
                    }
                }
                try:
                    resp = requests.post(f"{API_URL}/generate_report", json=report_payload)
                    resp.raise_for_status()
                    rpt = resp.json()
                    st.session_state.report = rpt.get("report", "")
                    st.session_state.step = GENERATE
                    st.rerun()
                except Exception as e:
                    st.error(f"API call failed: {str(e)}")
                    st.session_state.report = ""

# GENERATE: Display report and allow feedback
elif st.session_state.step == GENERATE:
    st.title("Your Personalized Learning Report")
    
    if not st.session_state.report:
        st.error("Report generation failed. Please try again.")
        if st.button("Return to Personalization"):
            st.session_state.step = CLARIFY
            st.rerun()
    else:
        st.markdown(st.session_state.report)
        
        st.sidebar.markdown("### Report Actions")
        # Markdown download option
        download_btn = st.sidebar.download_button(
            "Download Report (Markdown)",
            data=st.session_state.report,
            file_name=f"{st.session_state.topic.replace(' ', '_')}_report.md",
            mime="text/markdown"
        )
        
        # Add PDF download option
        if "pdf_report" not in st.session_state:
            with st.spinner("Preparing PDF..."):
                try:
                    # Install with: pip install fpdf2 markdown
                    import markdown
                    from fpdf import FPDF
                    import tempfile
                    import re
                    
                    # Convert markdown to HTML
                    html = markdown.markdown(st.session_state.report)
                    
                    # Create PDF
                    class PDF(FPDF):
                        def header(self):
                            self.set_font('Arial', 'B', 12)
                            self.cell(0, 10, f'Learning Report: {st.session_state.topic}', 0, 1, 'C')
                            self.ln(10)
                        
                        def footer(self):
                            self.set_y(-15)
                            self.set_font('Arial', 'I', 8)
                            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
                    
                    # Initialize PDF with Unicode support
                    pdf = PDF()
                    pdf.add_page()
                    pdf.set_font('Arial', '', 11)
                    
                    # Remove HTML tags for simplicity
                    text = re.sub(r'<[^>]*>', '', html)
                    
                    # Replace problematic Unicode characters with ASCII equivalents
                    replacements = {
                        '\u2013': '-',  # en dash
                        '\u2014': '--',  # em dash
                        '\u2018': "'",   # left single quote
                        '\u2019': "'",   # right single quote
                        '\u201c': '"',   # left double quote
                        '\u201d': '"',   # right double quote
                        '\u2022': '*',   # bullet
                        '\u2026': '...',  # ellipsis
                        '\u00a0': ' ',   # non-breaking space
                    }
                    
                    for unicode_char, ascii_char in replacements.items():
                        text = text.replace(unicode_char, ascii_char)
                    
                    # Process headings, bold, etc.
                    lines = text.split('\n')
                    for line in lines:
                        try:
                            if line.startswith('# '):  # Main heading
                                pdf.set_font('Arial', 'B', 16)
                                pdf.cell(0, 10, line[2:], 0, 1)
                                pdf.ln(5)
                            elif line.startswith('## '):  # Subheading
                                pdf.set_font('Arial', 'B', 14)
                                pdf.cell(0, 10, line[3:], 0, 1)
                                pdf.ln(3)
                            elif line.startswith('### '):  # Sub-subheading
                                pdf.set_font('Arial', 'B', 12)
                                pdf.cell(0, 10, line[4:], 0, 1)
                                pdf.ln(3)
                            else:
                                pdf.set_font('Arial', '', 11)
                                # Skip empty lines
                                if line.strip():
                                    pdf.multi_cell(0, 5, line)
                                    pdf.ln(2)
                        except Exception as line_error:
                            # Skip problematic lines
                            st.sidebar.warning(f"Skipped a line with invalid characters")
                            continue
                    
                    # Save PDF to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                        pdf.output(tmp.name)
                        
                        # Read the PDF file
                        with open(tmp.name, 'rb') as pdf_file:
                            st.session_state.pdf_report = pdf_file.read()
                        
                except Exception as e:
                    st.sidebar.error(f"PDF creation failed: {str(e)}")
                    st.session_state.pdf_report = None
        
        # Add PDF download button if PDF was successfully created
        if st.session_state.pdf_report:
            pdf_download_btn = st.sidebar.download_button(
                "Download Report (PDF)",
                data=st.session_state.pdf_report,
                file_name=f"{st.session_state.topic.replace(' ', '_')}_report.pdf",
                mime="application/pdf"
            )
        
        st.sidebar.markdown("### Customize Report")

# MODIFY: Show updated report
elif st.session_state.step == MODIFY:
    st.title("Your Updated Learning Report")
    
    st.markdown(st.session_state.report)
    
    st.sidebar.markdown("### Report Actions")
    download_btn = st.sidebar.download_button(
        "Download Report (Markdown)",
        data=st.session_state.report,
        file_name=f"{st.session_state.topic.replace(' ', '_')}_report.md",
        mime="text/markdown"
    )
    
    st.sidebar.markdown("### Next Steps")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("Give More Feedback"):
            st.session_state.step = GENERATE
            st.rerun()
    
    with col2:
        if st.button("Start Over"):
            for key in ["step", "answers", "documents", "report", "session_id"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.step = START
            st.rerun()
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Generate Practice Quiz"):
        st.sidebar.info("Quiz functionality coming soon!")