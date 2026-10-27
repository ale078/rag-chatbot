# API local

Requiere Python 3.11+ y Ollama. Desde `services/api`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

El modelo de chat predeterminado es `qwen2.5:7b`; si ya tienes otro modelo instalado,
puedes ajustar `OLLAMA_CHAT_MODEL` en `.env`.

En macOS/Linux, activa el entorno con `source .venv/bin/activate`. Configura `OLLAMA_CHAT_MODEL`,
`OLLAMA_EMBED_MODEL`, `OLLAMA_BASE_URL` y `DATA_DIR` según tu instalación. Los archivos e índice
persistente se guardan bajo `data/` en la raíz y no se envían a proveedores cloud.

OpenAPI local: http://127.0.0.1:8000/docs. Pruebas: `python -m pytest`.
