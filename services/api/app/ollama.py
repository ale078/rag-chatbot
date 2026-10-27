import httpx

from .config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL
from .errors import OllamaUnavailable


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL,
                 chat_model: str = OLLAMA_CHAT_MODEL,
                 embed_model: str = OLLAMA_EMBED_MODEL):
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embed_model = embed_model

    def _post(self, path: str, payload: dict) -> dict:
        try:
            response = httpx.post(f"{self.base_url}{path}", json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            detail = ""
            try:
                detail = exc.response.json().get("error", "")
            except ValueError:
                pass
            raise OllamaUnavailable(
                f"Ollama rechazó la solicitud ({detail or exc.response.status_code}). "
                "Comprueba que el modelo configurado esté descargado."
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaUnavailable(
                "No se pudo conectar con Ollama. Inícialo y verifica OLLAMA_BASE_URL."
            ) from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        result = self._post("/api/embed", {"model": self.embed_model, "input": texts})
        vectors = result.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise OllamaUnavailable(
                f"Ollama no devolvió embeddings para {self.embed_model}. "
                "Verifica el nombre del modelo de embeddings."
            )
        return vectors

    def generate(self, prompt: str) -> str:
        result = self._post("/api/chat", {
            "model": self.chat_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        })
        answer = result.get("message", {}).get("content", "").strip()
        if not answer:
            raise OllamaUnavailable(
                f"Ollama devolvió una respuesta vacía. Comprueba el modelo {self.chat_model}."
            )
        return answer

    def health(self) -> dict:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=3)
            response.raise_for_status()
            names = {item.get("name", "")
                     for item in response.json().get("models", [])}
            chat_base = self.chat_model.split(":")[0]
            embed_base = self.embed_model.split(":")[0]
            return {
                "available": True,
                "chat_model_available": self.chat_model in names or any(
                    name.split(":")[0] == chat_base for name in names
                ),
                "embedding_model_available": self.embed_model in names or any(
                    name.split(":")[0] == embed_base for name in names
                ),
                "chat_model": self.chat_model,
                "embedding_model": self.embed_model,
            }
        except (httpx.HTTPError, ValueError):
            return {
                "available": False,
                "chat_model_available": False,
                "embedding_model_available": False,
                "chat_model": self.chat_model,
                "embedding_model": self.embed_model,
            }
