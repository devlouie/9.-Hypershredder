"""
Document Processing Utilities
===========================

Pure functions for processing document elements like images and tables.
Each function is independently testable and has no side effects.
"""

import io
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image
import fitz  # PyMuPDF for better PDF handling
from docx.document import Document as DocxDocument
from docx.table import Table as DocxTable
from docx.oxml.table import CT_Tbl
from docx.shared import Inches
import pandas as pd
import numpy as np
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch

def optimize_image(
    image_data: bytes,
    max_size: Tuple[int, int] = (800, 800),
    quality: int = 85,
    target_format: str = 'JPEG'
) -> Optional[bytes]:
    """
    Optimize an image for PDF inclusion.
    
    Args:
        image_data: Raw image bytes
        max_size: Maximum dimensions (width, height)
        quality: JPEG quality (1-100)
        target_format: Output format ('JPEG', 'PNG')
    
    Returns:
        Optimized image bytes or None if processing fails
    """
    try:
        # Open image from bytes
        with Image.open(io.BytesIO(image_data)) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate aspect ratio
            aspect = img.size[0] / img.size[1]
            
            # Determine new size maintaining aspect ratio
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                if aspect > 1:
                    new_size = (max_size[0], int(max_size[0] / aspect))
                else:
                    new_size = (int(max_size[1] * aspect), max_size[1])
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            output = io.BytesIO()
            img.save(output, format=target_format, quality=quality, optimize=True)
            return output.getvalue()
            
    except Exception as e:
        print(f"Image optimization error: {str(e)}")
        return None

def extract_table_from_docx(table: DocxTable) -> List[List[str]]:
    """
    Extract data from a Word document table.
    
    Args:
        table: docx Table object
    
    Returns:
        2D list of cell values
    """
    data = []
    for row in table.rows:
        row_data = []
        for cell in row.cells:
            # Clean and normalize cell text
            text = cell.text.strip()
            # Handle merged cells
            if not text and cell._tc.xpath('./w:tcPr/w:vMerge'):
                # Find content from merged cell above
                for prev_row in data[::-1]:
                    if len(prev_row) > len(row_data):
                        text = prev_row[len(row_data)]
                        break
            row_data.append(text)
        data.append(row_data)
    return data

def create_reportlab_table(
    data: List[List[str]],
    col_widths: Optional[List[float]] = None,
    style: Optional[List[Tuple]] = None
) -> Table:
    """
    Create a ReportLab Table with styling.
    
    Args:
        data: 2D list of cell values
        col_widths: List of column widths (in inches)
        style: List of TableStyle commands
    
    Returns:
        Formatted ReportLab Table object
    """
    if not data:
        return None
        
    # Calculate column widths if not provided
    if not col_widths:
        table_width = 6.5  # Standard page width minus margins
        col_widths = [table_width / len(data[0]) * inch] * len(data[0])
    
    # Create default style if not provided
    if not style:
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ]
    
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle(style))
    return table

def extract_images_from_pdf(pdf_path: str) -> List[Tuple[bytes, str]]:
    """
    Extract images from a PDF file.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        List of tuples containing (image_bytes, image_type)
    """
    images = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_type = base_image["ext"]
                    
                    # Only include supported image types
                    if image_type.lower() in ('jpeg', 'jpg', 'png'):
                        images.append((image_bytes, image_type))
                except Exception as e:
                    print(f"Error extracting image {img_index} from page {page_num}: {str(e)}")
                    continue
                    
        doc.close()
        return images
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return []

def extract_tables_from_pdf(pdf_path: str) -> List[pd.DataFrame]:
    """
    Extract tables from a PDF file using various methods.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        List of pandas DataFrames containing table data
    """
    tables = []
    try:
        # First try using PyMuPDF's built-in table detection
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            tabs = page.find_tables()
            
            for tab in tabs.tables:
                df = pd.DataFrame(tab.extract())
                if not df.empty:
                    tables.append(df)
        
        doc.close()
        
        # If no tables found, try alternative methods
        if not tables:
            # You could add additional table extraction methods here
            # For example, using tabula-py or camelot-py
            pass
            
        return tables
    except Exception as e:
        print(f"Error extracting tables from PDF: {str(e)}")
        return []

def clean_table_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize table data.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Cleaned DataFrame
    """
    # Remove empty rows and columns
    df = df.dropna(how='all').dropna(axis=1, how='all')
    
    # Convert all data to strings and clean
    df = df.astype(str)
    df = df.apply(lambda x: x.str.strip())
    
    # Replace empty strings with None
    df = df.replace('', None)
    
    # Handle merged cells (forward fill) using ffill() instead of deprecated fillna(method='ffill')
    df = df.ffill()
    
    return df 