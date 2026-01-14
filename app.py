import streamlit as st
import pandas as pd
from utils import extract_text_from_upload, fetch_job_description_from_url, create_highlighted_pdf
from analyzer import analyze_resume

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ProMatch AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background-color: transparent; 
    }
    
    /* Header Styling - ADAPTIVE */
    .header-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        margin-bottom: 2rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    }
    .header-title {
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        color: inherit;
    }
    .header-subtitle {
        font-size: 1.1rem;
        opacity: 0.8;
        margin-top: -5px;
    }
    
    /* Footer Styling */
    .footer {
        width: 100%;
        text-align: center;
        padding: 20px;
        margin-top: 50px;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
        font-size: 0.9rem;
        opacity: 0.7;
    }
    
    /* Component Styling */
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #e74c3c, #f39c12, #4CAF50); }
    .skill-tag-match { display: inline-block; padding: 6px 12px; margin: 4px; border-radius: 20px; background-color: #2e7d32; color: white; border: 1px solid #1b5e20; font-size: 0.9rem; }
    .skill-tag-miss { display: inline-block; padding: 6px 12px; margin: 4px; border-radius: 20px; background-color: #c62828; color: white; border: 1px solid #b71c1c; font-size: 0.9rem; }
    
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- RENDER HEADER ---
st.markdown("""
<div class="header-container">
    <h1 class="header-title">🚀 ProMatch AI</h1>
    <p class="header-subtitle">Intelligent Resume Optimization & Analysis System</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50)
    st.subheader("Configuration")
    threshold = st.slider("Strictness Level", 0.0, 1.0, 0.45, help="Adjust how strict the semantic matching should be.")
    st.markdown("---")
    st.info("💡 **Tip:** Use the 'Job URL' tab to quickly load job requirements directly from LinkedIn or Indeed.")

# --- MAIN INPUT SECTION ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 1. Upload Resume")
    uploaded_file = st.file_uploader("Upload your resume (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt'])

with col2:
    st.markdown("### 2. Job Description")
    # Tab selection for Text vs URL
    jd_input_type = st.radio("Input Source", ["Paste Text", "Job URL"], horizontal=True, label_visibility="collapsed")
    
    if jd_input_type == "Paste Text":
        job_desc = st.text_area("Paste JD here...", height=200, placeholder="Copy and paste the full job description here...")
    else:
        job_url = st.text_input("Enter Job URL (LinkedIn/Indeed/etc.)")
        # UNIQUE KEY ADDED BELOW: key="btn_fetch_jd_unique"
        if st.button("Fetch JD", use_container_width=True, key="btn_fetch_jd_unique"):
            with st.spinner("Fetching job details..."):
                job_desc = fetch_job_description_from_url(job_url)
                if "Error" in job_desc:
                    st.error(job_desc)
                else:
                    st.success("Job description loaded successfully!")
                    st.text_area("Preview", job_desc, height=100)
        else:
            job_desc = ""

# --- ANALYSIS TRIGGER ---
st.markdown("<br>", unsafe_allow_html=True) # Spacer

# UNIQUE KEY ADDED BELOW: key="btn_analyze_resume_unique"
if st.button("Analyze Resume", type="primary", use_container_width=True, key="btn_analyze_resume_unique"):
    
    if jd_input_type == "Job URL" and 'job_desc' not in locals():
         st.warning("Please fetch the URL first.")
    
    elif uploaded_file and job_desc:
        with st.spinner("🔍 Analyzing semantic matches..."):
            
            # 1. EXTRACT TEXT
            resume_text = extract_text_from_upload(uploaded_file)
            
            # Validation Check
            if resume_text.startswith("Error"):
                st.error(f"❌ Failed to process file. It might be corrupted or password protected.\n\nDetails: {resume_text}")
                st.stop()
            
            if len(resume_text.strip()) < 50:
                st.warning("⚠️ The uploaded file contains very little text. If this is a scanned PDF, ensure it is clear enough for OCR.")

            # 2. ANALYZE
            score, present, missing = analyze_resume(resume_text, job_desc, threshold)
            
            st.markdown("---")
            
            # --- SCORE CARDS ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Match Score", f"{score}%")
            c2.metric("Skills Found", len(present))
            c3.metric("Missing Skills", len(missing), delta_color="inverse")
            st.progress(int(score))
            
            # --- TABS FOR RESULTS ---
            tab1, tab2, tab3, tab4 = st.tabs(["✅ Matched", "⚠️ Missing", "🔥 Heatmap", "📋 Data"])
            
            with tab1:
                if present:
                    html_tags = [f'<span class="skill-tag-match">{skill}</span>' for skill in present]
                    st.markdown(" ".join(html_tags), unsafe_allow_html=True)
                else:
                    st.info("No direct matches found.")
            
            with tab2:
                if missing:
                    html_tags = [f'<span class="skill-tag-miss">{skill}</span>' for skill in missing]
                    st.markdown(" ".join(html_tags), unsafe_allow_html=True)
                    st.caption("Tip: Try to include these keywords in your 'Experience' or 'Skills' section.")
                else:
                    st.success("All skills matched! You are a strong candidate.")

            with tab3:
                # Heatmap Overlay
                if uploaded_file.name.endswith(".pdf"):
                    st.write("Keywords highlighted in **Green** denote found skills.")
                    highlighted_images = create_highlighted_pdf(uploaded_file, present)
                    for img in highlighted_images:
                        st.image(img, use_container_width=True)
                else:
                    st.warning("Heatmap is only available for PDF files.")

            with tab4:
                all_skills = [{"Skill": s, "Status": "✅ Present"} for s in present] + \
                             [{"Skill": s, "Status": "⚠️ Missing"} for s in missing]
                st.dataframe(pd.DataFrame(all_skills), use_container_width=True)

    else:
        st.warning("Please provide both a resume and a job description.")

# --- FOOTER ---
st.markdown("""
<div class="footer">
    <p>Developed by Ruthvik | &copy; 2026 ProMatch AI</p>
</div>
""", unsafe_allow_html=True)