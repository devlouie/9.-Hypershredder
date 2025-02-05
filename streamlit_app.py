"""
Document Analysis and Tender Response Interface
============================================

This Streamlit application provides a web-based interface for analyzing tender documents
and generating contextually aware responses.

Key Features:
------------
1. Multi-file upload support
2. Document compilation
3. AI-powered analysis
4. Tender response generation
5. Interactive chat capabilities

Supported File Types:
-------------------
- PDF (.pdf): Maintains original formatting
- Word Documents (.docx): Preserves text and embedded images
- Excel Spreadsheets (.xlsx): Converts tables with styling
- Text Files (.txt): Simple text conversion
- Images (.jpg, .jpeg, .png, .gif): Optimized for PDF inclusion

Usage Instructions:
-----------------
1. Start the application:
   ```bash
   streamlit run streamlit_app.py
   ```

2. Access the web interface:
   - Default URL: http://localhost:8501
   - The interface will open automatically in your default browser

3. Upload documents:
   - Click the upload area or drag and drop files
   - Multiple files can be selected simultaneously
   - Files are processed in alphabetical order

4. Compile documents:
   - Click "Compile Documents" after uploading
   - Wait for the processing indicators
   - Download the compiled PDF when ready

Technical Details:
----------------
- Files are processed in a temporary directory for security
- Each compilation creates a unique timestamped output
- Memory-efficient processing for large documents
- Automatic cleanup of temporary files
- Error handling with user-friendly messages

Dependencies:
------------
- streamlit: Web interface framework
- PyPDF2: PDF processing
- python-docx: Word document handling
- openpyxl: Excel file processing
- reportlab: PDF generation
- Pillow: Image processing

Author: [Your Name]
Version: 1.0.0
Last Updated: 2024
License: MIT
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
import datetime
import shutil
from PIL import Image
import hashlib
import json

from document_processor import DocumentProcessor
from opportunity_analyzer import OpportunityAnalyzer
from tender_response_processor import TenderResponseProcessor

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None

def authenticate(username: str, password: str) -> bool:
    """Verify username and password."""
    if not st.secrets.credentials.usernames:
        st.error("No credentials configured. Please set up secrets.toml")
        return False
    
    if username not in st.secrets.credentials.usernames:
        return False
    
    # Hash the input password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return st.secrets.credentials.usernames[username] == hashed_password

def login_form():
    """Display the login form."""
    st.markdown("## 🔐 Login")
    
    # Center the form on the page
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if authenticate(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")

def logout():
    """Log out the user."""
    st.session_state.authenticated = False
    st.session_state.username = None
    reset_app_state()
    st.rerun()

# Set up the page configuration
st.set_page_config(
    page_title="Document Compiler",
    page_icon="📄",
    layout="wide"
)

# Add logo to sidebar
try:
    logo_path = "static/logo.png"
    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
        # Create a sidebar
        with st.sidebar:
            # Add the logo with custom styling
            st.image(logo, width=200)  # Adjust width as needed
            st.markdown("---")  # Add a separator line
except Exception as e:
    st.sidebar.error("Please add your logo.png file to the static directory")

# Check authentication
if not st.session_state.authenticated:
    login_form()
    st.stop()  # Stop the app here if not authenticated

# Add logout and welcome message to sidebar
with st.sidebar:
    st.markdown(f"👤 Welcome, **{st.session_state.username}**!")
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        logout()

# Function to reset the application state
def reset_app_state():
    for key in list(st.session_state.keys()):
        if key != 'opportunity_processor':  # Keep the processor instance to avoid reinitializing
            del st.session_state[key]
    st.session_state.current_step = 1
    st.session_state.compilation_complete = False
    st.session_state.analysis_complete = False
    st.session_state.uploaded_files = None
    st.session_state.compiled_pdf = None
    if 'chat_messages' in st.session_state:
        st.session_state.chat_messages = []

# Add restart button to sidebar
with st.sidebar:
    if st.button("🔄 Restart Process", use_container_width=True):
        reset_app_state()
        st.rerun()

# Initialize session state for storing PDF content and step tracking
if 'compiled_pdf' not in st.session_state:
    st.session_state.compiled_pdf = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'opportunity_processor' not in st.session_state:
    st.session_state.opportunity_processor = OpportunityAnalyzer()
if 'tender_processor' not in st.session_state:
    st.session_state.tender_processor = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = None
if 'compilation_complete' not in st.session_state:
    st.session_state.compilation_complete = False
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'submitter_context' not in st.session_state:
    st.session_state.submitter_context = None
if 'tender_response_complete' not in st.session_state:
    st.session_state.tender_response_complete = False

# Helper functions for step navigation
def next_step():
    st.session_state.current_step += 1
    
def prev_step():
    st.session_state.current_step -= 1

# Progress bar and step indicator
total_steps = 4  # Updated to include new step
progress = (st.session_state.current_step - 1) / (total_steps - 1)
st.progress(progress)

# Step titles with visual indicators
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"{'🔵' if st.session_state.current_step == 1 else '✅' if st.session_state.current_step > 1 else '⚪'} **Step 1: Add Documents**")
with col2:
    st.markdown(f"{'🔵' if st.session_state.current_step == 2 else '✅' if st.session_state.current_step > 2 else '⚪'} **Step 2: Compile PDF**")
with col3:
    st.markdown(f"{'🔵' if st.session_state.current_step == 3 else '✅' if st.session_state.current_step > 3 else '⚪'} **Step 3: AI Analysis**")
with col4:
    st.markdown(f"{'🔵' if st.session_state.current_step == 4 else '✅' if st.session_state.current_step > 4 else '⚪'} **Step 4: Tender Response**")

st.markdown("---")

# Step 1: Document Upload
if st.session_state.current_step == 1:
    st.header("Step 1: Add Documents")
    
    uploaded_files = st.file_uploader(
        "Upload your documents",
        type=['pdf', 'docx', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'gif'],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        st.success(f"✅ {len(uploaded_files)} documents uploaded successfully!")
        next_step()
        st.rerun()

# Step 2: Document Compilation
elif st.session_state.current_step == 2:
    st.header("Step 2: Compile Documents")
    
    if st.session_state.uploaded_files:
        if not st.session_state.compilation_complete:
            with st.spinner("Compiling documents..."):
                # Create a temporary directory to store uploaded files
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save uploaded files to temporary directory
                    for uploaded_file in st.session_state.uploaded_files:
                        file_path = Path(temp_dir) / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_file = f"compiled_docs_{timestamp}.pdf"
                    
                    # Initialize and run the document compiler
                    processor = DocumentProcessor(temp_dir, output_file)
                    processor.process_directory()
                    processor.save_output()

                    # Read the generated PDF for download
                    if os.path.exists(output_file):
                        with open(output_file, "rb") as pdf_file:
                            st.session_state.compiled_pdf = pdf_file.read()
                        
                        # Clean up the output file
                        os.remove(output_file)
                        st.session_state.compilation_complete = True
                        
            if st.session_state.compilation_complete:
                st.success("✅ Documents compiled successfully!")
                st.download_button(
                    label="Download Compiled PDF",
                    data=st.session_state.compiled_pdf,
                    file_name=output_file,
                    mime="application/pdf"
                )
                next_step()
                st.rerun()
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back"):
                prev_step()
                st.rerun()
    else:
        st.error("Please upload documents in Step 1 first.")
        if st.button("← Back to Upload"):
            prev_step()
            st.rerun()

# Step 3: AI Analysis
elif st.session_state.current_step == 3:
    st.header("Step 3: AI Analysis")
    
    if st.session_state.compiled_pdf is not None:
        # Initialize chat history in session state if not exists
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        # Create two columns - one for analysis, one for chat
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Main analysis area
            if not st.session_state.analysis_complete:
                with st.spinner("Analyzing documents..."):
                    summary = st.session_state.opportunity_processor.analyze_document(
                        st.session_state.compiled_pdf
                    )
                    st.session_state.opportunity_summary = summary
                    st.session_state.analysis_complete = True
            
            # Add button to proceed to tender response at the top
            if st.session_state.analysis_complete:
                st.success("✅ Analysis complete!")
                if st.button("🚀 Generate Tender Response", use_container_width=True):
                    next_step()
                    st.rerun()
                st.markdown("---")
            
            with st.expander("📊 Document Analysis", expanded=True):
                st.markdown(st.session_state.opportunity_summary)
            
            # Opportunity metrics in a clean grid
            metrics = st.session_state.opportunity_processor.get_opportunity_summary()
            if 'error' not in metrics:
                st.subheader("📈 Key Metrics")
                metric_cols = st.columns(2)
                for idx, (key, value) in enumerate(metrics.items()):
                    with metric_cols[idx % 2]:
                        if isinstance(value, (str, int, float)):
                            st.metric(label=key.replace('_', ' ').title(), value=value)
        
        with col2:
            # Enhanced AI Chat Interface
            st.subheader("💬 AI Assistant")
            
            # Chat message container with custom styling
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.chat_messages:
                    if message["role"] == "user":
                        st.markdown(
                            f"""
                            <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
                                <div style="background-color: #e6f3ff; padding: 0.5rem 1rem; border-radius: 15px; max-width: 80%;">
                                    <p style="margin: 0;"><strong>You:</strong> {message["content"]}</p>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"""
                            <div style="display: flex; margin-bottom: 1rem;">
                                <div style="background-color: #f0f2f6; padding: 0.5rem 1rem; border-radius: 15px; max-width: 80%;">
                                    <p style="margin: 0;"><strong>AI:</strong> {message["content"]}</p>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            
            # Chat input area with a clean design
            st.markdown("---")
            with st.form(key="chat_form", clear_on_submit=True):
                user_question = st.text_area("Ask me anything about the documents:", height=100, 
                                           placeholder="Type your question here...")
                submit_button = st.form_submit_button("Send Message 📤")
                
                if submit_button and user_question:
                    # Add user message to chat history
                    st.session_state.chat_messages.append({"role": "user", "content": user_question})
                    
                    # Get AI response
                    with st.spinner("Thinking..."):
                        response = st.session_state.opportunity_processor.get_chat_response(user_question)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    
                    # Rerun to update chat display
                    st.rerun()
            
            # Helper text
            with st.expander("💡 Tips for better questions"):
                st.markdown("""
                - Ask specific questions about the document content
                - Request clarification on technical requirements
                - Inquire about risk assessments and mitigation strategies
                - Ask for deadline and timeline details
                - Request budget and financial analysis
                """)
        
        # Navigation buttons
        st.markdown("---")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back"):
                prev_step()
                st.session_state.analysis_complete = False
                st.rerun()
    else:
        st.error("Please complete document compilation in Step 2 first.")
        if st.button("← Back to Compilation"):
            prev_step()
            st.rerun()

# Step 4: Tender Response
elif st.session_state.current_step == 4:
    st.header("Step 4: Tender Response")
    
    if st.session_state.analysis_complete:
        # Initialize tender processor if not already done
        if st.session_state.tender_processor is None and st.session_state.opportunity_processor.analysis_context:
            st.session_state.tender_processor = TenderResponseProcessor(
                st.session_state.opportunity_processor.analysis_context
            )
        
        # Add pre-amble section
        st.markdown("""
        <style>
        .info-box {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #f8f9fa;
            border-left: 4px solid #0066cc;
            margin-bottom: 1.5rem;
        }
        .requirement-list {
            list-style-type: none;
            padding-left: 0;
        }
        .requirement-list li {
            margin-bottom: 0.5rem;
            padding-left: 1.5rem;
            position: relative;
        }
        .requirement-list li:before {
            content: "•";
            color: #0066cc;
            font-weight: bold;
            position: absolute;
            left: 0;
        }
        .workflow-step {
            background-color: #ffffff;
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            border: 1px solid #e6e6e6;
            margin-bottom: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Information Box
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### ℹ️ Submitter Profile Requirements")
        st.markdown("""
        Your submitter profile helps us generate a tailored tender response that highlights your company's strengths 
        and aligns with the tender requirements. Please provide accurate and detailed information in each section.
        
        **Key Requirements:**
        <ul class="requirement-list">
        <li><strong>Company Details:</strong> Official registered name and website for credibility verification</li>
        <li><strong>Core Competencies:</strong> Clear description of your main business activities and expertise</li>
        <li><strong>Differentiators:</strong> Unique selling points that set you apart from competitors</li>
        <li><strong>Track Record:</strong> Relevant past projects and performance metrics</li>
        <li><strong>Compliance:</strong> Current certifications and regulatory compliance status</li>
        </ul>
        
        **Workflow:**
        <div class="workflow-step">1️⃣ <strong>Load or Create Profile</strong> - Either upload a saved profile or fill out a new one</div>
        <div class="workflow-step">2️⃣ <strong>Review & Refine</strong> - Ensure all information is accurate and up-to-date</div>
        <div class="workflow-step">3️⃣ <strong>Save for Later</strong> - Optionally download your profile for future use</div>
        <div class="workflow-step">4️⃣ <strong>Proceed</strong> - Generate your tailored tender response</div>
        
        **Tips for Better Responses:**
        <ul class="requirement-list">
        <li>Be specific about your experience in similar projects</li>
        <li>Quantify achievements where possible (e.g., "Delivered 20% cost savings")</li>
        <li>Focus on relevant certifications for this tender</li>
        <li>Highlight unique technological capabilities or methodologies</li>
        </ul>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Context Collection Form
        if not st.session_state.submitter_context:
            st.subheader("📝 Submitter Context")
            
            # Add memory card features
            st.markdown("""
            <style>
            .memory-card {
                padding: 1rem;
                border-radius: 0.5rem;
                background-color: #f8f9fa;
                margin-bottom: 1rem;
            }
            .form-card {
                padding: 1.5rem;
                border-radius: 0.5rem;
                background-color: #ffffff;
                border: 1px solid #e6e6e6;
                margin-bottom: 1rem;
            }
            .action-buttons {
                display: flex;
                gap: 1rem;
                margin-top: 1rem;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Create two columns for side-by-side layout
            left_col, right_col = st.columns([1, 1])
            
            # Memory Card Section in left column
            with left_col:
                with st.container():
                    st.markdown("### 💾 Load Saved Profile")
                    st.markdown('<div class="memory-card">', unsafe_allow_html=True)
                    st.markdown("""
                    **Instructions:**
                    1. Upload your saved profile (.json)
                    2. Form will be populated automatically
                    3. Review and click 'Proceed' when ready
                    """)
                    
                    # Load profile section
                    uploaded_profile = st.file_uploader(
                        "Upload a saved profile (.json)",
                        type=['json'],
                        key="profile_uploader"
                    )
                    
                    if uploaded_profile:
                        try:
                            loaded_context = json.loads(uploaded_profile.getvalue().decode())
                            # Instead of using immediately, populate the form
                            st.session_state.form_data = loaded_context
                            st.success("✅ Profile loaded! Please review the form →")
                        except Exception as e:
                            st.error(f"Error loading profile: {str(e)}")
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # New Submitter Form in right column
            with right_col:
                st.markdown("### 📋 Submitter Profile")
                st.markdown('<div class="form-card">', unsafe_allow_html=True)
                
                # Initialize form data from session state if exists
                if 'form_data' not in st.session_state:
                    st.session_state.form_data = {
                        'company_name': '',
                        'company_website': '',
                        'company_description': '',
                        'key_differentiators': '',
                        'past_performance': '',
                        'certifications': ''
                    }
                
                # Create form with pre-populated values if available
                new_context = {}
                new_context['company_name'] = st.text_input("Company Name", value=st.session_state.form_data.get('company_name', ''))
                new_context['company_website'] = st.text_input("Company Website", value=st.session_state.form_data.get('company_website', ''))
                new_context['company_description'] = st.text_area(
                    "Company Description",
                    value=st.session_state.form_data.get('company_description', ''),
                    help="Provide a brief description of your company, its core competencies, and relevant experience."
                )
                new_context['key_differentiators'] = st.text_area(
                    "Key Differentiators",
                    value=st.session_state.form_data.get('key_differentiators', ''),
                    help="What makes your company unique? List your main competitive advantages."
                )
                new_context['past_performance'] = st.text_area(
                    "Past Performance",
                    value=st.session_state.form_data.get('past_performance', ''),
                    help="Describe relevant past projects or similar work experience."
                )
                new_context['certifications'] = st.text_area(
                    "Certifications & Compliance",
                    value=st.session_state.form_data.get('certifications', ''),
                    help="List relevant certifications, accreditations, and compliance standards."
                )
                
                # Action buttons in a single row
                st.markdown("---")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("💾 Download Profile", use_container_width=True):
                        if new_context['company_name'] and new_context['company_website'] and new_context['company_description']:
                            profile_json = json.dumps(new_context, indent=2)
                            filename = f"{new_context['company_name'].lower().replace(' ', '_')}_profile.json"
                            st.download_button(
                                label="📄 Save to Device",
                                data=profile_json,
                                file_name=filename,
                                mime="application/json",
                                key="download_profile"
                            )
                        else:
                            st.error("Please fill in all required fields before downloading")
                
                with col2:
                    if st.button("✅ Proceed with Profile", use_container_width=True):
                        if new_context['company_name'] and new_context['company_website'] and new_context['company_description']:
                            st.session_state.submitter_context = new_context
                            st.success("Profile accepted! Generating tender response...")
                            st.rerun()
                        else:
                            st.error("Please fill in all required fields (Company Name, Website, and Description)")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
        # Display Tender Response after context is provided
        if st.session_state.submitter_context and st.session_state.tender_processor:
            if not st.session_state.tender_response_complete:
                with st.spinner("Generating tender response..."):
                    tender_response = st.session_state.tender_processor.generate_response(
                        context=st.session_state.submitter_context
                    )
                    st.session_state.tender_response = tender_response
                    st.session_state.tender_response_complete = True
            
            # Display tender response in an expander
            with st.expander("📝 Tender Response", expanded=True):
                st.markdown(st.session_state.tender_response)
                
                # Add section-specific response generation
                st.subheader("Generate Section-Specific Response")
                sections = [
                    "1. Executive Overview",
                    "2. Technical Response",
                    "3. Implementation Plan",
                    "4. Team Structure",
                    "5. Past Performance",
                    "6. Commercial Terms",
                    "7. Value Added"
                ]
                selected_section = st.selectbox("Select section to regenerate:", sections)
                if st.button("Regenerate Section"):
                    with st.spinner(f"Regenerating {selected_section}..."):
                        section_response = st.session_state.tender_processor.generate_response(
                            context=st.session_state.submitter_context,
                            section_name=selected_section
                        )
                        st.markdown(section_response)
            
            # Add option to edit context
            if st.button("Edit Submitter Context"):
                st.session_state.submitter_context = None
                st.session_state.tender_response_complete = False
                st.rerun()
        
        # Navigation buttons
        st.markdown("---")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back"):
                prev_step()
                st.rerun()
    else:
        st.error("Please complete the AI Analysis in Step 3 first.")
        if st.button("← Back to Analysis"):
            prev_step()
            st.rerun()

# Add helpful information in sidebar
with st.sidebar:
    with st.expander("ℹ️ Supported File Types"):
        st.write("""
        - PDF files (.pdf)
        - Word documents (.docx)
        - Excel spreadsheets (.xlsx)
        - Text files (.txt)
        - Images (.jpg, .jpeg, .png, .gif)
        """)

# Add footer
st.markdown("---")
st.markdown(
    "Made with ❤️ using Streamlit",
    unsafe_allow_html=True
) 