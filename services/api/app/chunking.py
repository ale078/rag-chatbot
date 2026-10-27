from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    text: str
    page: int | None
    index: int


def split_text(text: str, size: int = 900, overlap: int = 150,
               page: int | None = None) -> list[TextChunk]:
    if size < 1 or overlap < 0 or overlap >= size:
        raise ValueError("size debe ser positivo y overlap debe estar entre 0 y size.")
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks: list[TextChunk] = []
    start = 0
    while start < len(normalized):
        end = min(start + size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start + size // 2:
                end = boundary
        fragment = normalized[start:end].strip()
        if fragment:
            chunks.append(TextChunk(fragment, page, len(chunks)))
        if end >= len(normalized):
            break
        start = max(start + 1, end - overlap)
    return chunks
