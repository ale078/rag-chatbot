import chromadb

from .config import CHROMA_DIR


class ChromaStore:
    def __init__(self, path=CHROMA_DIR):
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            name="documents", metadata={"hnsw:space": "cosine"}
        )

    def add(self, document_id: str, texts: list[str], embeddings: list[list[float]],
            metadatas: list[dict]) -> None:
        ids = [f"{document_id}:{item['chunk_index']}" for item in metadatas]
        self.collection.add(ids=ids, documents=texts, embeddings=embeddings,
                            metadatas=metadatas)

    def search(self, embedding: list[float], limit: int) -> list[dict]:
        result = self.collection.query(query_embeddings=[embedding], n_results=limit,
                                       include=["documents", "metadatas", "distances"])
        documents = result.get("documents", [[]])[0]
        metadata = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [{"text": text, "metadata": meta, "distance": distance}
                for text, meta, distance in zip(documents, metadata, distances)]

    def delete(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})

    def count(self) -> int:
        return self.collection.count()
