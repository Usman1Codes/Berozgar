"""
nlp_pipeline.py

Implements context aggregation and structure-aware resume parsing.
"""

import os
from typing import Dict, List
from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader, UnstructuredWordDocumentLoader
from pylatexenc.latexwalker import LatexWalker
from pylatexenc.latex2text import LatexNodes2Text


def aggregate_context(directory: str) -> str:
    """
    Load all supporting documents in a directory using langchain-community loaders
    and concatenate them into a single context string.
    Supports .txt, .md, .pdf, .docx, and .tex files.
    """
    pieces: List[str] = []
    for fname in sorted(os.listdir(directory)):
        path = os.path.join(directory, fname)
        ext = os.path.splitext(fname)[1].lower()
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(path)
                docs = loader.load()
                pieces.extend(doc.page_content for doc in docs)
            elif ext == ".md":
                try:
                    loader = UnstructuredMarkdownLoader(path)
                    docs = loader.load()
                    pieces.extend(doc.page_content for doc in docs)
                except LookupError:
                    # Fallback to raw markdown text if NLTK tagger is missing
                    with open(path, "r", encoding="utf-8") as f:
                        pieces.append(f.read())
            elif ext == ".docx":
                loader = UnstructuredWordDocumentLoader(path)
                docs = loader.load()
                pieces.extend(doc.page_content for doc in docs)
            elif ext == ".tex":
                with open(path, "r", encoding="utf-8") as f:
                    latex_str = f.read()
                try:
                    text = LatexNodes2Text().latex_to_text(latex_str)
                except Exception:
                    # Fallback to raw LaTeX if parsing fails
                    text = latex_str
                pieces.append(text)
            elif ext == ".txt":
                with open(path, "r", encoding="utf-8") as f:
                    pieces.append(f.read())
            else:
                continue
        except Exception as e:
            raise RuntimeError(f"Failed to load {fname}: {e}")
    # Separate documents with two newlines
    return "\n\n".join(pieces)


def parse_tex_sections(path: str) -> Dict[str, str]:
    """
    Parse a LaTeX resume (.tex) into a mapping of section names to raw LaTeX content.
    Uses pylatexenc to walk the node tree.
    """
    with open(path, "r", encoding="utf-8") as f:
        latex_str = f.read()
    walker = LatexWalker(latex_str)
    nodes, _, _ = walker.get_latex_nodes()
    sections: Dict[str, str] = {}
    current: str = None
    buffer: List[str] = []
    for node in nodes:
        # Detect \section commands
        if hasattr(node, "macroname") and node.macroname == "section":
            # Save previous section
            if current:
                sections[current] = "".join(buffer).strip()
                buffer = []
            # Safely extract section title
            title = None
            if hasattr(node, "nodeargs") and isinstance(node.nodeargs, list) and len(node.nodeargs) > 0:
                arg0 = node.nodeargs[0]
                if hasattr(arg0, "nodelist") and arg0.nodelist:
                    title = "".join(n.chars for n in arg0.nodelist).strip()
            current = title or "Unnamed"
        else:
            buffer.append(node.latex_verbatim())
    # Save last section
    if current:
        sections[current] = "".join(buffer).strip()
    return sections

def parse_pdf_resume(path: str) -> str:
    """
    Extract full clean text from PDF resume using PyPDFLoader.
    """
    loader = PyPDFLoader(path)
    docs = loader.load()
    return "\n\n".join(doc.page_content for doc in docs)