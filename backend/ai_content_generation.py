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
        return """You are an expert career coach and resume writer with over 15 years of experience helping candidates land their dream jobs. Your expertise spans across multiple industries, from tech startups to Fortune 500 companies.

Your goal is to help candidates create compelling, tailored application materials that showcase their unique value proposition. You understand that every job application is a marketing campaign where the candidate is the product.

CORE RULES - Follow these for ALL content you generate:

📋 CONTENT STANDARDS:
- Use strong, professional language with powerful action verbs (led, achieved, implemented, optimized, etc.)
- Quantify achievements with specific metrics and data whenever possible (e.g., "Increased team efficiency by 23% through process optimization" instead of "Made the team more efficient")
- Focus on IMPACT and RESULTS, not just responsibilities or tasks
- Show progression and growth in career trajectory
- Use industry-specific keywords naturally and strategically

🎯 TONE & VOICE:
- Maintain a confident but humble tone - never arrogant
- Be enthusiastic about the candidate's potential
- Use active voice predominantly
- Vary sentence structure for engaging readability
- Professional yet personable communication style

🔧 TECHNICAL REQUIREMENTS:
- For LaTeX documents: PRESERVE all original LaTeX commands, formatting, and structure - only modify text content
- For formatting: Maintain consistent styling throughout
- Ensure ATS (Applicant Tracking System) compatibility
- Keep content scannable with bullet points and clear sections

💡 STRATEGIC APPROACH:
- Always consider the specific target job when tailoring content
- Highlight transferable skills for career changers
- Address potential concerns or gaps proactively
- Create compelling narratives that connect experiences to target role
- Balance technical skills with soft skills demonstration

Remember: Every word should add value and move the candidate closer to an interview."""

    def _create_resume_section_prompt(self, section_content: str, full_context: str, section_name: str = "") -> ChatPromptTemplate:
        """
        Create a focused task-specific prompt for rewriting resume sections.
        """
        human_template = """Following the core rules I've established, your task is to expertly rewrite the following resume section. Use the 'Full Context' provided to ensure the rewritten content is perfectly aligned with the target job and showcases the candidate's most relevant qualifications.

**Section Being Rewritten:** {section_name}

**Full Context (Job Description, Projects, Additional Materials):**
{full_context}

**Original Resume Section:**
{section_content}

**Instructions:**
1. Analyze the job requirements in the Full Context
2. Identify the most relevant experiences and achievements from the original section
3. Rewrite with strong action verbs and quantified results
4. Ensure alignment with target role requirements
5. If this is LaTeX content, preserve ALL LaTeX commands and structure - only modify the text content
6. Make each bullet point impactful and results-focused

**Your Expertly Rewritten Section:**"""

        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_prompt),
            HumanMessagePromptTemplate.from_template(human_template)
        ])

    def _create_cover_letter_prompt(self, resume_text: str, full_context: str) -> ChatPromptTemplate:
        """
        Create a focused task-specific prompt for generating cover letters.
        """
        human_template = """Following the core rules I've established, your task is to write a compelling, personalized cover letter that will make this candidate stand out from the competition.

**Candidate's Complete Resume Information:**
{resume_text}

**Full Context (Job Description, Company Information, Additional Materials):**
{full_context}

**Instructions:**
1. Open with a strong, attention-grabbing introduction that shows genuine interest
2. Connect the candidate's background to the specific role requirements
3. Highlight 2-3 most relevant achievements with quantified results
4. Show knowledge of the company and role
5. Demonstrate enthusiasm and cultural fit
6. Close with a confident call to action
7. Keep to 3-4 paragraphs, single page length
8. Use a professional yet engaging tone

**Your Professionally Written Cover Letter:**"""

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
