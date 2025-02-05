"""
Opportunity Analyzer
==================

This module handles the analysis of tender documents using Gemini AI to extract
key insights, requirements, and opportunities.

Key Features:
------------
1. PDF document analysis
2. Opportunity scoring
3. Requirements extraction
4. Risk assessment
5. Interactive Q&A capabilities
"""

import google.generativeai as genai
from pathlib import Path
import tempfile
import json
import os
import logging
from typing import Optional, Dict, List
import PyPDF2
import re
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpportunityAnalyzer:
    """
    A class to analyze tender documents and extract key insights.
    
    This class handles:
    1. Document processing
    2. Opportunity analysis
    3. Requirements extraction
    4. Interactive Q&A
    """
    
    def __init__(self):
        """Initialize the opportunity analyzer."""
        self._setup_gemini()
        self.chat_history = []
        self.analysis_context = ""
        self.max_text_length = 30000  # Maximum characters to process
        
    def _setup_gemini(self):
        """Configure the Gemini AI client."""
        try:
            if not hasattr(st.secrets.api_keys, 'gemini'):
                raise ValueError("Gemini API key not found in secrets")
            
            genai.configure(api_key=st.secrets.api_keys.gemini)
            self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')
            self.chat = self.model.start_chat(history=[])
            logger.info("Gemini AI setup completed successfully")
        except Exception as e:
            logger.error(f"Error setting up Gemini AI: {e}")
            raise

    def analyze_document(self, pdf_content: bytes) -> str:
        """
        Analyze the PDF content and extract key insights.
        
        Args:
            pdf_content (bytes): The compiled PDF file content
            
        Returns:
            str: A structured analysis of the opportunity
        """
        try:
            # Save PDF temporarily for processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf.write(pdf_content)
                temp_pdf_path = temp_pdf.name

            # Create a Part object for the PDF
            pdf_part = {
                "mime_type": "application/pdf",
                "data": pdf_content
            }

            # Generate initial analysis
            initial_prompt = """You are an expert business analyst specializing in technical procurement and enterprise sales opportunities. Analyze the provided document and generate a structured analysis that can be directly displayed in Streamlit.

Structure your response in clear markdown sections as follows:

# Executive Summary
[Provide a 2-3 sentence overview of the opportunity]

# What are they asking for?
[ A direct clean list of the requirements ]

# Who is needed to make this happen?
[ A list of contractors or providers and their responsibilities ( jobs to be done - doers matrix ) ]

# Opportunity Score: [1-10]
[Brief justification for the score]

# Key Metrics
- Current Phase: [Phase]
- Timeline: [Duration]
- Budget Status: [Status]
- Estimated Value: [Amount]

# Important Dates
- Submission Deadline: [Date]
- Project Start: [Date]
- Key Milestones: [Dates]

# Technical Requirements
1. Core Requirements:
   - [Requirement 1]
   - [Requirement 2]

2. Compliance Requirements:
   - [Requirement 1]
   - [Requirement 2]

# Risk Analysis
## High Priority Risks
- [Risk 1]: [Mitigation Strategy]
- [Risk 2]: [Mitigation Strategy]

## Medium Priority Risks
- [Risk 1]: [Mitigation Strategy]
- [Risk 2]: [Mitigation Strategy]

# Key Stakeholders
| Role | Influence Level | Notes |
|------|----------------|-------|
| [Role 1] | [High/Medium/Low] | [Notes] |
| [Role 2] | [High/Medium/Low] | [Notes] |

# Financial Overview
- Budget Range: [Range]
- Payment Terms: [Terms]
- Key Financial Constraints: [List]

# Next Steps
1. [Action Item 1]
2. [Action Item 2]
3. [Action Item 3]

# Additional Notes
- [Note 1]
- [Note 2]

Please ensure:
1. All sections use clear markdown formatting
2. Information is concise and actionable
3. Risks and priorities are clearly identified
4. Numbers and dates are specific where available
5. Technical requirements are detailed and clear"""
            
            # Send both PDF and prompt to Gemini
            response = self.model.generate_content([
                pdf_part,
                {"text": initial_prompt}
            ])
            
            # Store context for chat
            self.analysis_context = response.text
            
            # Clean up temporary file
            os.unlink(temp_pdf_path)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            return f"Error analyzing document: {str(e)}"
    
    def get_chat_response(self, user_message: str) -> str:
        """
        Get a response to a user question based on the document analysis.
        
        Args:
            user_message (str): The user's question
            
        Returns:
            str: AI response to the question
        """
        try:
            prompt = f"""Based on the following document analysis, please answer the user's question.
            Be specific and reference relevant parts of the analysis when possible.
            
            Document Analysis:
            {self.analysis_context}
            
            User Question: {user_message}
            
            Please provide a clear, helpful response:"""
            
            response = self.model.generate_content(prompt)
            self.chat_history.append({"user": user_message, "assistant": response.text})
            return response.text
            
        except Exception as e:
            logger.error(f"Error getting chat response: {e}")
            return f"Error generating response: {str(e)}"
    
    def get_opportunity_summary(self) -> dict:
        """
        Generate a structured summary of the opportunity.
        
        Returns:
            dict: Structured opportunity data
        """
        try:
            prompt = """
            Based on the document analysis, provide a structured analysis in JSON format with the following:
            {
                "key_findings": [list of 3-5 main findings],
                "potential_value": {
                    "financial_impact": "estimated impact",
                    "timeline": "estimated timeline",
                    "confidence": "high/medium/low"
                },
                "risk_assessment": {
                    "level": "high/medium/low",
                    "factors": [list of risk factors]
                },
                "next_steps": [ordered list of recommended actions]
            }
            """
            
            response = self.model.generate_content([
                {"text": f"Document Analysis:\n{self.analysis_context}"},
                {"text": prompt}
            ])
            
            try:
                # Attempt to parse response as JSON
                return json.loads(response.text)
            except json.JSONDecodeError:
                # Fallback structure if JSON parsing fails
                return {
                    "error": "Could not generate structured opportunity data",
                    "raw_response": response.text
                }
                
        except Exception as e:
            logger.error(f"Error generating opportunity summary: {e}")
            return {"error": str(e)} 