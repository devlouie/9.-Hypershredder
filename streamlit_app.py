"""
Document Compiler Streamlit Interface
===================================

This Streamlit application provides a web-based interface for combining multiple documents
into a single, well-formatted PDF file. It leverages the DocumentCompiler class to process
and merge various document types.

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
import datetime
import shutil

st.set_page_config(
    page_title="Document Compiler",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Document Compiler")
st.write("Upload multiple documents to compile them into a single PDF file.")

# File uploader
uploaded_files = st.file_uploader(
    "Upload your documents",
    type=['pdf', 'docx', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'gif'],
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Compile Documents"):
        # Create a temporary directory to store uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files to temporary directory
            with st.spinner("Saving uploaded files..."):
                for uploaded_file in uploaded_files:
                    file_path = Path(temp_dir) / uploaded_file.name
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

            # Process the files
            with st.spinner("Compiling documents..."):
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"compiled_docs_{timestamp}.pdf"
                
                # Initialize and run the document compiler
                processor = DocumentCompiler(temp_dir, output_file)
                processor.process_directory()
                processor.save_output()

                # Read the generated PDF for download
                if os.path.exists(output_file):
                    with open(output_file, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                    
                    # Clean up the output file
                    os.remove(output_file)
                    
                    # Create download button
                    st.success("✅ Documents compiled successfully!")
                    st.download_button(
                        label="Download Compiled PDF",
                        data=pdf_bytes,
                        file_name=output_file,
                        mime="application/pdf"
                    )
                else:
                    st.error("❌ Error: Failed to generate the compiled PDF.")

# Add some helpful information
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