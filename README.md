# Document Compiler

This Python script compiles various document types (PDF, DOCX, XLSX, TXT, and images) into a single, optimized PDF file. The output preserves document structure, includes metadata, and optimizes images for reduced file size while maintaining quality.

## Features

- Supports multiple file formats:
  - PDF files (`.pdf`)
  - Word documents (`.docx`)
  - Excel spreadsheets (`.xlsx`)
  - Text files (`.txt`)
  - Images (`.jpg`, `.jpeg`, `.png`, `.gif`)
- Preserves document structure and metadata
- Optimizes images (resizes large images, compresses with quality preservation)
- Creates a well-formatted, professional PDF output
- Includes table formatting for Excel data
- Provides clear document separation and navigation
- Includes error handling and logging
- Automatic timestamp-based output filename generation

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script from the command line:

```bash
python document_compiler.py <input_directory>
```

Example:
```bash
python document_compiler.py ./RequestDocs
```

The script will automatically generate an output file named `compiled_docs_YYYYMMDD_HHMMSS.pdf` where:
- `YYYYMMDD` is the current date
- `HHMMSS` is the current time

For example: `compiled_docs_20240321_143022.pdf`

## Output Format

The script generates a PDF with the following structure:

1. Title page with:
   - Compilation timestamp
   - Source directory information

2. For each document:
   - Document title
   - Metadata block (filename, type, path, timestamp)
   - Content with preserved formatting
   - Optimized images (if present)
   - Clear separation between documents

## Image Optimization

- Images are automatically optimized:
  - Resized if larger than 800x800 pixels
  - Converted to RGB color space
  - Compressed with 85% JPEG quality
  - Optimized for PDF inclusion

## Excel Handling

- Excel sheets are converted to formatted tables
- Includes sheet names and headers
- Preserves data formatting
- Optimized for readability

## Error Handling

- The script includes comprehensive error handling and logging
- Processing errors for individual files won't stop the entire process
- Check the console output for processing status and any error messages 