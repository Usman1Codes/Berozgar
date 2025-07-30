import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger("uvicorn.error")

# Initialize LLM
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.warning("GOOGLE_API_KEY not found. AI content generation will be disabled.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=api_key,
    temperature=0.7,
    max_tokens=20000
) if api_key else None

# System prompt
system_prompt = """You are an expert resume assistant and career strategist.

Using the attached resume and all available context (job description, experience, project details), generate a fully updated, professionally tailored resume for the role described in job description".

Follow these strict guidelines:

📋 CONTENT STANDARDS:
- Use a professional, formal tone with simple, clear, and pleasant language.
- Be concise and straightforward—every bullet or sentence should be short, precise, and easy to read, yet thoughtful and informative.
- Focus on impact and achievements; include metrics and quantified outcomes wherever possible.
- Avoid unnecessary detail. Convey only what’s essential and compelling using the simplest effective wording.
- Reuse and intelligently adapt content from the attached resume to reflect the target role more effectively.

📂 SOURCE PRIORITY:
- Prioritize the content in the attached resume/document as the primary data source.
- Cross-reference with the job description to identify gaps, align language, and enhance relevance.
- Only introduce new content if it is clearly supported by the candidate’s background or the job requirements.

🎯 STRATEGIC APPROACH:
- Assume the role of an expert in the target job’s field to evaluate and represent the candidate's experience with clarity and depth.
- Tailor content specifically for the target role and company.
- Add new sections only when contextually necessary and remove irrelevant or outdated material.
- Maintain consistent formatting, tone, and section structure.
- Always include content which has hifh relevane to the JD 

🧠 ATS OPTIMIZATION:
- Ensure full ATS (Applicant Tracking System) compatibility.
- Match terminology and phrasing to the job description for optimal keyword alignment.
- Embed relevant keywords naturally without stuffing.
- Use clean formatting and conventional section labels that are easily parsed by ATS tools.

📌 STRUCTURE & ORDER:
- Arrange sections in this logical order unless the role demands otherwise: Custom sections (if applicable), Experience, Projects, Certifications (if any), Education, Skills.
- Ensure clean grouping and a coherent flow of information.

💼 OUTPUT FORMAT:
- Return ONLY the final, updated resume content as plain text.
- DO NOT include LaTeX, markdown, explanations, or commentary of any kind.

💡 QUALITY PRINCIPLES:
- Every sentence must add value—precise, contextual, and relevant.
- Use industry-specific terminology authentically and appropriately.
- Prioritize clarity, strategic alignment, and readability in every section.
"""

def load_prompt_template(prompt_file: str) -> str:
    """
    Load a prompt template from the prompts/ directory.
    """
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", prompt_file)
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
            logger.debug(f"Loaded prompt template from {prompt_path}")
            return prompt_content
    except FileNotFoundError:
        logger.error(f"Prompt file {prompt_path} not found")
        raise

async def rewrite_resume(resume_text: str, context_text: str) -> str:
    """
    Rewrite a resume using plain text input and LCEL chain.
    """
    if not llm:
        logger.warning("AI content generation disabled - returning original resume text")
        return resume_text

    try:
        logger.debug(f"Resume text: {resume_text[:100]}...")
        logger.debug(f"Context text: {context_text[:100]}...")

        # Load prompt and create chain
        prompt_template = load_prompt_template("resume_section_prompt.txt")
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            ("human", prompt_template)
        ])
        chain = prompt | llm | StrOutputParser()

        # Execute chain
        result = await chain.ainvoke({
            "section_name": "Resume",
            "section_content": resume_text,
            "full_context": context_text
        })

        logger.info("Successfully rewrote resume")
        return result.strip()
    except Exception as e:
        logger.error(f"Error rewriting resume: {str(e)}")
        raise

async def generate_cover_letter(resume_text: str, context_text: str) -> str:
    """
    Generate a cover letter using plain text input and LCEL chain.
    """
    if not llm:
        logger.warning("AI content generation disabled - returning default cover letter")
        return """Dear Hiring Manager,
I am writing to express my interest in the position. Please find my resume attached.
Best regards,
[Your Name]"""

    try:
        logger.debug(f"Resume text for cover letter: {resume_text[:100]}...")
        logger.debug(f"Context text for cover letter: {context_text[:100]}...")

        prompt_template = load_prompt_template("cover_letter_prompt.txt")
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            ("human", prompt_template)
        ])
        chain = prompt | llm | StrOutputParser()

        result = await chain.ainvoke({
            "resume_text": resume_text,
            "full_context": context_text
        })

        logger.info("Successfully generated cover letter")
        return result.strip()
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        raise