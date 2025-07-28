from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from typing import List
import logging

# Load environment variables from .env
load_dotenv()

# Create local tmp directory for uploads
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(BASE_DIR, "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

# Logger setup
logger = logging.getLogger("uvicorn.error")
import requests
from fastapi import Body

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
        filename = "job_description_url.txt"
        filepath = os.path.join(TMP_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
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
    Endpoint for handling submission including job description via text, file, or url (handled separately).
    """
    logger.info(f"TMP_DIR: {TMP_DIR}")
    logger.info(f"Received resume_files: {[rf.filename for rf in resume_files]}")
    # Validate & save resume files
    allowed_ext = {".pdf", ".tex"}
    saved = []
    exp_saved: List[str] = []
    readme_saved: List[str] = []
    jd_saved: List[str] = []

    # Handle job description text input
    if jd_text:
        jd_txt_path = os.path.join(TMP_DIR, "job_description_text.txt")
        try:
            with open(jd_txt_path, "w", encoding="utf-8") as f:
                f.write(jd_text)
            jd_saved.append("job_description_text.txt")
            logger.info(f"Saved job description text to {jd_txt_path}")
        except Exception as e:
            logger.error(f"Failed to save job description text: {e}")
            raise HTTPException(status_code=500, detail="Failed to save job description text.")

    # Handle job description file upload
    if jd_file:
        allowed_jd_ext = {".pdf", ".docx", ".md", ".tex", ".txt"}
        ext_jd = os.path.splitext(jd_file.filename)[1].lower()
        if ext_jd not in allowed_jd_ext:
            raise HTTPException(status_code=400, detail=f"Invalid job description file type: {jd_file.filename}")
        jd_file_path = os.path.join(TMP_DIR, jd_file.filename)
        try:
            with open(jd_file_path, "wb") as f:
                content_jd = await jd_file.read()
                f.write(content_jd)
            jd_saved.append(jd_file.filename)
            logger.info(f"Saved job description file {jd_file.filename} to {jd_file_path}")
        except Exception as e:
            logger.error(f"Failed to save job description file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save job description file.")

    # Handle job description from URL (scraped HTML)
    if not jd_file and not jd_text:
        jd_url_path = os.path.join(TMP_DIR, "job_description_url.txt")
        if os.path.exists(jd_url_path):
            try:
                # Confirm file is readable and non-empty
                with open(jd_url_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content.strip():
                        raise Exception("job_description_url.txt is empty")
                jd_saved.append("job_description_url.txt")
                logger.info(f"Attached job description from URL: {jd_url_path}")
            except Exception as e:
                logger.error(f"Failed to use job description from URL: {e}")
                raise HTTPException(status_code=500, detail="Failed to use job description from URL.")

    # Clean up old JD files after submission
    for fn in ["job_description_text.txt", "job_description_url.txt"]:
        try:
            path = os.path.join(TMP_DIR, fn)
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Cleaned up old JD file: {path}")
        except Exception as e:
            logger.warning(f"Failed to clean up JD file {fn}: {e}")

    # Handle experience files
    if exp_files:
        allowed_exp_ext = {".pdf", ".docx", ".md", ".tex"}
        for ef in exp_files:
            ext2 = os.path.splitext(ef.filename)[1].lower()
            if ext2 not in allowed_exp_ext:
                raise HTTPException(status_code=400, detail=f"Invalid experience file type: {ef.filename}")
            exp_path = os.path.join(TMP_DIR, ef.filename)
            logger.info(f"Saved experience file {ef.filename} to {exp_path}")
            with open(exp_path, "wb") as f:
                content2 = await ef.read()
                f.write(content2)
            exp_saved.append(ef.filename)

        # Handle project readmes
    if readme_files:
        allowed_readme_ext = {".pdf", ".docx", ".md", ".tex", ".txt"}
        for rf2 in readme_files:
            ext3 = os.path.splitext(rf2.filename)[1].lower()
            if ext3 not in allowed_readme_ext:
                raise HTTPException(status_code=400, detail=f"Invalid project readme file type: {rf2.filename}")
            readme_path = os.path.join(TMP_DIR, rf2.filename)
            logger.info(f"Saved readme file {rf2.filename} to {readme_path}")
            with open(readme_path, "wb") as f:
                content3 = await rf2.read()
                f.write(content3)
            readme_saved.append(rf2.filename)
    for rf in resume_files:
        ext = os.path.splitext(rf.filename)[1].lower()
        if ext not in allowed_ext:
            raise HTTPException(status_code=400, detail=f"Invalid file type: {rf.filename}")
        path = os.path.join(TMP_DIR, rf.filename)
        logger.info(f"Saved {rf.filename} to {path}")
        with open(path, "wb") as f:
            content = await rf.read()
            f.write(content)
        saved.append(rf.filename)

    logger.info(f"Returning response files: {saved}, exp_files: {exp_saved}, readme_files: {readme_saved}, jd_files: {jd_saved}")
    return {"status": "ok", "resume_files": saved, "exp_files": exp_saved, "readme_files": readme_saved, "jd_files": jd_saved, "tmp_dir": TMP_DIR}
