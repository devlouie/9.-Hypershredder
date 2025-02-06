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
import datetime

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
        """Initialize the opportunity analyzer with enhanced chat capabilities."""
        self._setup_gemini()
        # Initialize chat session
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "context" not in st.session_state:
            st.session_state.context = ""
        if "analysis_complete" not in st.session_state:
            st.session_state.analysis_complete = False
        self.max_text_length = 30000
        self.pdf_info = None
        
    def _setup_gemini(self):
        """Configure the Gemini AI client with enhanced chat capabilities."""
        try:
            if not hasattr(st.secrets.api_keys, 'gemini'):
                raise ValueError("Gemini API key not found in secrets")
            
            genai.configure(api_key=st.secrets.api_keys.gemini)
            # Initialize model with specific configuration
            self.model = genai.GenerativeModel(
                model_name='gemini-2.0-flash-thinking-exp-01-21',
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.8,
                    'top_k': 40
                },
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            )
            logger.info("Gemini AI setup completed successfully")
        except Exception as e:
            logger.error(f"Error setting up Gemini AI: {e}")
            raise

    def _format_chat_message(self, role: str, content: str) -> dict:
        """Format chat messages consistently."""
        return {
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        }

    def _get_chat_context(self) -> str:
        """Generate a context string from PDF analysis and chat history."""
        context_parts = []
        
        # Add PDF information if available
        if self.pdf_info:
            context_parts.append(f"Document Context: {self.pdf_info.get('pages', '?')} pages document")
        
        # Add recent chat context (last 5 messages)
        if st.session_state.chat_history:
            recent_messages = st.session_state.chat_history[-5:]
            chat_context = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in recent_messages
            ])
            context_parts.append(f"Recent Conversation:\n{chat_context}")
        
        # Add analysis context if available
        if st.session_state.context:
            context_parts.append(f"Analysis Context:\n{st.session_state.context}")
        
        return "\n\n".join(context_parts)

    def analyze_document(self, pdf_content: bytes) -> str:
        """Analyze the PDF content and extract relevant information."""
        try:
            # If analysis is already complete, return the stored analysis
            if st.session_state.analysis_complete and st.session_state.context:
                return st.session_state.context

            # Store PDF metadata for UI
            self.pdf_info = self._get_pdf_metadata(pdf_content)
            
            # Create PDF part for Gemini
            pdf_part = {
                "mime_type": "application/pdf",
                "data": pdf_content
            }

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
            
            # Send PDF and prompt to Gemini
            response = self.model.generate_content([
                pdf_part,
                {"text": initial_prompt}
            ])
            
            # Store analysis in session state
            st.session_state.context = response.text
            st.session_state.analysis_complete = True
            
            # Add system message about PDF attachment
            system_msg = self._format_chat_message(
                "system",
                f"Document attached ({self.pdf_info.get('pages', '?')} pages, {self.pdf_info.get('size', '?')})"
            )
            st.session_state.chat_history.append(system_msg)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            return f"Error analyzing document: {str(e)}"

    def get_chat_response(self, user_message: str) -> str:
        """Enhanced chat response generation with context awareness."""
        try:
            if not self.pdf_info:
                raise ValueError("No document is attached to this conversation")

            # Create PDF part for context
            pdf_part = {
                "mime_type": "application/pdf",
                "data": st.session_state.compiled_pdf
            }

            # Build comprehensive prompt with context
            chat_context = self._get_chat_context()
            prompt = f"""As an expert business analyst, provide a response based on the following context:

Context:
{chat_context}

Current Question: {user_message}

Guidelines for response:
1. Reference specific sections or pages from the document when relevant
2. Maintain consistency with previous responses in the conversation
3. Provide concrete examples or evidence from the document
4. Be concise but thorough
5. If information is not found in the document, clearly state that

Please provide your response:"""

            # Generate response using both PDF and context
            response = self.model.generate_content([
                pdf_part,
                {"text": prompt}
            ])
            
            # Format and store messages
            user_msg = self._format_chat_message("user", user_message)
            assistant_msg = self._format_chat_message("assistant", response.text)
            
            # Update session state
            st.session_state.chat_history.extend([user_msg, assistant_msg])
            
            # Log interaction for debugging
            logger.info(f"Chat interaction completed: {len(st.session_state.chat_history)} messages in history")
            
            return response.text
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def clear_chat_history(self):
        """Clear the chat history while maintaining document context."""
        st.session_state.chat_history = []
        if self.pdf_info:
            # Add system message about attached document
            system_msg = self._format_chat_message(
                "system", 
                f"Document attached ({self.pdf_info.get('pages', '?')} pages, {self.pdf_info.get('size', '?')})"
            )
            st.session_state.chat_history.append(system_msg)

    def get_chat_history(self) -> List[Dict]:
        """Get formatted chat history for display."""
        return st.session_state.chat_history

    def get_pdf_status(self) -> Dict:
        """Get current PDF attachment status for UI display."""
        if not self.pdf_info:
            return {
                "attached": False,
                "message": "No document attached"
            }
        
        return {
            "attached": True,
            "message": f"📎 Document ({self.pdf_info.get('pages', '?')} pages, {self.pdf_info.get('size', '?')})",
            "timestamp": self.pdf_info.get('timestamp', '')
        }

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
                {"text": f"Document Analysis:\n{st.session_state.context}"},
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

    def _get_pdf_metadata(self, pdf_content: bytes) -> Dict:
        """Extract basic PDF metadata for display."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf.write(pdf_content)
                temp_pdf_path = temp_pdf.name
                
                reader = PyPDF2.PdfReader(temp_pdf_path)
                metadata = {
                    "pages": len(reader.pages),
                    "size": f"{len(pdf_content) / 1024:.1f} KB",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                os.unlink(temp_pdf_path)
                return metadata
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}")
            return {} 