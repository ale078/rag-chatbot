from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def test_list_upload_delete_document_routes(monkeypatch):
    class Documents:
        def list_documents(self):
            return [{"id": "abc123", "filename": "guia.txt", "status": "indexed", "chunks": 1}]

        def add(self, filename, content):
            assert filename == "guia.txt"
            assert content == b"contenido"
            return {"id": "abc123", "filename": filename, "status": "indexed", "chunks": 1}

        def delete(self, document_id):
            return document_id == "abc123"

    monkeypatch.setattr(main, "document_service", Documents())
    assert client.get("/api/documents").json()["documents"][0]["id"] == "abc123"
    response = client.post("/api/documents", files={"file": ("guia.txt", b"contenido")})
    assert response.status_code == 201
    assert response.json()["status"] == "indexed"
    assert client.delete("/api/documents/abc123").json()["deleted"] is True
    assert client.delete("/api/documents/unknown").status_code == 404


def test_unsupported_upload_and_chat_error_handling(monkeypatch):
    response = client.post("/api/documents", files={"file": ("nota.html", b"<p>no</p>")})
    assert response.status_code == 400
    assert "Formato" in response.json()["detail"]

    class BrokenRag:
        def answer(self, question):
            raise main.OllamaUnavailable("Ollama no disponible")

    monkeypatch.setattr(main, "rag_service", BrokenRag())
    response = client.post("/api/chat", json={"question": "pregunta"})
    assert response.status_code == 503
    assert "Ollama" in response.json()["detail"]


def test_chat_returns_grounding_and_citations(monkeypatch):
    class Rag:
        def answer(self, question):
            return {"answer": "Está en la guía.", "grounding": "documents",
                    "citations": [{"filename": "guia.pdf", "page": 2}]}

    monkeypatch.setattr(main, "rag_service", Rag())
    response = client.post("/api/chat", json={"question": "¿Dónde está?"})
    assert response.status_code == 200
    assert response.json()["grounding"] == "documents"
    assert response.json()["citations"][0]["filename"] == "guia.pdf"
