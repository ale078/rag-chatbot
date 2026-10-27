import pytest
from docx import Document

from app.chunking import split_text
from app.document_service import DocumentService
from app.errors import OllamaUnavailable
from app.extraction import extract_chunks, validate_filename
from app.rag import RagService


def test_chunking_overlap_and_page_metadata():
    chunks = split_text("uno dos tres cuatro cinco seis", size=14, overlap=4, page=3)
    assert len(chunks) > 1
    assert all(chunk.page == 3 for chunk in chunks)
    assert chunks[0].index == 0


def test_supported_extensions_and_reject_unsafe_formats():
    assert validate_filename("../../informe.PDF") == "informe.PDF"
    with pytest.raises(ValueError, match="Formato"):
        validate_filename("payload.html")


def test_extract_txt_and_docx(tmp_path):
    text_path = tmp_path / "nota.md"
    text_path.write_text("# Hola\ncontenido", encoding="utf-8")
    assert "Hola" in extract_chunks(text_path)[0].text
    docx_path = tmp_path / "nota.docx"
    document = Document()
    document.add_paragraph("Texto DOCX")
    document.save(docx_path)
    assert extract_chunks(docx_path)[0].text == "Texto DOCX"


class FakeOllama:
    def embed(self, texts):
        return [[0.1, 0.2] for _ in texts]


class FakeStore:
    def __init__(self, results=None):
        self.results = results or []
        self.added = []
        self.deleted = []

    def count(self):
        return len(self.results)

    def add(self, *args):
        self.added.append(args)

    def search(self, *_):
        return self.results

    def delete(self, document_id):
        self.deleted.append(document_id)


def test_document_upload_list_delete_and_size_validation(tmp_path):
    store = FakeStore()
    service = DocumentService(FakeOllama(), store, tmp_path, max_bytes=1000)
    record = service.add("guia.txt", b"texto de prueba")
    assert service.list_documents()[0]["id"] == record["id"]
    assert len(store.added) == 1
    assert service.delete(record["id"]) is True
    assert service.list_documents() == []
    with pytest.raises(ValueError, match="l\xedmite"):
        service.add("big.txt", b"x" * 1001)


def test_rag_citation_and_unbacked_fallback_are_distinguished():
    class Generator(FakeOllama):
        def generate(self, prompt):
            return "Respuesta de prueba"

    store = FakeStore([{
        "text": "El manual indica el horario.",
        "metadata": {"document_id": "abc", "filename": "manual.pdf", "page": 2},
        "distance": 0.1,
    }])
    backed = RagService(Generator(), store).answer("¿Cuál es el horario?")
    assert backed["grounding"] == "documents"
    assert backed["citations"] == [{"filename": "manual.pdf", "page": 2, "document_id": "abc"}]

    store.results = [{"text": "irrelevante", "metadata": {}, "distance": 0.9}]
    fallback = RagService(Generator(), store).answer("Pregunta sin evidencia")
    assert fallback["grounding"] == "fallback"
    assert fallback["citations"] == []


def test_rag_uses_chat_fallback_without_embedding_when_library_is_empty():
    class ChatOnlyOllama:
        def embed(self, texts):
            raise AssertionError("No debe solicitar embeddings sin documentos.")

        def generate(self, prompt):
            assert "conocimiento general" in prompt
            return "Respuesta general"

    result = RagService(ChatOnlyOllama(), FakeStore()).answer("¿Qué es RAG?")

    assert result == {
        "answer": "Respuesta general",
        "grounding": "fallback",
        "citations": [],
    }


def test_upload_removes_file_if_embedding_service_fails(tmp_path):
    class BrokenOllama(FakeOllama):
        def embed(self, texts):
            raise OllamaUnavailable("Ollama no disponible")

    store = FakeStore()
    service = DocumentService(BrokenOllama(), store, tmp_path)
    with pytest.raises(OllamaUnavailable):
        service.add("nota.txt", b"contenido")
    assert list(tmp_path.iterdir()) == []
