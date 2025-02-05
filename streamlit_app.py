"""
Document Compiler Streamlit Interface
===================================

This Streamlit application provides a web-based interface for combining multiple documents
into a single, well-formatted PDF file and analyzing opportunities using Gemini AI.

Key Features:
------------
1. Multi-file upload support
2. Progress tracking with visual indicators
3. Automatic file type detection
4. Clean PDF output with consistent formatting
5. Immediate download capability

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
from document_compiler import DocumentCompiler
from opportunity_dashboard_processor import OpportunityDashboardProcessor
import datetime
import shutil
from PIL import Image
import hashlib

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
    st.session_state.opportunity_processor = OpportunityDashboardProcessor()
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = None
if 'compilation_complete' not in st.session_state:
    st.session_state.compilation_complete = False
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

# Helper functions for step navigation
def next_step():
    st.session_state.current_step += 1
    
def prev_step():
    st.session_state.current_step -= 1

# Progress bar and step indicator
total_steps = 3
progress = (st.session_state.current_step - 1) / (total_steps - 1)
st.progress(progress)

# Step titles with visual indicators
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"{'🔵' if st.session_state.current_step == 1 else '✅' if st.session_state.current_step > 1 else '⚪'} **Step 1: Add Documents**")
with col2:
    st.markdown(f"{'🔵' if st.session_state.current_step == 2 else '✅' if st.session_state.current_step > 2 else '⚪'} **Step 2: Compile PDF**")
with col3:
    st.markdown(f"{'🔵' if st.session_state.current_step == 3 else '✅' if st.session_state.current_step > 3 else '⚪'} **Step 3: AI Analysis**")

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
                    processor = DocumentCompiler(temp_dir, output_file)
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
                    summary = st.session_state.opportunity_processor.process_pdf_context(
                        st.session_state.compiled_pdf
                    )
                    st.session_state.opportunity_summary = summary
                    st.session_state.analysis_complete = True
            
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