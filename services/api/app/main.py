from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import CHROMA_DIR, DOCUMENTS_DIR, FRONTEND_ORIGIN, MAX_UPLOAD_BYTES
from .document_service import DocumentService
from .errors import DocumentProcessingError, OllamaUnavailable
from .ollama import OllamaClient
from .rag import RagService
from .vector_store import ChromaStore

Path(DOCUMENTS_DIR).mkdir(parents=True, exist_ok=True)
Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
ollama_client = OllamaClient()
vector_store = ChromaStore()
document_service = DocumentService(ollama_client, vector_store)
rag_service = RagService(ollama_client, vector_store)

app = FastAPI(title="RAG Chatbot API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, FRONTEND_ORIGIN.replace("localhost", "127.0.0.1")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


@app.get("/api/health")
def health():
    return {"status": "ok", "ollama": ollama_client.health()}


@app.get("/api/documents")
def list_documents():
    return {"documents": document_service.list_documents()}


@app.post("/api/documents", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        result = document_service.add(file.filename or "", content)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OllamaUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo indexar el documento. Comprueba el espacio disponible, "
                "los permisos de la carpeta de datos y la dimensión del modelo de embeddings."
            ),
        ) from exc
    finally:
        await file.close()


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str):
    if not document_id.isalnum():
        raise HTTPException(status_code=400, detail="Identificador de documento no válido.")
    if not document_service.delete(document_id):
        raise HTTPException(status_code=404, detail="No se encontró el documento.")
    return {"deleted": True, "id": document_id}


@app.post("/api/chat")
def chat(request: ChatRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Escribe una pregunta antes de enviarla.")
    try:
        return rag_service.answer(question)
    except OllamaUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Falló la recuperación local. Comprueba el índice Chroma y la configuración del modelo.",
        ) from exc
