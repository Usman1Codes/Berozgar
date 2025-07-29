from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from typing import List, Dict
import logging
from nlp_pipeline import aggregate_context, parse_tex_sections, parse_pdf_resume
from ai_content_generation import ai_generator

# Helper function for LaTeX reconstruction
async def reconstruct_latex_file(original_file_path: str, improved_sections: Dict[str, str]) -> str:
    """
    Reconstruct a LaTeX file by replacing sections with AI-improved content.
    Preserves the original structure and replaces section content in-place.
    """
    try:
        with open(original_file_path, "r", encoding="utf-8") as f:
            original_content = f.read()
        
        reconstructed_content = original_content
        
        # Map common section names to LaTeX patterns
        section_patterns = {
            'experience': [r'\\section\{.*?experience.*?\}', r'\\section\{.*?work.*?\}'],
            'education': [r'\\section\{.*?education.*?\}'],
            'skills': [r'\\section\{.*?skills.*?\}', r'\\section\{.*?technical.*?\}'],
            'projects': [r'\\section\{.*?projects.*?\}'],
            'summary': [r'\\section\{.*?summary.*?\}', r'\\section\{.*?objective.*?\}'],
        }
        
        import re
        
        # Process each improved section
        for section_name, improved_content in improved_sections.items():
            section_key = section_name.lower().strip()
            
            # Find matching patterns for this section
            patterns_to_try = []
            for key, patterns in section_patterns.items():
                if key in section_key or section_key in key:
                    patterns_to_try.extend(patterns)
            
            # If no specific patterns found, try a generic approach
            if not patterns_to_try:
                patterns_to_try = [rf'\\section\{{.*?{re.escape(section_name)}.*?\}}']
            
            # Try to find and replace the section content
            for pattern in patterns_to_try:
                # Find the section header
                section_match = re.search(pattern, reconstructed_content, re.IGNORECASE)
                if section_match:
                    section_start = section_match.end()
                    
                    # Find the end of this section (next \section or \end{document})
                    next_section_pattern = r'\\section\{|\\end\{document\}'
                    next_match = re.search(next_section_pattern, reconstructed_content[section_start:])
                    
                    if next_match:
                        section_end = section_start + next_match.start()
                    else:
                        section_end = len(reconstructed_content)
                    
                    # Extract the section content (everything between section header and next section)
                    original_section_content = reconstructed_content[section_start:section_end]
                    
                    # Clean up the improved content and ensure it maintains LaTeX formatting
                    cleaned_improved_content = improved_content.strip()
                    
                    # If the improved content doesn't start with LaTeX commands, add proper formatting
                    if not cleaned_improved_content.startswith('\\'):
                        # Add proper LaTeX environment spacing
                        cleaned_improved_content = f"\n\n{cleaned_improved_content}\n"
                    
                    # Replace the section content
                    reconstructed_content = (
                        reconstructed_content[:section_start] + 
                        cleaned_improved_content + 
                        reconstructed_content[section_end:]
                    )
                    
                    logger.info(f"Successfully replaced content for section: {section_name}")
                    break
            else:
                logger.warning(f"Could not find section pattern for: {section_name}")
        
        return reconstructed_content
        
    except Exception as e:
        logger.error(f"Error reconstructing LaTeX file: {str(e)}")
        # Return original content if reconstruction fails
        with open(original_file_path, "r", encoding="utf-8") as f:
            return f.read()

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
import requests
from bs4 import BeautifulSoup
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
        # Parse HTML and extract <h1>, <h2>, <h3> text
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

    # Persistent JD files: no cleanup needed

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

        # NLP pipeline processing
    try:
        full_context = aggregate_context(TMP_DIR)
        
        # print(full_context)
        parsed_resumes = {}
        for fname in saved:
            ext = os.path.splitext(fname)[1].lower()
            path = os.path.join(TMP_DIR, fname)
            if ext == ".tex":
                parsed_resumes[fname] = parse_tex_sections(path)
                # print(parsed_resumes[fname])
            else:
                parsed_resumes[fname] = parse_pdf_resume(path)
    except Exception as e:
        logger.error(f"NLP pipeline processing failed: {e}")
        raise HTTPException(status_code=500, detail="NLP pipeline processing failed.")

    # AI Content Generation Pipeline (Phase 2)
    try:
        logger.info("Starting AI content generation pipeline...")
        
        ai_generated_files = []
        
        # Process each resume with AI
        for fname in saved:
            ext = os.path.splitext(fname)[1].lower()
            base_name = os.path.splitext(fname)[0]
            
            if ext == ".tex":
                # Process LaTeX resume
                logger.info(f"Processing LaTeX resume: {fname}")
                tex_sections = parsed_resumes[fname]
                
                # Generate improved sections
                improved_sections = await ai_generator.process_latex_resume(tex_sections, full_context)
                
                # Reconstruct the LaTeX file with improved content
                improved_latex_content = await reconstruct_latex_file(
                    os.path.join(TMP_DIR, fname), improved_sections
                )
                
                # Save improved LaTeX file
                improved_latex_filename = f"{base_name}_ai_improved.tex"
                improved_latex_path = os.path.join(TMP_DIR, improved_latex_filename)
                with open(improved_latex_path, "w", encoding="utf-8") as f:
                    f.write(improved_latex_content)
                
                ai_generated_files.append(improved_latex_filename)
                logger.info(f"Saved improved LaTeX resume: {improved_latex_filename}")
                
            elif ext == ".pdf":
                # Process PDF resume
                logger.info(f"Processing PDF resume: {fname}")
                resume_text = parsed_resumes[fname]
                
                # Generate improved resume content
                improved_resume = await ai_generator.process_pdf_resume(resume_text, full_context)
                
                # Save improved resume as text file
                improved_resume_filename = f"{base_name}_ai_improved.txt"
                improved_resume_path = os.path.join(TMP_DIR, improved_resume_filename)
                with open(improved_resume_path, "w", encoding="utf-8") as f:
                    f.write(improved_resume)
                
                ai_generated_files.append(improved_resume_filename)
                logger.info(f"Saved improved PDF resume content: {improved_resume_filename}")
        
        # Generate cover letter for the first resume
        if saved:
            logger.info("Generating cover letter...")
            first_resume = saved[0]
            first_ext = os.path.splitext(first_resume)[1].lower()
            
            # Get resume text for cover letter generation
            if first_ext == ".tex":
                # Convert LaTeX sections to text for cover letter context
                resume_text_for_cover = "\n\n".join([
                    f"**{section_name}:**\n{content}" 
                    for section_name, content in parsed_resumes[first_resume].items()
                ])
            else:
                resume_text_for_cover = parsed_resumes[first_resume]
            
            # Generate cover letter
            cover_letter = await ai_generator.generate_cover_letter(resume_text_for_cover, full_context)
            
            # Save cover letter
            cover_letter_filename = "ai_generated_cover_letter.txt"
            cover_letter_path = os.path.join(TMP_DIR, cover_letter_filename)
            with open(cover_letter_path, "w", encoding="utf-8") as f:
                f.write(cover_letter)
            
            ai_generated_files.append(cover_letter_filename)
            logger.info(f"Saved cover letter: {cover_letter_filename}")
        
        logger.info(f"AI content generation completed. Generated files: {ai_generated_files}")
        
    except Exception as e:
        logger.error(f"AI content generation failed: {str(e)}")
        # Don't raise exception - let the API continue to work even if AI fails
        ai_generated_files = []
        logger.info("Continuing without AI generation due to error")
    
    logger.info(f"Returning response files: {saved}, exp_files: {exp_saved}, readme_files: {readme_saved}, jd_files: {jd_saved}")
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
