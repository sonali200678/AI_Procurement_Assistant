import fitz  # PyMuPDF
import os

def parse_file(file_path: str) -> dict:
    """
    Parses a PDF file and returns its text content and metadata.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at {file_path}")

    text_content = []
    metadata = {}

    try:
        # Open PDF file using fitz (PyMuPDF)
        doc = fitz.open(file_path)
        
        # Extract basic metadata
        metadata = {
            "page_count": len(doc),
            "title": doc.metadata.get("title", "") or "",
            "author": doc.metadata.get("author", "") or "",
            "subject": doc.metadata.get("subject", "") or "",
            "keywords": doc.metadata.get("keywords", "") or "",
            "creator": doc.metadata.get("creator", "") or "",
            "producer": doc.metadata.get("producer", "") or "",
        }

        # Extract text page by page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text_content.append(page.get_text())

        doc.close()
    except Exception as e:
        # Fallback to pdfplumber if fitz has an issue
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                metadata = {
                    "page_count": len(pdf.pages),
                    "title": pdf.metadata.get("Title", "") or "",
                    "author": pdf.metadata.get("Author", "") or "",
                }
                text_content = [page.extract_text() or "" for page in pdf.pages]
        except Exception as e2:
            raise ValueError(f"Failed to parse PDF file: {str(e)} (Fallback error: {str(e2)})")

    full_text = "\n".join(text_content)
    
    # Calculate simple word count for text metadata
    word_count = len(full_text.split())
    metadata["word_count"] = word_count
    
    return {
        "text": full_text,
        "metadata": metadata
    }
