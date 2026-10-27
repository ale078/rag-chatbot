# Plan de integración — RAG Chatbot

- **Backend:** `services/api`; iniciar: `uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000`; puerto `8000`; build: `python -m compileall services/api/app`; health: `GET /api/health`.
- **Frontend:** `services/web`; dev: `npm --prefix services/web run dev`; build: `npm --prefix services/web run build`; API seam: `services/web/src/api/index.ts`. El MVP ya utiliza la API HTTP local; no hay clientes mock ni datos simulados que eliminar.
- **Rutas API:** `GET /api/health`; `GET /api/documents`; `POST /api/documents` (multipart field `file`); `DELETE /api/documents/{document_id}`; `POST /api/chat` (JSON `{ "question": "..." }`).
- **Datos:** Chroma persistente local + documentos locales en `data/`; no se usa PostgreSQL/Azure SQL, por lo tanto no aplica migración relacional. No agregar datos semilla.
- **Modelos:** Ollama local, configurado por `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL`, `OLLAMA_EMBED_MODEL`; el API responde 503 si la dependencia/modelo falta.
- **Servicios:** `web` (Essential), `api` (Essential), Ollama local (Essential; dependencia externa local).
- **Pruebas:** `python -m pytest services/api/tests`; build web: `npm --prefix services/web run build`.
