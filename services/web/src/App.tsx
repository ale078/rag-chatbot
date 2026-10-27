import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  ArrowUp, BookOpen, Check, FileText, FileUp, LoaderCircle, MessageSquareText,
  Plus, ShieldCheck, Sparkles, Trash2, TriangleAlert,
} from "lucide-react";
import { api, type ChatResult, type DocumentItem } from "./api";

type Message = { id: string; role: "user" | "assistant"; text: string; result?: ChatResult };
const greeting: Message = {
  id: "welcome",
  role: "assistant",
  text: "¡Hola! Soy tu asistente de documentos. Añade archivos a tu biblioteca y pregúntame lo que quieras encontrar.",
};

function App() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [messages, setMessages] = useState<Message[]>([greeting]);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [ollamaOnline, setOllamaOnline] = useState<boolean | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const endOfChat = useRef<HTMLDivElement>(null);

  async function refreshDocuments() {
    try {
      setDocuments(await api.listDocuments());
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo obtener la biblioteca.");
    }
  }

  useEffect(() => {
    void refreshDocuments();
    void api.health().then((health) => setOllamaOnline(health.ollama.available)).catch(() => setOllamaOnline(false));
  }, []);

  useEffect(() => {
    endOfChat.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function upload(file?: File) {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await api.uploadDocument(file);
      await refreshDocuments();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo cargar el archivo.");
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function removeDocument(document: DocumentItem) {
    if (!window.confirm(`¿Eliminar “${document.filename}” y sus fragmentos indexados?`)) return;
    setError("");
    try {
      await api.deleteDocument(document.id);
      setDocuments((current) => current.filter((item) => item.id !== document.id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo eliminar el documento.");
    }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    const text = question.trim();
    if (!text || busy) return;
    setQuestion("");
    setError("");
    setMessages((current) => [...current, { id: crypto.randomUUID(), role: "user", text }]);
    setBusy(true);
    try {
      const result = await api.chat(text);
      setMessages((current) => [...current, {
        id: crypto.randomUUID(), role: "assistant", text: result.answer, result,
      }]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo obtener una respuesta.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" aria-label="Cuaderno, inicio">
          <span className="brand-mark"><BookOpen size={19} strokeWidth={2.2} /></span>
          <span>cuaderno<span className="brand-period">.</span></span>
        </a>
        <button className="new-chat" onClick={() => setMessages([greeting])}>
          <Plus size={17} /> Nueva conversación
        </button>
        <div className="library-heading">
          <span>TU BIBLIOTECA</span>
          <span className="doc-count">{documents.length}</span>
        </div>
        <div className="document-list">
          {documents.length === 0 ? (
            <div className="empty-library"><FileText size={18} /><span>Tus documentos aparecerán aquí.</span></div>
          ) : documents.map((document) => (
            <div className="document-row" key={document.id}>
              <span className="file-icon"><FileText size={16} /></span>
              <div className="document-info">
                <span className="document-name" title={document.filename}>{document.filename}</span>
                <span className="document-meta"><Check size={11} /> {document.chunks} fragmentos</span>
              </div>
              <button className="icon-button delete-button" title={`Eliminar ${document.filename}`}
                aria-label={`Eliminar ${document.filename}`} onClick={() => void removeDocument(document)}>
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
        <div className="sidebar-bottom">
          <div className="privacy-note"><ShieldCheck size={16} /><span>Tus archivos se quedan en este dispositivo.</span></div>
          <div className="connection">
            <span className={`status-dot ${ollamaOnline === false ? "offline" : ""}`} />
            {ollamaOnline === null ? "Comprobando Ollama…" : ollamaOnline ? "Ollama conectado" : "Ollama sin conexión"}
          </div>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="topbar-label"><MessageSquareText size={16} /><span>Chat</span></div>
          <div className="local-badge"><span /> PRIVADO Y LOCAL</div>
        </header>

        <div className="chat-scroll">
          <div className="chat-content">
            <div className="welcome-block">
              <div className="eyebrow"><Sparkles size={14} /> TU ESPACIO DE CONOCIMIENTO</div>
              <h1>Piensa con tus<br /><span>documentos.</span></h1>
              <p>Encuentra respuestas, conecta ideas y vuelve a la fuente.</p>
            </div>

            {documents.length === 0 && (
              <button className="upload-card" onClick={() => fileInput.current?.click()} disabled={uploading}
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => { event.preventDefault(); void upload(event.dataTransfer.files[0]); }}>
                <span className="upload-icon">{uploading ? <LoaderCircle className="spin" size={20} /> : <FileUp size={20} />}</span>
                <span className="upload-copy"><strong>{uploading ? "Indexando documento…" : "Empieza con un documento"}</strong>
                  <small>Arrastra o elige un PDF, DOCX, TXT o Markdown</small></span>
                <span className="upload-action">Añadir archivo <span>↗</span></span>
              </button>
            )}

            <div className="messages" aria-live="polite">
              {messages.map((message) => (
                <article className={`message ${message.role}`} key={message.id}>
                  {message.role === "assistant" && <div className="assistant-avatar"><Sparkles size={15} /></div>}
                  <div className="message-body">
                    {message.result?.grounding === "fallback" && (
                      <div className="fallback-alert"><TriangleAlert size={15} />
                        <span>No encontré respaldo en tus documentos. Esta respuesta usa conocimiento general y puede no estar verificada.</span>
                      </div>
                    )}
                    <p>{message.text}</p>
                    {message.result?.grounding === "documents" && message.result.citations.length > 0 && (
                      <div className="citations"><span className="citation-label">FUENTES</span>
                        {message.result.citations.map((citation, index) => (
                          <span className="citation-chip" key={`${citation.document_id}-${citation.page}-${index}`}>
                            <FileText size={12} /> {citation.filename}{citation.page ? ` · pág. ${citation.page}` : ""}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </article>
              ))}
              {busy && <div className="thinking"><span /><span /><span /> <small>Buscando en tus documentos…</small></div>}
              <div ref={endOfChat} />
            </div>
          </div>
        </div>

        <div className="composer-wrap">
          {error && <div className="error-banner" role="alert"><TriangleAlert size={15} /><span>{error}</span>
            <button onClick={() => setError("")} aria-label="Cerrar error">×</button></div>}
          <form className="composer" onSubmit={(event) => void sendMessage(event)}>
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void sendMessage(event); } }}
              placeholder="Pregunta algo sobre tus documentos…" rows={1} maxLength={4000} aria-label="Tu pregunta" />
            <button className="composer-upload" type="button" onClick={() => fileInput.current?.click()}
              title="Añadir documento" aria-label="Añadir documento"><Plus size={19} /></button>
            <button className="send-button" type="submit" disabled={!question.trim() || busy} title="Enviar pregunta" aria-label="Enviar pregunta">
              {busy ? <LoaderCircle className="spin" size={17} /> : <ArrowUp size={18} />}
            </button>
          </form>
          <p className="composer-hint">La IA puede cometer errores. Comprueba las citas antes de confiar en una respuesta.</p>
        </div>
      </section>

      <input ref={fileInput} className="visually-hidden" type="file" accept=".pdf,.docx,.txt,.md,.markdown"
        onChange={(event) => void upload(event.target.files?.[0])} />
      {uploading && <div className="upload-progress"><LoaderCircle className="spin" size={15} /> Indexando {documents.length ? "nuevo documento" : "documento"}…</div>}
    </main>
  );
}

export default App;
