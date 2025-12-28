"""
LLM-Based ATS & Resume Builder - Main Streamlit Application
"""
import streamlit as st
import logging
from datetime import datetime
from pathlib import Path

# Import custom modules
from src import (
    LLMHandler, ResumeParser, ATSAnalyzer, ResumeGenerator, CSVManager,
    load_config, setup_logging, ensure_directories, load_prompts,
    save_base_resume, load_base_resume
)
from src.utils import extract_score_from_response, get_score_category, truncate_text


# Page configuration
st.set_page_config(
    page_title="LLM-Based ATS & Resume Builder",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_app():
    """Initialize application components"""
    if 'initialized' not in st.session_state:
        # Ensure directory structure
        ensure_directories()
        
        # Load configuration
        config = load_config()
        st.session_state.config = config
        
        # Setup logging
        setup_logging(config)
        logging.info("Application started")
        
        # Load prompts
        prompts = load_prompts(config['paths']['prompts'])
        st.session_state.prompts = prompts
        
        # Initialize LLM handler
        llm_handler = LLMHandler(config)
        st.session_state.llm_handler = llm_handler
        
        # Initialize other components
        st.session_state.resume_parser = ResumeParser()
        st.session_state.ats_analyzer = ATSAnalyzer(llm_handler, prompts, config)
        st.session_state.resume_generator = ResumeGenerator(llm_handler, prompts)
        st.session_state.csv_manager = CSVManager(config['paths']['applications_csv'])
        
        # Load base resume if exists
        base_resume = load_base_resume(config)
        st.session_state.base_resume = base_resume
        
        # Check Ollama connection
        st.session_state.ollama_connected = llm_handler.check_connection()
        
        st.session_state.initialized = True


def sidebar():
    """Render sidebar"""
    st.sidebar.title("⚙️ Settings")
    
    # Ollama connection status
    if st.session_state.ollama_connected:
        st.sidebar.success("✅ Ollama Connected")
    else:
        st.sidebar.error("❌ Ollama Not Connected")
        st.sidebar.info("Please start Ollama and refresh the page")
    
    # Model selection
    available_models = st.session_state.llm_handler.list_models()
    if available_models:
        selected_model = st.sidebar.selectbox(
            "Select LLM Model",
            available_models,
            index=available_models.index(st.session_state.config['ollama']['model']) 
                  if st.session_state.config['ollama']['model'] in available_models else 0
        )
        st.session_state.llm_handler.model = selected_model
    
    st.sidebar.divider()
    
    # Base Resume Management
    st.sidebar.subheader("📝 Base Resume")
    if st.session_state.base_resume:
        st.sidebar.success("Base resume loaded")
        preview = truncate_text(st.session_state.base_resume, 150)
        st.sidebar.text_area("Preview", preview, height=100, disabled=True)
        
        if st.sidebar.button("Clear Base Resume"):
            st.session_state.base_resume = None
            st.rerun()
    else:
        st.sidebar.warning("No base resume set")
    
    st.sidebar.divider()
    
    # Background/Context
    st.sidebar.subheader("👤 Your Background")
    st.session_state.background = st.sidebar.text_area(
        "Professional Background (Optional)",
        value=st.session_state.get('background', ''),
        height=150,
        help="Provide context about your experience, skills, and career goals for better recommendations"
    )
    
    st.sidebar.divider()
    
    # Application Statistics
    st.sidebar.subheader("📊 Statistics")
    stats = st.session_state.csv_manager.get_statistics()
    if stats:
        st.sidebar.metric("Total Applications", stats['total_applications'])
        st.sidebar.metric("Resumes Created", stats['resumes_created'])
        if stats['average_score'] > 0:
            st.sidebar.metric("Average ATS Score", f"{stats['average_score']}")


def main_content():
    """Render main content area"""
    st.title("🎯 LLM-Based ATS & Resume Builder")
    st.markdown("---")
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Upload Resume",
        "🔍 Resume Review",
        "📊 ATS Analysis",
        "✨ Generate Resume",
        "📈 Applications"
    ])
    
    with tab1:
        upload_resume_tab()
    
    with tab2:
        resume_review_tab()
    
    with tab3:
        ats_analysis_tab()
    
    with tab4:
        generate_resume_tab()
    
    with tab5:
        applications_tab()


def upload_resume_tab():
    """Tab for uploading and setting base resume"""
    st.header("📄 Upload & Set Base Resume")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload Resume File")
        uploaded_file = st.file_uploader(
            "Choose your resume file",
            type=['pdf', 'docx', 'txt'],
            help="Upload your resume in PDF, Word, or text format"
        )
        
        if uploaded_file:
            # Parse the file
            file_type = uploaded_file.name.split('.')[-1]
            
            with st.spinner("Parsing resume..."):
                resume_text = st.session_state.resume_parser.parse(uploaded_file, file_type)
            
            if resume_text:
                st.success("✅ Resume parsed successfully!")
                st.text_area("Extracted Text", resume_text, height=300)
                
                if st.button("Set as Base Resume", type="primary"):
                    st.session_state.base_resume = resume_text
                    save_base_resume(resume_text, st.session_state.config)
                    st.success("Base resume saved!")
                    st.rerun()
            else:
                st.error("Failed to parse resume. Please check the file format.")
    
    with col2:
        st.subheader("Or Paste Text")
        resume_text_input = st.text_area(
            "Paste your resume here",
            height=300,
            help="Copy and paste your resume text"
        )
        
        if st.button("Set Pasted Text as Base Resume"):
            if resume_text_input.strip():
                st.session_state.base_resume = resume_text_input
                save_base_resume(resume_text_input, st.session_state.config)
                st.success("Base resume saved!")
                st.rerun()
            else:
                st.warning("Please paste some text first")


def resume_review_tab():
    """Tab for reviewing resume without JD"""
    st.header("🔍 Resume Review")
    st.info("Get comprehensive feedback on your resume without a specific job description")
    
    # Resume input options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        input_method = st.radio(
            "Resume Input Method",
            ["Use Base Resume", "Upload New Resume", "Paste Text"],
            horizontal=True
        )
        
        resume_text = None
        
        if input_method == "Use Base Resume":
            if st.session_state.base_resume:
                resume_text = st.session_state.base_resume
                st.success("Using base resume")
            else:
                st.warning("No base resume set. Please upload one first.")
        
        elif input_method == "Upload New Resume":
            uploaded_file = st.file_uploader(
                "Upload resume",
                type=['pdf', 'docx', 'txt'],
                key="review_upload"
            )
            if uploaded_file:
                file_type = uploaded_file.name.split('.')[-1]
                resume_text = st.session_state.resume_parser.parse(uploaded_file, file_type)
        
        else:  # Paste Text
            resume_text = st.text_area("Paste resume text", height=200, key="review_paste")
    
    with col2:
        st.markdown("### Quick Actions")
        if st.button("🔍 Analyze Resume", type="primary", disabled=not resume_text):
            analyze_resume(resume_text)


def analyze_resume(resume_text):
    """Analyze resume and display results"""
    with st.spinner("Analyzing your resume..."):
        feedback = st.session_state.ats_analyzer.review_resume(resume_text)
    
    if feedback:
        st.success("✅ Analysis Complete!")
        st.markdown("### 📋 Resume Feedback")
        st.markdown(feedback)
        
        # Download option
        st.download_button(
            "📥 Download Feedback",
            feedback,
            file_name=f"resume_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    else:
        st.error("Failed to analyze resume. Please check Ollama connection.")


def ats_analysis_tab():
    """Tab for ATS scoring with job description"""
    st.header("📊 ATS Score Analysis")
    st.info("Compare your resume against a job description and get an ATS compatibility score")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Resume")
        resume_method = st.radio(
            "Select Resume",
            ["Use Base Resume", "Upload New", "Paste Text"],
            key="ats_resume_method",
            horizontal=True
        )
        
        resume_text = None
        
        if resume_method == "Use Base Resume":
            if st.session_state.base_resume:
                resume_text = st.session_state.base_resume
                st.success("✅ Using base resume")
            else:
                st.warning("⚠️ No base resume set")
        
        elif resume_method == "Upload New":
            file = st.file_uploader("Upload", type=['pdf', 'docx', 'txt'], key="ats_upload")
            if file:
                resume_text = st.session_state.resume_parser.parse(file, file.name.split('.')[-1])
        
        else:
            resume_text = st.text_area("Paste Resume", height=250, key="ats_paste_resume")
    
    with col2:
        st.subheader("Job Description")
        jd_text = st.text_area(
            "Paste job description here",
            height=250,
            help="Copy the entire job description",
            key="ats_jd"
        )
        
        company_name = st.text_input(
            "Company Name",
            help="This will be saved in your applications tracker",
            key="ats_company"
        )
    
    # Analyze button
    if st.button("📊 Calculate ATS Score", type="primary", disabled=not (resume_text and jd_text)):
        analyze_ats_score(resume_text, jd_text, company_name)


def analyze_ats_score(resume_text, jd_text, company_name):
    """Perform ATS analysis and display results"""
    background = st.session_state.get('background', None)
    
    with st.spinner("Analyzing ATS compatibility..."):
        score, feedback = st.session_state.ats_analyzer.analyze_ats_score(
            resume_text, jd_text, background
        )
    
    if feedback:
        # Display score prominently
        col1, col2, col3 = st.columns(3)
        
        if score is not None:
            interpretation = st.session_state.ats_analyzer.get_score_interpretation(score)
            
            with col1:
                st.metric("ATS Score", f"{score}/100")
            with col2:
                st.metric("Category", interpretation['category'])
            with col3:
                st.metric("Status", interpretation['interpretation'])
            
            # Score visualization
            score_color = interpretation['color']
            st.progress(score / 100)
        
        st.markdown("---")
        st.markdown("### 📋 Detailed Analysis")
        st.markdown(feedback)
        
        # Save to CSV
        if company_name:
            # Extract key improvements from feedback
            changes = truncate_text(feedback, 200)
            jd_summary = truncate_text(jd_text, 150)
            
            st.session_state.csv_manager.add_entry(
                company=company_name,
                resume_created=False,
                ats_score=score,
                changes_required=changes,
                job_description_summary=jd_summary
            )
            st.success(f"📝 Entry saved for {company_name}")
        
        # Download option
        st.download_button(
            "📥 Download Analysis",
            feedback,
            file_name=f"ats_analysis_{company_name}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
    else:
        st.error("Failed to perform ATS analysis. Check Ollama connection.")


def generate_resume_tab():
    """Tab for generating tailored resumes"""
    st.header("✨ Generate Tailored Resume")
    st.info("Create a customized resume based on your base resume and a job description")
    
    if not st.session_state.base_resume:
        st.warning("⚠️ Please set a base resume first in the 'Upload Resume' tab")
        return
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Job Description")
        jd_for_gen = st.text_area(
            "Paste the job description",
            height=300,
            key="gen_jd"
        )
        
        company_for_gen = st.text_input(
            "Company Name",
            key="gen_company",
            help="Required for tracking"
        )
    
    with col2:
        st.subheader("Options")
        use_background = st.checkbox(
            "Use background context",
            value=bool(st.session_state.get('background')),
            help="Include your background for better results"
        )
        
        st.markdown("---")
        st.markdown("**Base Resume Preview**")
        preview = truncate_text(st.session_state.base_resume, 200)
        st.text_area("", preview, height=150, disabled=True, key="gen_preview")
    
    if st.button("✨ Generate Tailored Resume", type="primary", disabled=not (jd_for_gen and company_for_gen)):
        generate_resume(jd_for_gen, company_for_gen, use_background)


def generate_resume(jd_text, company_name, use_background):
    """Generate tailored resume"""
    background = st.session_state.get('background') if use_background else None
    
    with st.spinner("Generating tailored resume... This may take a minute."):
        generated = st.session_state.resume_generator.generate_tailored_resume(
            st.session_state.base_resume,
            jd_text,
            background
        )
    
    if generated:
        st.success("✅ Resume Generated Successfully!")
        st.markdown("### 📄 Your Tailored Resume")
        st.text_area("", generated, height=400, key="generated_resume_display")
        
        # Save to CSV
        jd_summary = truncate_text(jd_text, 150)
        st.session_state.csv_manager.add_entry(
            company=company_name,
            resume_created=True,
            job_description_summary=jd_summary,
            notes="Resume generated successfully"
        )
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download as TXT",
                generated,
                file_name=f"resume_{company_name}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
        with col2:
            st.download_button(
                "📥 Download Markdown",
                generated,
                file_name=f"resume_{company_name}_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
    else:
        st.error("Failed to generate resume. Please check Ollama connection.")


def applications_tab():
    """Tab for viewing application history"""
    st.header("📈 Application Tracker")
    
    df = st.session_state.csv_manager.get_all_entries()
    
    if df is not None and len(df) > 0:
        st.subheader(f"📊 Total Applications: {len(df)}")
        
        # Display statistics
        stats = st.session_state.csv_manager.get_statistics()
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", stats['total_applications'])
            with col2:
                st.metric("Generated", stats['resumes_created'])
            with col3:
                st.metric("Avg Score", f"{stats['average_score']}")
            with col4:
                st.metric("Companies", len(stats['companies']))
        
        st.markdown("---")
        
        # Filters
        col1, col2 = st.columns([3, 1])
        with col1:
            search_company = st.text_input("🔍 Search by company", key="search_company")
        with col2:
            show_entries = st.selectbox("Show entries", [10, 25, 50, 100, "All"], index=0)
        
        # Filter dataframe
        display_df = df
        if search_company:
            display_df = display_df[display_df['company'].str.contains(search_company, case=False, na=False)]
        
        if show_entries != "All":
            display_df = display_df.head(show_entries)
        
        # Display table
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Export option
        if st.button("📥 Export to Excel"):
            output_path = f"applications_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            if st.session_state.csv_manager.export_to_excel(output_path):
                st.success(f"Exported to {output_path}")
                with open(output_path, 'rb') as f:
                    st.download_button(
                        "Download Excel",
                        f,
                        file_name=output_path,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
    else:
        st.info("📭 No applications yet. Start by analyzing resumes or generating tailored ones!")


def main():
    """Main application entry point"""
    # Initialize app
    initialize_app()
    
    # Render sidebar
    sidebar()
    
    # Render main content
    main_content()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Made with ❤️ | Powered by Ollama & Streamlit"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()