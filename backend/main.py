from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
from typing import List
from nlp_pipeline import process_input_content, process_text_input, scrape_job_description
from ai_content_generation import rewrite_resume, generate_cover_letter
from latex_resume_generator import generate_latex_resume

# Load environment variables
load_dotenv()

# Create directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(BASE_DIR, "tmp")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(PROMPTS_DIR, exist_ok=True)

# Logger setup
logger = logging.getLogger("uvicorn.error")

# Ensure job_description_text.txt exists
jd_text_default_path = os.path.join(TMP_DIR, "job_description_text.txt")
if not os.path.exists(jd_text_default_path):
    with open(jd_text_default_path, "w", encoding="utf-8") as f:
        f.write("")
    logger.info(f"Ensured job description text file exists at {jd_text_default_path}")

app = FastAPI(
    title="Resume Tool Backend",
    description="API for processing resumes, job descriptions, and generating tailored documents",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/jd_from_url")
async def jd_from_url(url: str = Form(...)):
    """
    Accepts a URL, scrapes job description, and saves it as a .txt file.
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")
    try:
        filename = "job_description_url"
        scrape_job_description(url, filename, TMP_DIR)
        filepath = os.path.join(TMP_DIR, f"{filename}.txt")
        logger.info(f"Saved job description from URL {url} to {filepath}")
        return {"status": "ok", "jd_file": f"{filename}.txt", "tmp_dir": TMP_DIR}
    except Exception as e:
        logger.error(f"Failed to scrape job description from URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to scrape job description from URL.")

@app.post("/api/submit")
async def submit(
    resume_files: List[UploadFile] = File(...),
    exp_files: List[UploadFile] = File(None),
    readme_files: List[UploadFile] = File(None),
    jd_text: str = Form(None),
    jd_file: UploadFile = File(None)
):
    """
    Endpoint for handling submission, processing inputs, and generating AI content.
    Requires at least one PDF and one .tex resume file.
    Processes all PDFs for text extraction and LaTeX generation using the first .tex as the template.
    """
    logger.info(f"TMP_DIR: {TMP_DIR}")
    logger.info(f"Received resume_files: {[rf.filename for rf in resume_files]}")
    saved = []
    exp_saved: List[str] = []
    readme_saved: List[str] = []
    jd_saved: List[str] = []
    ai_generated_files = []

    # Validate resume files: at least one PDF and one .tex
    pdf_files = [rf for rf in resume_files if os.path.splitext(rf.filename)[1].lower() == '.pdf']
    tex_files = [rf for rf in resume_files if os.path.splitext(rf.filename)[1].lower() == '.tex']
    if not pdf_files or not tex_files:
        logger.error(f"Received {len(pdf_files)} PDF and {len(tex_files)} .tex files. At least one of each is required.")
        raise HTTPException(status_code=400, detail=f"At least one PDF and one .tex resume file are required. Received {len(pdf_files)} PDF and {len(tex_files)} .tex files.")

    # Save the first .tex file as user_resume_template.tex
    user_template_path = os.path.join(TEMPLATES_DIR, "user_resume_template.tex")
    tex_processed = False
    for rf in tex_files:
        if not tex_processed:
            content = await rf.read()
            try:
                with open(user_template_path, 'wb') as f:
                    f.write(content)
                logger.info(f"Saved user .tex file '{rf.filename}' as {user_template_path}")
                tex_processed = True
            except Exception as e:
                logger.error(f"Failed to save user .tex file '{rf.filename}': {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to save user .tex file: {str(e)}")
        else:
            logger.warning(f"Skipping additional .tex file '{rf.filename}' as only one template is used.")

    # Handle job description
    if jd_text:
        process_text_input(jd_text, "job_description_text", TMP_DIR)
        jd_saved.append("job_description_text.txt")
        logger.info(f"Saved job description text to {jd_text_default_path}")
    elif jd_file:
        content_jd = await jd_file.read()
        ext = os.path.splitext(jd_file.filename)[1].lower()
        process_input_content(content_jd, ext, "job_description_file", TMP_DIR)
        jd_saved.append("job_description_file.txt")
        logger.info(f"Processed job description file {jd_file.filename} to job_description_file.txt")
    elif os.path.exists(os.path.join(TMP_DIR, "job_description_url.txt")):
        jd_saved.append("job_description_url.txt")
        logger.info("Using existing job description from URL.")

    # Handle supporting files
    if exp_files:
        for ef in exp_files:
            content = await ef.read()
            ext = os.path.splitext(ef.filename)[1].lower()
            input_field = f"experience_{os.path.splitext(ef.filename)[0]}"
            process_input_content(content, ext, input_field, TMP_DIR)
            exp_saved.append(f"{input_field}.txt")
            logger.info(f"Processed experience file {ef.filename} to {input_field}.txt")
    if readme_files:
        for rf2 in readme_files:
            content = await rf2.read()
            ext = os.path.splitext(rf2.filename)[1].lower()
            input_field = f"readme_{os.path.splitext(rf2.filename)[0]}"
            process_input_content(content, ext, input_field, TMP_DIR)
            readme_saved.append(f"{input_field}.txt")
            logger.info(f"Processed readme file {rf2.filename} to {input_field}.txt")

    # Handle resume files (only PDFs for content extraction)
    for rf in pdf_files:
        content = await rf.read()
        logger.debug(f"Reading resume file {rf.filename} with size {len(content)} bytes")
        ext = os.path.splitext(rf.filename)[1].lower()
        if ext != '.pdf':
            logger.error(f"Skipping non-PDF file {rf.filename} in resume processing.")
            continue
        input_field = f"resume_{os.path.splitext(rf.filename)[0]}"
        process_input_content(content, ext, input_field, TMP_DIR)
        saved.append(f"{input_field}.txt")
        logger.info(f"Processed resume file {rf.filename} to {input_field}.txt")

    # AI Content Generation Pipeline
    try:
        logger.info("Starting AI content generation pipeline...")
        for fname in saved:
            # Load resume text
            resume_path = os.path.join(TMP_DIR, fname)
            with open(resume_path, 'r', encoding='utf-8') as f:
                resume_text = f.read()
            logger.debug(f"Loaded resume text from {fname}: {resume_text[:100]}...")
            base_name = os.path.splitext(fname)[0]

            # Load context (job description, experience, readme)
            context_parts = []
            for ctx_file in exp_saved + readme_saved + jd_saved:
                ctx_path = os.path.join(TMP_DIR, ctx_file)
                with open(ctx_path, 'r', encoding='utf-8') as f:
                    ctx_content = f.read()
                context_parts.append(ctx_content)
                logger.debug(f"Loaded context from {ctx_file}: {ctx_content[:100]}...")
            context_text = "\n".join(context_parts)

            # Generate improved resume
            logger.info(f"Processing resume: {fname}")
            improved_resume = await rewrite_resume(resume_text, context_text)
            improved_resume_filename = f"{base_name}_ai_improved.txt"
            improved_resume_path = os.path.join(TMP_DIR, improved_resume_filename)
            with open(improved_resume_path, 'w', encoding='utf-8') as f:
                f.write(improved_resume)
            ai_generated_files.append(improved_resume_filename)
            logger.info(f"Saved improved resume: {improved_resume_filename}")

            # Generate LaTeX resume using user template
            latex_prompt_path = os.path.join(PROMPTS_DIR, "latex_resume_prompt.txt")
            try:
                latex_resume = await generate_latex_resume(improved_resume, user_template_path, latex_prompt_path)
                latex_filename = f"{base_name}_ai_improved.tex"
                latex_path = os.path.join(TMP_DIR, latex_filename)
                with open(latex_path, 'w', encoding='utf-8') as f:
                    f.write(latex_resume)
                ai_generated_files.append(latex_filename)
                logger.info(f"Saved LaTeX resume: {latex_filename}")
            except Exception as e:
                logger.error(f"Failed to generate LaTeX resume for {fname}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to generate LaTeX resume for {fname}: {str(e)}")

        if saved:
            # Generate cover letter using the first resume
            logger.info("Generating cover letter...")
            first_resume_fname = saved[0]
            with open(os.path.join(TMP_DIR, first_resume_fname), 'r', encoding='utf-8') as f:
                resume_text = f.read()
            context_parts = []
            for ctx_file in exp_saved + readme_saved + jd_saved:
                ctx_path = os.path.join(TMP_DIR, ctx_file)
                with open(ctx_path, 'r', encoding='utf-8') as f:
                    ctx_content = f.read()
                context_parts.append(ctx_content)
            context_text = "\n".join(context_parts)

            cover_letter = await generate_cover_letter(resume_text, context_text)
            cover_letter_filename = "ai_generated_cover_letter.txt"
            cover_letter_path = os.path.join(TMP_DIR, cover_letter_filename)
            with open(cover_letter_path, 'w', encoding='utf-8') as f:
                f.write(cover_letter)
            ai_generated_files.append(cover_letter_filename)
            logger.info(f"Saved cover letter: {cover_letter_filename}")

        logger.info(f"AI content generation completed. Generated files: {ai_generated_files}")

    except Exception as e:
        logger.error(f"AI content generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI content generation failed: {str(e)}")

    return {
        "status": "ok",
        "resume_files": saved,
        "exp_files": exp_saved,
        "readme_files": readme_saved,
        "jd_files": jd_saved,
        "ai_generated_files": ai_generated_files,
        "tmp_dir": TMP_DIR
    }