"""
ai_content_generation.py

Phase 2: AI-Powered Content Generation with Hierarchical Prompting
Implements two-tiered prompting strategy using LangChain and Gemini API.
"""

import os
from typing import Dict, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger("uvicorn.error")

class AIContentGenerator:
    """
    Hierarchical prompting system for AI-powered content generation.
    Uses a two-tiered approach: System Prompt + Task-Specific Prompts.
    """
    
    def __init__(self):
        """Initialize the AI content generator with Gemini API."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found. AI content generation will be disabled.")
            self.llm = None
            self.output_parser = None
            self.system_prompt = None
            return
        
        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=self.api_key,
            temperature=0.7,
            max_tokens=8000
        )
        
        # Output parser
        self.output_parser = StrOutputParser()
        
        # Core system prompt (meta-prompt sent with every request)
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """
        Define the core AI persona and rules (System Prompt).
        This master "meta-prompt" sets global rules for the AI.
        """
        return """You are an expert LaTeX resume assistant and career strategist with extensive experience in professional document creation across multiple industries.

Your goal is to create concise, impactful, and professionally tailored application materials that present candidates in the most compelling way possible.

CORE RULES - Follow these for ALL content you generate:

📋 CONTENT STANDARDS:
- Use professional, formal tone with simple, clear, and pleasant language
- Be concise and straightforward - every bullet should be short, precise, and easy to read
- Convey necessary information using the simplest effective wording
- Focus on RESULTS and quantified achievements when possible
- Reuse and intelligently adapt existing content to fit target requirements
- Do not overwhelm the reader with excessive detail

🎯 STRATEGIC APPROACH:
- Assume the role of an expert in the target job's field
- Evaluate and represent candidate's experience with precision and intelligence
- Add new sections only if contextually supported by job requirements
- Remove irrelevant sections while maintaining consistent formatting
- Tailor content specifically for the target role and company

🔧 TECHNICAL REQUIREMENTS:
- For LaTeX: ALWAYS maintain valid and minimal LaTeX structure
- Preserve contact section format and all LaTeX commands
- Ensure consistent formatting across all sections
- Structure sections logically: custom sections first, Experience, Projects, Certifications (if applicable), Education second to last, Skills at the end
- Return ONLY final code without explanations or commentary

💡 QUALITY PRINCIPLES:
- Every sentence should be thoughtful and informative yet concise
- Use industry-appropriate terminology naturally
- Maintain ATS compatibility with hkeyword useage efficiently and precisely.
- Focus on clarity and readability above all else

Remember: Professional precision with maximum clarity and minimum complexity."""

    def _create_resume_section_prompt(self, section_content: str, full_context: str, section_name: str = "") -> ChatPromptTemplate:
        """
        Create a focused task-specific prompt for rewriting resume sections.
        """
        human_template = """Following the core rules established, rewrite the specified resume section with professional precision and clarity.

**Section Being Rewritten:** {section_name}

**Full Context (Job Description, Requirements, Additional Materials):**
{full_context}

**Original Resume Section:**
{section_content}

**Instructions:**
1. Analyze target role requirements from the Full Context
2. Intelligently adapt and reuse content from the original section
3. Use concise, professional language - every bullet should be short and precise
4. Focus on relevant achievements and results
5. Preserve ALL LaTeX commands and structure if applicable
6. Remove irrelevant information, add contextually supported content
7. Ensure consistent formatting and logical flow

**Your Rewritten Section (code only, no explanations):**"""

        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_prompt),
            HumanMessagePromptTemplate.from_template(human_template)
        ])

    def _create_cover_letter_prompt(self, resume_text: str, full_context: str) -> ChatPromptTemplate:
        """
        Create a focused task-specific prompt for generating cover letters.
        """
        human_template = """Following the core rules established, create a professional, concise cover letter that effectively connects the candidate to the target opportunity.

**Candidate's Resume Information:**
{resume_text}

**Full Context (Job Description, Company Information, Role Requirements):**
{full_context}

**Instructions:**
1. Write in professional, formal tone with clear, pleasant language
2. Be concise and straightforward cold toen yet respectful- avoid overwhelming detail
3. Connect candidate's background directly to role requirements
4. Highlight 2-3 most relevant achievements with specific results
5. Show understanding of company and position
6. Keep to 1 or 2 short paragraphs, single page with bullet points achievements in F pattern making easy to read 
7. Use simple, effective wording throughout
8. Close with confident, professional call to action

**Your Professional Cover Letter (final version only, no explanations):**"""

        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_prompt),
            HumanMessagePromptTemplate.from_template(human_template)
        ])

    async def rewrite_resume_section(self, section_content: str, full_context: str, section_name: str = "") -> str:
        """
        Rewrite a specific resume section using hierarchical prompting.
        
        Args:
            section_content: The original content of the resume section
            full_context: Job description, projects, and other context
            section_name: Name of the section being rewritten (e.g., "Experience", "Education")
        
        Returns:
            AI-generated rewritten section content
        """
        if not self.llm:
            logger.warning("AI content generation disabled - returning original content")
            return section_content
            
        try:
            # Create the chain
            prompt = self._create_resume_section_prompt(section_content, full_context, section_name)
            chain = prompt | self.llm | self.output_parser
            
            # Execute the chain
            result = await chain.ainvoke({
                "section_content": section_content,
                "full_context": full_context,
                "section_name": section_name or "Resume Section"
            })
            
            logger.info(f"Successfully rewrote resume section: {section_name}")
            return result.strip()
            
        except Exception as e:
            logger.error(f"Error rewriting resume section {section_name}: {str(e)}")
            raise

    async def generate_cover_letter(self, resume_text: str, full_context: str) -> str:
        """
        Generate a complete cover letter using hierarchical prompting.
        
        Args:
            resume_text: The candidate's complete resume text
            full_context: Job description, company info, and other context
        
        Returns:
            AI-generated cover letter
        """
        if not self.llm:
            logger.warning("AI content generation disabled - returning default cover letter")
            return f"Dear Hiring Manager,\n\nI am writing to express my interest in the position. Please find my resume attached for your consideration.\n\nBest regards,\n[Your Name]"
            
        try:
            # Create the chain
            prompt = self._create_cover_letter_prompt(resume_text, full_context)
            chain = prompt | self.llm | self.output_parser
            
            # Execute the chain
            result = await chain.ainvoke({
                "resume_text": resume_text,
                "full_context": full_context
            })
            
            logger.info("Successfully generated cover letter")
            return result.strip()
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            raise

    async def process_latex_resume(self, tex_sections: Dict[str, str], full_context: str) -> Dict[str, str]:
        """
        Process a LaTeX resume by rewriting each relevant section.
        
        Args:
            tex_sections: Dictionary mapping section names to LaTeX content
            full_context: Job description and additional context
        
        Returns:
            Dictionary with rewritten sections
        """
        if not self.llm:
            logger.warning("AI content generation disabled - returning original sections")
            return tex_sections
            
        rewritten_sections = {}
        
        # Define sections that should be processed
        processable_sections = [
            'experience', 'work experience', 'professional experience',
            'education', 'skills', 'technical skills', 'projects',
            'achievements', 'accomplishments', 'summary', 'objective'
        ]
        
        for section_name, content in tex_sections.items():
            # Check if this section should be processed
            if any(keyword in section_name.lower() for keyword in processable_sections):
                logger.info(f"Processing LaTeX section: {section_name}")
                rewritten_content = await self.rewrite_resume_section(
                    content, full_context, section_name
                )
                rewritten_sections[section_name] = rewritten_content
            else:
                # Keep original content for non-processable sections
                rewritten_sections[section_name] = content
        
        return rewritten_sections

    async def process_pdf_resume(self, resume_text: str, full_context: str) -> str:
        """
        Process a PDF resume by generating an improved version.
        
        Args:
            resume_text: Extracted text from PDF resume
            full_context: Job description and additional context
        
        Returns:
            Improved resume content
        """
        try:
            # For PDF resumes, we treat the entire content as one section
            improved_resume = await self.rewrite_resume_section(
                resume_text, full_context, "Complete Resume"
            )
            
            logger.info("Successfully processed PDF resume")
            return improved_resume
            
        except Exception as e:
            logger.error(f"Error processing PDF resume: {str(e)}")
            raise


# Singleton instance for the application
ai_generator = AIContentGenerator()