from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

MAX_DOCUMENT_CHARS = 100_000


def extract_document_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()
    try:
        if extension == ".pdf":
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                raise ValueError("Encrypted PDF files are not supported.")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif extension == ".docx":
            document = Document(BytesIO(content))
            paragraphs = [paragraph.text for paragraph in document.paragraphs]
            tables = [
                "\n".join(
                    " | ".join(cell.text for cell in row.cells)
                    for row in table.rows
                )
                for table in document.tables
            ]
            text = "\n".join(paragraphs + tables)
        else:
            raise ValueError("Only PDF and DOCX evidence files are supported.")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Could not extract text from {extension or 'the file'}.") from exc

    text = text.strip()
    if not text:
        raise ValueError("The document contains no extractable text.")
    if len(text) > MAX_DOCUMENT_CHARS:
        raise ValueError(
            f"Extracted text exceeds the {MAX_DOCUMENT_CHARS:,}-character limit."
        )
    return text
