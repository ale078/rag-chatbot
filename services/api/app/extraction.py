from pathlib import Path

from pypdf import PdfReader
from docx import Document

from .chunking import TextChunk, split_text
from .config import ALLOWED_EXTENSIONS, CHUNK_OVERLAP, CHUNK_SIZE
from .errors import DocumentProcessingError


def validate_filename(filename: str) -> str:
    safe_name = Path(filename or "").name
    suffix = Path(safe_name).suffix.lower()
    if not safe_name or suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Formato no compatible. Carga un archivo PDF, DOCX, TXT o Markdown.")
    return safe_name


def extract_chunks(path: Path) -> list[TextChunk]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            pages = []
            for page_number, page in enumerate(PdfReader(str(path)).pages, start=1):
                text = page.extract_text() or ""
                pages.extend(split_text(text, CHUNK_SIZE, CHUNK_OVERLAP, page_number))
            chunks = [TextChunk(item.text, item.page, index) for index, item in enumerate(pages)]
        elif suffix == ".docx":
            document = Document(str(path))
            text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
            chunks = split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        else:
            text = path.read_text(encoding="utf-8-sig")
            chunks = split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    except (OSError, UnicodeError, Exception) as exc:
        raise DocumentProcessingError(f"No se pudo leer el documento: {exc}") from exc
    if not chunks:
        raise DocumentProcessingError("El documento no contiene texto extraíble. Los PDF escaneados no admiten OCR.")
    return chunks
