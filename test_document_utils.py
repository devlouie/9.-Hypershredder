"""
Tests for document processing utilities
"""

import unittest
import io
import os
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image
from document_utils import (
    optimize_image,
    extract_table_from_docx,
    create_reportlab_table,
    extract_images_from_pdf,
    extract_tables_from_pdf,
    clean_table_data
)

class TestDocumentUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create test images
        cls.test_image_path = Path("test_image.jpg")
        img = Image.new('RGB', (1000, 1000), color='red')
        img.save(cls.test_image_path)
        
        # Create test PDF with images and tables
        cls.test_pdf_path = Path("test_document.pdf")
        # You would create a test PDF here with known content
        
    @classmethod
    def tearDownClass(cls):
        # Clean up test files
        if cls.test_image_path.exists():
            cls.test_image_path.unlink()
        if cls.test_pdf_path.exists():
            cls.test_pdf_path.unlink()

    def test_optimize_image(self):
        """Test image optimization function"""
        # Test with valid image
        with open(self.test_image_path, 'rb') as f:
            image_data = f.read()
        
        result = optimize_image(
            image_data,
            max_size=(500, 500),
            quality=85
        )
        
        self.assertIsNotNone(result)
        # Verify the optimized image size
        with Image.open(io.BytesIO(result)) as img:
            self.assertLessEqual(img.size[0], 500)
            self.assertLessEqual(img.size[1], 500)
        
        # Test with invalid image data
        result = optimize_image(b'invalid image data')
        self.assertIsNone(result)

    def test_create_reportlab_table(self):
        """Test ReportLab table creation"""
        # Test with valid data
        data = [
            ['Header 1', 'Header 2'],
            ['Cell 1', 'Cell 2'],
            ['Cell 3', 'Cell 4']
        ]
        
        table = create_reportlab_table(data)
        self.assertIsNotNone(table)
        
        # Test with empty data
        table = create_reportlab_table([])
        self.assertIsNone(table)
        
        # Test with custom column widths
        col_widths = [2*inch, 3*inch]
        table = create_reportlab_table(data, col_widths=col_widths)
        self.assertIsNotNone(table)

    def test_clean_table_data(self):
        """Test table data cleaning"""
        # Create test DataFrame with various issues
        df = pd.DataFrame({
            'A': ['  value1  ', '', np.nan, 'value4'],
            'B': [np.nan, 'value2', '  value3  ', ''],
            'C': [np.nan, np.nan, np.nan, np.nan]
        })
        
        cleaned_df = clean_table_data(df)
        
        # Verify cleaning results
        self.assertNotIn('C', cleaned_df.columns)  # Empty column should be removed
        self.assertEqual(cleaned_df['A'][0], 'value1')  # Spaces should be stripped
        self.assertIsNotNone(cleaned_df['A'][1])  # Empty values should be filled
        
if __name__ == '__main__':
    unittest.main() 