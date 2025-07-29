from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from typing import List, Dict
import logging
import re
import requests
from bs4 import BeautifulSoup
from fastapi import Body

from nlp_pipeline import aggregate_context, parse_tex_sections, parse_pdf_resume
from ai_content_generation import ai_generator

# Load environment variables from .env
load_dotenv()

# Create local tmp directory for uploads
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(BASE_DIR, "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

# Logger setup
logger = logging.getLogger("uvicorn.error")

# Ensure job_description_text.txt exists so it can be overwritten on each submission
jd_text_default_path = os.path.join(TMP_DIR, "job_description_text.txt")
if not os.path.exists(jd_text_default_path):
    with open(jd_text_default_path, "w", encoding="utf-8") as f:
        pass
logger.info(f"Ensured job description text file exists at {jd_text_default_path}")

def reconstruct_latex_file(original_latex_path: str, parsed_sections: Dict[str, str], improved_sections: Dict[str, str]) -> str:
    """
    Reconstructs a LaTeX file by replacing the content of specified sections with improved versions.

    This function reads a LaTeX file, iterates through sections that have been parsed, and replaces
    their original content with AI-generated improvements. It uses regular expressions for robust,
    in-place replacement to preserve the overall LaTeX structure.

    Args:
        original_latex_path: The file path to the original LaTeX resume.
        parsed_sections: A dictionary where keys are section names and values are the original,
                         extracted text content of those sections.
        improved_sections: A dictionary containing the AI-improved text for one or more sections.

    Returns:
        The full content of the LaTeX file with the sections replaced.
    """
    try:
        with open(original_latex_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except FileNotFoundError:
        logger.error(f"Error: Original LaTeX file not found at {original_latex_path}")
        return ""

    modified_content = original_content
    for section_name, original_section_content in parsed_sections.items():
        if section_name in improved_sections:
            improved_section_content = improved_sections[section_name]

            if not original_section_content.strip():
                logger.warning(f"Skipping replacement for section '{section_name}' because original content is empty.")
                continue

            try:
                # Use regex for a more robust replacement. Escape special regex characters in the original content.
                # The `re.DOTALL` flag allows `.` to match newlines, which is crucial for multi-line section content.
                pattern = re.compile(re.escape(original_section_content), re.DOTALL)

                if pattern.search(modified_content):
                    modified_content = pattern.sub(improved_section_content, modified_content, count=1)
                    logger.info(f"Successfully replaced section: {section_name}")
                else:
                    logger.warning(f"Could not find the exact text for section '{section_name}' in the resume. Skipping replacement.")

            except re.error as e:
                logger.error(f"Regex error while replacing section '{section_name}': {e}")

    return modified_content

app = FastAPI(
    title="Resume Tool Backend",
    description="API for processing resumes, job descriptions, and generating tailored documents",
    version="0.1.0"
)

# Allow CORS from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/jd_from_url")
async def jd_from_url(url: str = Body(..., embed=True)):
    """
    Accepts a URL, fetches its HTML, and saves it as a .txt file in tmp.
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html_content = response.text
        # Parse HTML and extract text
        soup = BeautifulSoup(html_content, "html.parser")
        elements = soup.find_all(["p", "li"])
        page_text = "\n\n".join(el.get_text(strip=True) for el in elements)
        filename = "job_description_url.txt"
        filepath = os.path.join(TMP_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(page_text)
        logger.info(f"Saved job description from URL {url} to {filepath}")
        return {"status": "ok", "jd_file": filename, "tmp_dir": TMP_DIR}
    except Exception as e:
        logger.error(f"Failed to fetch or save job description from URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch or save job description from URL.")

@app.post("/api/submit")
async def submit(
    resume_files: List[UploadFile] = File(...),
    exp_files: List[UploadFile] = File(None),
    readme_files: List[UploadFile] = File(None),
    jd_text: str = Form(None),
    jd_file: UploadFile = File(None)
):
    """
    Endpoint for handling submission including job description via text, file, or url.
    """
    logger.info(f"TMP_DIR: {TMP_DIR}")
    logger.info(f"Received resume_files: {[rf.filename for rf in resume_files]}")
    saved = []
    exp_saved: List[str] = []
    readme_saved: List[str] = []
    jd_saved: List[str] = []

    # Handle job description
    if jd_text:
        jd_txt_path = os.path.join(TMP_DIR, "job_description_text.txt")
        with open(jd_txt_path, "w", encoding="utf-8") as f:
            f.write(jd_text)
        jd_saved.append("job_description_text.txt")
        logger.info(f"Saved job description text to {jd_txt_path}")
    elif jd_file:
        jd_file_path = os.path.join(TMP_DIR, jd_file.filename)
        with open(jd_file_path, "wb") as f:
            content_jd = await jd_file.read()
            f.write(content_jd)
        jd_saved.append(jd_file.filename)
        logger.info(f"Saved job description file {jd_file.filename} to {jd_file_path}")
    elif os.path.exists(os.path.join(TMP_DIR, "job_description_url.txt")):
        jd_saved.append("job_description_url.txt")
        logger.info("Using existing job description from URL.")

    # Handle supporting files
    if exp_files:
        for ef in exp_files:
            exp_path = os.path.join(TMP_DIR, ef.filename)
            with open(exp_path, "wb") as f:
                content2 = await ef.read()
                f.write(content2)
            exp_saved.append(ef.filename)
            logger.info(f"Saved experience file {ef.filename} to {exp_path}")
    if readme_files:
        for rf2 in readme_files:
            readme_path = os.path.join(TMP_DIR, rf2.filename)
            with open(readme_path, "wb") as f:
                content3 = await rf2.read()
                f.write(content3)
            readme_saved.append(rf2.filename)
            logger.info(f"Saved readme file {rf2.filename} to {readme_path}")

    # Handle resume files
    for rf in resume_files:
        path = os.path.join(TMP_DIR, rf.filename)
        with open(path, "wb") as f:
            content = await rf.read()
            f.write(content)
        saved.append(rf.filename)
        logger.info(f"Saved {rf.filename} to {path}")

    # NLP pipeline processing
    try:
        full_context = aggregate_context(TMP_DIR)
        parsed_resumes = {}
        for fname in saved:
            ext = os.path.splitext(fname)[1].lower()
            path = os.path.join(TMP_DIR, fname)
            if ext == ".tex":
                parsed_resumes[fname] = parse_tex_sections(path)
            else:
                parsed_resumes[fname] = parse_pdf_resume(path)
    except Exception as e:
        logger.error(f"NLP pipeline processing failed: {e}")
        raise HTTPException(status_code=500, detail="NLP pipeline processing failed.")

    # AI Content Generation Pipeline
    ai_generated_files = []
    try:
        logger.info("Starting AI content generation pipeline...")
        for fname in saved:
            ext = os.path.splitext(fname)[1].lower()
            base_name = os.path.splitext(fname)[0]

            if ext == ".tex":
                logger.info(f"Processing LaTeX resume: {fname}")
                tex_sections = parsed_resumes[fname]
                improved_sections = await ai_generator.process_latex_resume(tex_sections, full_context)
                improved_latex_content = reconstruct_latex_file(
                    os.path.join(TMP_DIR, fname), tex_sections, improved_sections
                )
                improved_latex_filename = f"{base_name}_ai_improved.tex"
                improved_latex_path = os.path.join(TMP_DIR, improved_latex_filename)
                with open(improved_latex_path, "w", encoding="utf-8") as f:
                    f.write(improved_latex_content)
                ai_generated_files.append(improved_latex_filename)
                logger.info(f"Saved improved LaTeX resume: {improved_latex_filename}")

            elif ext == ".pdf":
                logger.info(f"Processing PDF resume: {fname}")
                resume_text = parsed_resumes[fname]
                improved_resume = await ai_generator.process_pdf_resume(resume_text, full_context)
                improved_resume_filename = f"{base_name}_ai_improved.txt"
                improved_resume_path = os.path.join(TMP_DIR, improved_resume_filename)
                with open(improved_resume_path, "w", encoding="utf-8") as f:
                    f.write(improved_resume)
                ai_generated_files.append(improved_resume_filename)
                logger.info(f"Saved improved PDF resume content: {improved_resume_filename}")

        if saved:
            logger.info("Generating cover letter...")
            first_resume_fname = saved[0]
            parsed_resume_data = parsed_resumes[first_resume_fname]
            if isinstance(parsed_resume_data, dict):
                resume_text_for_cover = "\n\n".join(f"**{k}:**\n{v}" for k, v in parsed_resume_data.items())
            else:
                resume_text_for_cover = parsed_resume_data
            cover_letter = await ai_generator.generate_cover_letter(resume_text_for_cover, full_context)
            cover_letter_filename = "ai_generated_cover_letter.txt"
            cover_letter_path = os.path.join(TMP_DIR, cover_letter_filename)
            with open(cover_letter_path, "w", encoding="utf-8") as f:
                f.write(cover_letter)
            ai_generated_files.append(cover_letter_filename)
            logger.info(f"Saved cover letter: {cover_letter_filename}")
        
        logger.info(f"AI content generation completed. Generated files: {ai_generated_files}")

    except Exception as e:
        logger.error(f"AI content generation failed: {str(e)}")
        ai_generated_files = []
        logger.info("Continuing without AI generation due to error")

    return {
        "status": "ok",
        "resume_files": saved,
        "exp_files": exp_saved,
        "readme_files": readme_saved,
        "jd_files": jd_saved,
        "ai_generated_files": ai_generated_files,
        "tmp_dir": TMP_DIR,
        "full_context": full_context,
        "parsed_resumes": parsed_resumes
    }