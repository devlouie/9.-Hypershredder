"""
Opportunity Dashboard Processor
==============================

This module handles the interaction between the compiled PDF documents and Google's
Gemini AI model to provide intelligent insights and opportunity analysis.

Key Features:
------------
1. PDF context processing
2. Gemini AI integration
3. Opportunity extraction and analysis
4. Interactive chat capabilities
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

class OpportunityDashboardProcessor:
    """
    A class to process documents and interact with Gemini AI for opportunity analysis.
    
    This class handles:
    1. Setting up Gemini AI connection
    2. Processing PDF content
    3. Generating insights and opportunities
    4. Managing chat interactions
    """
    
    def __init__(self):
        self._setup_gemini()
        self.chat_history = []
        self.context = ""
        self.max_text_length = 30000
        self.pdf_info = None  # Store PDF metadata for UI
        
    def _setup_gemini(self):
        """Configure the Gemini AI client with enhanced model selection."""
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

    def process_pdf_context(self, pdf_content: bytes) -> str:
        """Process the PDF content and extract relevant information."""
        try:
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

# Who is need to make this happen?
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
5. Technical requirements are detailed and clear

Begin your analysis:"""
            
            # Send PDF and prompt to Gemini
            response = self.model.generate_content([
                pdf_part,
                {"text": initial_prompt}
            ])
            
            # Store context and add system message about PDF attachment
            self.context = response.text
            self.chat_history.append({
                "role": "system",
                "content": f"📎 PDF Document attached ({self.pdf_info.get('pages', '?')} pages, {self.pdf_info.get('size', '?')})"
            })
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error processing PDF context: {e}")
            return f"Error analyzing document: {str(e)}"
    
    def get_chat_response(self, user_message: str) -> str:
        """Get a response from Gemini based on user input and document context."""
        try:
            if not self.pdf_info:
                raise ValueError("No PDF document is attached to this conversation")

            # Create PDF part for each interaction
            pdf_part = {
                "mime_type": "application/pdf",
                "data": st.session_state.compiled_pdf
            }

            prompt = f"""Based on the attached PDF document and the following analysis, please answer the user's question.
            Be specific and reference relevant parts of both the PDF and analysis when possible.
            When referencing the PDF, please include page numbers where applicable.
            
            Document Analysis:
            {self.context}
            
            User Question: {user_message}
            
            Please provide a clear, helpful response that directly references relevant sections from the PDF document:"""
            
            # Send PDF and prompt to Gemini
            response = self.model.generate_content([
                pdf_part,
                {"text": prompt}
            ])
            
            # Add messages to chat history
            self.chat_history.append({"role": "user", "content": user_message})
            self.chat_history.append({"role": "assistant", "content": response.text})
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error getting chat response: {e}")
            return f"Error generating response: {str(e)}"
    
    def get_pdf_status(self) -> Dict:
        """Get current PDF attachment status for UI display."""
        if not self.pdf_info:
            return {
                "attached": False,
                "message": "No PDF document attached"
            }
        
        return {
            "attached": True,
            "message": f"📎 PDF Document ({self.pdf_info.get('pages', '?')} pages, {self.pdf_info.get('size', '?')})",
            "timestamp": self.pdf_info.get('timestamp', '')
        }
    
    def get_opportunity_summary(self) -> dict:
        """
        Generate a structured summary of opportunities from the document context.
        
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
                {"text": f"Document Analysis:\n{self.context}"},
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
            
    def generate_contextual_response(self) -> str:
        """
        Generate a contextually aware response based on the compiled PDF and initial analysis.
        This response follows the structure from the user's first response format.
        
        Returns:
            str: A structured markdown response
        """
        try:
            prompt = """Based on the compiled PDF and the previous analysis, generate a comprehensive response that builds upon our understanding. 
            Focus on providing actionable insights and strategic recommendations.

Structure your response using this exact markdown format:

# Strategic Overview
[Provide a strategic assessment of the opportunity, incorporating key findings from the initial analysis]

# Competitive Analysis
## Our Strengths
- [Strength 1 with specific relevance to this opportunity]
- [Strength 2 with specific relevance to this opportunity]

## Market Position
- [Current market dynamics]
- [Our positioning]
- [Key differentiators]

# Resource Requirements
## Team Composition
| Role | Required Skills | Availability |
|------|----------------|--------------|
| [Role 1] | [Skills] | [Timeline] |
| [Role 2] | [Skills] | [Timeline] |

## Technical Stack
- [Required technology 1]: [Purpose/Justification]
- [Required technology 2]: [Purpose/Justification]

# Implementation Strategy
1. [Phase 1]: [Description]
   - Key Activities
   - Timeline
   - Dependencies
2. [Phase 2]: [Description]
   - Key Activities
   - Timeline
   - Dependencies

# Risk Mitigation Updates
| Risk Category | Identified Risks | Mitigation Strategy | Status |
|--------------|------------------|---------------------|--------|
| [Category 1] | [Risks] | [Strategy] | [Status] |
| [Category 2] | [Risks] | [Strategy] | [Status] |

# Success Metrics
## Key Performance Indicators
1. [KPI 1]
   - Target: [Specific target]
   - Measurement: [How it will be measured]
2. [KPI 2]
   - Target: [Specific target]
   - Measurement: [How it will be measured]

# Budget Allocation
## Cost Breakdown
| Category | Estimated Cost | Notes |
|----------|---------------|-------|
| [Category 1] | [Amount] | [Notes] |
| [Category 2] | [Amount] | [Notes] |

# Recommendations
1. [Primary Recommendation]
   - Justification
   - Expected Impact
2. [Secondary Recommendation]
   - Justification
   - Expected Impact

# Action Items
## Immediate (Next 2 Weeks)
- [ ] [Action 1]
- [ ] [Action 2]

## Short Term (Next 30 Days)
- [ ] [Action 1]
- [ ] [Action 2]

## Long Term (Next Quarter)
- [ ] [Action 1]
- [ ] [Action 2]

Please ensure:
1. All recommendations are data-driven and tied to specific findings
2. Action items are specific, measurable, and time-bound
3. Risk assessments include both probability and impact
4. Resource requirements are realistic and well-justified
5. Success metrics are quantifiable where possible

Begin your analysis:"""

            response = self.model.generate_content([
                {"text": f"Previous Analysis:\n{self.context}"},
                {"text": prompt}
            ])
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return f"Error generating contextual response: {str(e)}" 

    def generate_tender_response(self, section_name: Optional[str] = None, context: Optional[Dict] = None) -> str:
        """
        Generate a contextually aware response based on the tender document structure.
        
        Args:
            section_name (Optional[str]): Specific section to generate response for.
                                        If None, generates response for all sections.
            context (Optional[Dict]): Submitter context information including company details,
                                    past performance, and differentiators.
            
        Returns:
            str: Structured response following tender document format
        """
        try:
            # Create context prompt from submitter information
            context_prompt = ""
            if context:
                context_prompt = f"""
Use the following company information to personalize and contextualize the response:

Company Profile:
- Name: {context.get('company_name', 'N/A')}
- Website: {context.get('company_website', 'N/A')}
- Description: {context.get('company_description', 'N/A')}

Key Differentiators:
{context.get('key_differentiators', 'N/A')}

Past Performance:
{context.get('past_performance', 'N/A')}

Certifications & Compliance:
{context.get('certifications', 'N/A')}

Please incorporate this information naturally throughout the response, especially in relevant sections like company introduction, past performance, and technical capabilities.
"""

            # Define the response structure prompt
            structure_prompt = """Based on the tender document analysis and provided company context, generate a detailed response that follows the exact structure and requirements outlined in the tender. 

Your response should:
1. Directly address each requirement point by point
2. Use the same section numbering and hierarchy as the original tender
3. Include all mandatory forms and declarations
4. Follow any specific formatting requirements
5. Address evaluation criteria explicitly
6. Incorporate the provided company information naturally
7. Highlight relevant past performance and certifications
8. Emphasize key differentiators in appropriate sections

Structure the response as follows:

# 1. Executive Overview
- Company introduction (using provided company description)
- Understanding of requirements
- Value proposition (incorporating key differentiators)
- Unique capabilities and experience

# 2. Technical Response
## 2.1 Methodology
- Approach overview
- Project phases
- Quality assurance
- Risk management

## 2.2 Technical Compliance
- Point-by-point compliance matrix
- Technical specifications
- Standards adherence (referencing relevant certifications)
- Integration approach

# 3. Implementation Plan
- Project timeline
- Resource allocation
- Milestones
- Deliverables schedule

# 4. Team Structure
- Key personnel
- Roles and responsibilities
- Relevant experience
- Certifications and qualifications

# 5. Past Performance
- Similar projects (from provided past performance)
- Client references
- Success metrics
- Lessons learned

# 6. Commercial Terms
- Pricing structure
- Payment schedule
- Commercial compliance
- Terms and conditions

# 7. Value Added
- Innovation aspects (from key differentiators)
- Additional benefits
- Future roadmap
- Strategic alignment

Please ensure:
1. All responses are evidence-based and reference provided company information
2. Claims are substantiated with examples from past performance
3. Language matches the tender's tone
4. All mandatory requirements are addressed
5. Evaluation criteria are explicitly met
6. Company strengths and differentiators are highlighted appropriately

Using the context from the tender document and company information, generate a response that follows this structure:"""

            # If a specific section is requested, modify the prompt
            if section_name:
                structure_prompt += f"\n\nPlease generate the response ONLY for the section: {section_name}"

            # Combine prompts and send to Gemini
            prompts = [
                {"text": f"Document Analysis:\n{self.context}"}
            ]
            
            if context:
                prompts.append({"text": f"Company Context:\n{context_prompt}"})
                
            prompts.append({"text": structure_prompt})
            
            response = self.model.generate_content(prompts)

            return response.text

        except Exception as e:
            logger.error(f"Error generating tender response: {e}")
            return f"Error generating tender response: {str(e)}"