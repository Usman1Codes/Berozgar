import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import asyncio

# Load environment variables
load_dotenv()

logger = logging.getLogger("uvicorn.error")

# Initialize Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.warning("GOOGLE_API_KEY not found. LaTeX resume generation will be disabled.")
else:
    genai.configure(api_key=api_key)

def load_file(file_path: str) -> str:
    """
    Load content from a file (template or prompt).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug(f"Loaded file from {file_path}")
        return content
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise

async def generate_latex_resume(resume_text: str, template_path: str, prompt_path: str) -> str:
    """
    Generate a LaTeX resume by filling a template with content from resume text using Gemini directly.
    """
    if not api_key:
        logger.warning("LaTeX resume generation disabled - returning empty LaTeX content")
        return ""

    try:
        # Load the LaTeX template and prompt
        template_content = load_file(template_path)
        prompt_template = load_file(prompt_path)

        # Format the prompt with inputs
        prompt = prompt_template.format(
            resume_text=resume_text,
            template_content=template_content
        )

        # Initialize Gemini model
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 20000
            }
        )

        # Generate content
        response = await asyncio.to_thread(model.generate_content, prompt)
        result = response.text.strip()

        logger.info("Successfully generated LaTeX resume")
        return result
    except Exception as e:
        logger.error(f"Error generating LaTeX resume: {str(e)}")
        raise