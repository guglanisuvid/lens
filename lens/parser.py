"""Parses documents (PDF, txt) into clean text chunks."""
import os
import fitz  # PyMuPDF


CHUNK_SIZE = 1000   # characters
CHUNK_OVERLAP = 200


def parse_file(path: str) -> list[dict]:
    """
    Parse a file into a list of chunks.
    Returns: [{text, page, source}]
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return _parse_pdf(path)
    elif ext == ".txt":
        return _parse_txt(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .txt")


def _parse_pdf(path: str) -> list[dict]:
    chunks = []
    doc = fitz.open(path)
    source = os.path.basename(path)

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if not text:
            continue
        for chunk in chunk_text(text):
            chunks.append({
                "text":   chunk,
                "page":   page_num,
                "source": source,
            })

    doc.close()
    return chunks


def _parse_txt(path: str) -> list[dict]:
    source = os.path.basename(path)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    return [
        {"text": chunk, "page": 1, "source": source}
        for chunk in chunk_text(text)
    ]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
