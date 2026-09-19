from io import BytesIO
from PyPDF2 import PdfReader


def extract_text(filename: str, content: bytes) -> str:
    """Extract plain text from the allowed resume formats without persisting uploads."""
    if filename.lower().endswith(".txt"):
        return content.decode("utf-8", errors="ignore")
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError("Only .pdf and .txt resumes are supported")
