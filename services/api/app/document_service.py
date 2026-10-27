import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .chunking import TextChunk
from .config import DOCUMENTS_DIR, MAX_UPLOAD_BYTES
from .errors import DocumentProcessingError, OllamaUnavailable
from .extraction import extract_chunks, validate_filename
from .ollama import OllamaClient
from .vector_store import ChromaStore


class DocumentService:
    def __init__(self, ollama: OllamaClient, store: ChromaStore,
                 documents_dir: Path = DOCUMENTS_DIR, max_bytes: int = MAX_UPLOAD_BYTES):
        self.ollama = ollama
        self.store = store
        self.documents_dir = documents_dir
        self.max_bytes = max_bytes
        self.documents_dir.mkdir(parents=True, exist_ok=True)

    def list_documents(self) -> list[dict]:
        documents = []
        for manifest_path in self.documents_dir.glob("*.json"):
            try:
                documents.append(json.loads(manifest_path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return sorted(documents, key=lambda item: item.get("uploaded_at", ""), reverse=True)

    def add(self, filename: str, content: bytes) -> dict:
        safe_name = validate_filename(filename)
        if not content:
            raise ValueError("El archivo está vacío.")
        if len(content) > self.max_bytes:
            raise ValueError(f"El archivo supera el límite de {self.max_bytes // 1_000_000} MB.")
        document_id = uuid.uuid4().hex
        extension = Path(safe_name).suffix.lower()
        content_path = self.documents_dir / f"{document_id}{extension}"
        manifest_path = self.documents_dir / f"{document_id}.json"
        content_path.write_bytes(content)
        try:
            chunks: list[TextChunk] = extract_chunks(content_path)
            embeddings = self.ollama.embed([chunk.text for chunk in chunks])
            metadata = [
                {"document_id": document_id, "filename": safe_name,
                 "chunk_index": chunk.index, **({"page": chunk.page} if chunk.page else {})}
                for chunk in chunks
            ]
            self.store.add(document_id, [chunk.text for chunk in chunks], embeddings, metadata)
            record = {
                "id": document_id,
                "filename": safe_name,
                "status": "indexed",
                "chunks": len(chunks),
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
            manifest_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            return record
        except (DocumentProcessingError, OllamaUnavailable, Exception):
            try:
                self.store.delete(document_id)
            except Exception:
                pass
            content_path.unlink(missing_ok=True)
            manifest_path.unlink(missing_ok=True)
            raise

    def delete(self, document_id: str) -> bool:
        if not document_id.isalnum():
            return False
        manifest_path = self.documents_dir / f"{document_id}.json"
        record = None
        if manifest_path.exists():
            try:
                record = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                record = None
        self.store.delete(document_id)
        for path in self.documents_dir.glob(f"{document_id}.*"):
            if path.is_file():
                path.unlink(missing_ok=True)
        return record is not None
