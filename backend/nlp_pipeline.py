import os
import re
from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from bs4 import BeautifulSoup
import requests
import logging
import tempfile

# Logger setup
logger = logging.getLogger("uvicorn.error")

def normalize_text(text: str) -> str:
    """
    Normalize text by removing extra whitespace and standardizing newlines.
    """
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'\n+', '\n', text)
    logger.debug(f"Normalized text: {text[:100]}...")
    return text

def save_text(text: str, output_path: str) -> None:
    """
    Save text to a .txt file.
    """
    logger.debug(f"Saving text to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

def process_input_content(content: bytes, ext: str, input_field: str, output_dir: str) -> None:
    """
    Process in-memory content (PDF, TXT, MD), extract text, and save to .txt.
    """
    if ext not in {'.pdf', '.txt', '.md'}:
        raise ValueError(f"Unsupported file extension: {ext}")

    try:
        logger.debug(f"Processing content for {input_field} with extension {ext}")
        if ext == '.pdf':
            # Save to temporary file for PyPDFLoader
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            try:
                loader = PyPDFLoader(temp_file_path)
                docs = loader.load()
                text = "\n".join(doc.page_content for doc in docs)
            finally:
                os.unlink(temp_file_path)  # Clean up temporary file
            logger.debug(f"Extracted PDF text: {text[:100]}...")
        elif ext == '.md':
            temp_path = os.path.join(output_dir, f"temp_{input_field}.md")
            with open(temp_path, 'wb') as f:
                f.write(content)
            loader = UnstructuredMarkdownLoader(temp_path)
            docs = loader.load()
            text = "\n".join(doc.page_content for doc in docs)
            os.remove(temp_path)
            logger.debug(f"Extracted Markdown text: {text[:100]}...")
        elif ext == '.txt':
            text = content.decode('utf-8')
            logger.debug(f"Extracted Text: {text[:100]}...")
    except Exception as e:
        logger.error(f"Failed to process content for {input_field}: {e}")
        raise RuntimeError(f"Failed to process content for {input_field}: {e}")

    normalized_text = normalize_text(text)
    output_path = os.path.join(output_dir, f"{input_field}.txt")
    save_text(normalized_text, output_path)
    logger.info(f"Saved extracted text to {output_path}")

def process_text_input(text: str, input_field: str, output_dir: str) -> None:
    """
    Process text input, normalize, and save to .txt.
    """
    logger.debug(f"Processing text input for {input_field}: {text[:100]}...")
    normalized_text = normalize_text(text)
    output_path = os.path.join(output_dir, f"{input_field}.txt")
    save_text(normalized_text, output_path)
    logger.info(f"Saved text to {output_path}")

def scrape_job_description(url: str, input_field: str, output_dir: str) -> None:
    """
    Scrape job description from a URL and save to .txt.
    """
    logger.debug(f"Scraping job description from {url}")
    include_keywords = [
        'job description', 'responsibilities', 'requirements', 'qualifications',
        'skills', 'experience', 'duties', 'role', 'position', 'overview'
    ]
    exclude_keywords = [
        'privacy policy', 'terms of service', 'cookie policy', 'footer', 'navigation'
    ]

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for elem in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            elem.decompose()

        text_parts = []
        for tag in soup.find_all(['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4']):
            text = tag.get_text(strip=True)
            if not text:
                continue
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in include_keywords) and \
               not any(keyword in text_lower for keyword in exclude_keywords):
                text_parts.append(text)

        raw_text = " ".join(text_parts)
        normalized_text = normalize_text(raw_text)
        output_path = os.path.join(output_dir, f"{input_field}.txt")
        save_text(normalized_text, output_path)
        logger.info(f"Saved scraped job description to {output_path}")
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        raise RuntimeError(f"Failed to scrape {url}: {e}")