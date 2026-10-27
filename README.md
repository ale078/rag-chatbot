# Cuaderno — chat local con documentos

Aplicación local de recuperación aumentada (RAG): conversa en español con PDF, DOCX, TXT y Markdown,
con citas por archivo y página cuando está disponible. Si no encuentra evidencia relacionada, ofrece
una respuesta de conocimiento general marcada explícitamente como **sin respaldo en los documentos**.
No requiere login, Azure, API keys ni proveedores cloud. Los documentos, embeddings y conversaciones
se quedan en local; el historial vive sólo en la sesión abierta del navegador.

## Requisitos

- Python 3.11 o posterior
- Node.js 18 o posterior y npm
- [Ollama](https://ollama.com/) instalado y en ejecución

Descarga un modelo de conversación y uno de embeddings (pueden ser diferentes):

```sh
ollama pull nomic-embed-text
```

El modelo de chat predeterminado es `qwen2.5:7b`; si aún no lo tienes, descárgalo con
`ollama pull qwen2.5:7b`. Los nombres son configurables: `OLLAMA_CHAT_MODEL` y
`OLLAMA_EMBED_MODEL`. Ajusta el modelo de chat al tamaño que admita tu equipo. La aplicación
usa `/api/chat` y `/api/embed` de Ollama.

## Iniciar en desarrollo

En dos terminales, desde la raíz:

**API**

```sh
python -m venv services/api/.venv
# Windows PowerShell:
services/api/.venv/Scripts/Activate.ps1
# macOS/Linux: source services/api/.venv/bin/activate
python -m pip install -r services/api/requirements.txt
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000
```

**Web**

```sh
npm --prefix services/web install
npm --prefix services/web run dev
```

Abre la URL que Vite indique (normalmente http://localhost:5173). La API escucha sólo en `127.0.0.1`.
Documentación interactiva de la API: http://127.0.0.1:8000/docs.

## Configuración

La API toma configuración del entorno (se puede copiar `services/api/.env.example` a
`services/api/.env`; el servidor carga ese archivo automáticamente):

| Variable | Predeterminado | Uso |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Servicio Ollama local |
| `OLLAMA_CHAT_MODEL` | `qwen2.5:7b` | Modelo generativo |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Modelo de embeddings |
| `DATA_DIR` | `./data` en la raíz | Archivos fuente y persistencia Chroma |
| `MAX_UPLOAD_BYTES` | `20000000` | Tamaño máximo (20 MB) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `900` / `150` | Fragmentación de texto |
| `TOP_K` / `RELEVANCE_DISTANCE` | `5` / `0.45` | Recuperación y umbral cosine-distance |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Origen CORS permitido |

El directorio `data/` está ignorado por Git. Los PDF escaneados no se procesan (no hay OCR).

## Funcionalidades

- Carga, extracción, fragmentación e indexación semántica de PDF, DOCX, TXT y Markdown.
- Biblioteca de documentos con estado, fragmentos y eliminación de fuente + índice.
- Chat con citas de origen y página para respuestas recuperadas.
- Fallback de Ollama claramente advertido y sin citas cuando no hay fragmentos relevantes.
- Mensajes útiles si FastAPI, Ollama o el modelo local no están disponibles.
- Sin persistencia de chat y sin transmisión del contenido a servicios externos.

## Pruebas y compilación

```sh
python -m pip install -r services/api/requirements.txt
python -m pytest services/api/tests
npm --prefix services/web install
npm --prefix services/web run build
```

Las pruebas Python usan dobles locales y no necesitan Ollama activo.
