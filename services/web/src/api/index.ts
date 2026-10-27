export interface DocumentItem {
  id: string;
  filename: string;
  status: string;
  chunks: number;
  uploaded_at: string;
}

export interface Citation {
  filename: string;
  page: number | null;
  document_id: string | null;
}

export interface ChatResult {
  answer: string;
  grounding: "documents" | "fallback";
  citations: Citation[];
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new Error("No se pudo conectar con la API local. Comprueba que FastAPI esté iniciado en el puerto 8000.");
  }
  if (!response.ok) {
    let message = `La solicitud falló (${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // Use the status message if the server response isn't JSON.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  listDocuments: async () => (await request<{ documents: DocumentItem[] }>("/api/documents")).documents,
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentItem>("/api/documents", { method: "POST", body: form });
  },
  deleteDocument: (id: string) =>
    request<{ deleted: boolean }>(`/api/documents/${encodeURIComponent(id)}`, { method: "DELETE" }),
  chat: (question: string) =>
    request<ChatResult>("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
  health: () => request<{ status: string; ollama: { available: boolean } }>("/api/health"),
};
