import os
from pathlib import Path

from dotenv import load_dotenv

API_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(API_ROOT / ".env")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


DATA_DIR = Path(os.getenv("DATA_DIR", str(API_ROOT.parents[1] / "data"))).expanduser().resolve()
DOCUMENTS_DIR = DATA_DIR / "documents"
CHROMA_DIR = DATA_DIR / "chroma"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:7b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
MAX_UPLOAD_BYTES = _int_env("MAX_UPLOAD_BYTES", 20_000_000)
CHUNK_SIZE = _int_env("CHUNK_SIZE", 900)
CHUNK_OVERLAP = _int_env("CHUNK_OVERLAP", 150)
TOP_K = _int_env("TOP_K", 5)
RELEVANCE_DISTANCE = _float_env("RELEVANCE_DISTANCE", 0.45)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}
