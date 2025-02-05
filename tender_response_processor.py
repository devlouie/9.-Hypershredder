"""
Tender Response Processor
========================

This module handles the generation of tender responses based on opportunity analysis
and submitter context information. It provides structured, contextually aware responses
that align with tender requirements.

Key Features:
------------
1. Context-aware response generation
2. Section-specific regeneration
3. Tender structure compliance
4. Company information integration
"""

import google.generativeai as genai
import logging
from typing import Optional, Dict, List
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TenderResponseProcessor:
    """
    A class to generate tender responses incorporating company context and opportunity analysis.
    
    This class handles:
    1. Company context management
    2. Response structure enforcement
    3. Section-specific generation
    4. Context integration
    """
    
    def __init__(self, opportunity_context: str):
        """
        Initialize the tender response processor.
        
        Args:
            opportunity_context (str): The analyzed opportunity context from previous stages
        """
        self._setup_gemini()
        self.opportunity_context = opportunity_context
        
    def _setup_gemini(self):
        """Configure the Gemini AI client."""
        try:
            if not hasattr(st.secrets.api_keys, 'gemini'):
                raise ValueError("Gemini API key not found in secrets")
            
            genai.configure(api_key=st.secrets.api_keys.gemini)
            self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')
            logger.info("Gemini AI setup completed successfully")
        except Exception as e:
            logger.error(f"Error setting up Gemini AI: {e}")
            raise
            
    def _create_context_prompt(self, context: Dict) -> str:
        """
        Create a prompt incorporating company context information.
        
        Args:
            context (Dict): Company information and context
            
        Returns:
            str: Formatted context prompt
        """
        return f"""
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

    def _create_structure_prompt(self, section_name: Optional[str] = None) -> str:
        """
        Create the response structure prompt.
        
        Args:
            section_name (Optional[str]): Specific section to generate
            
        Returns:
            str: Formatted structure prompt
        """
        prompt = """Based on the tender document analysis and provided company context, generate a detailed response that follows the exact structure and requirements outlined in the tender. 

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
6. Company strengths and differentiators are highlighted appropriately"""

        if section_name:
            prompt += f"\n\nPlease generate the response ONLY for the section: {section_name}"
            
        return prompt

    def generate_response(self, context: Dict, section_name: Optional[str] = None) -> str:
        """
        Generate a tender response based on company context and opportunity analysis.
        
        Args:
            context (Dict): Company information and context
            section_name (Optional[str]): Specific section to generate
            
        Returns:
            str: Generated tender response
        """
        try:
            # Create prompts
            context_prompt = self._create_context_prompt(context)
            structure_prompt = self._create_structure_prompt(section_name)
            
            # Combine prompts
            prompts = [
                {"text": f"Opportunity Analysis:\n{self.opportunity_context}"},
                {"text": f"Company Context:\n{context_prompt}"},
                {"text": f"Response Structure:\n{structure_prompt}"}
            ]
            
            # Generate response
            response = self.model.generate_content(prompts)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating tender response: {e}")
            return f"Error generating tender response: {str(e)}"
            
    def validate_context(self, context: Dict) -> bool:
        """
        Validate that the required context information is provided.
        
        Args:
            context (Dict): Company information and context
            
        Returns:
            bool: True if context is valid, False otherwise
        """
        required_fields = ['company_name', 'company_website', 'company_description']
        return all(context.get(field) for field in required_fields) 