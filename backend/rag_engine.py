import os
import pickle
from sentence_transformers import SentenceTransformer
import faiss

# 1. Load embedding model (MiniLM is fast & good)
model = SentenceTransformer("all-MiniLM-L6-v2")

class RAGEngine:
    def __init__(self, doc_folder: str):
        self.doc_folder = doc_folder
        self.index = None
        self.text_chunks = []
        self.id_to_text = {}

    def load_and_split_docs(self):
        """Reads all .txt files and splits them into 300-character chunks"""
        from pathlib import Path
        for filepath in Path(self.doc_folder).glob("*.txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
                chunks = [text[i:i+300] for i in range(0, len(text), 300)]
                self.text_chunks.extend(chunks)

    def embed_and_store(self):
        """Embeds all chunks and stores them in FAISS"""
        embeddings = model.encode(self.text_chunks)
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        self.id_to_text = {i: chunk for i, chunk in enumerate(self.text_chunks)}

        save_path = os.path.join("backend", "vectorstore.pkl")
        with open(save_path, "wb") as f:
            pickle.dump((self.index, self.id_to_text), f)

    def load_index(self):
        """Loads the stored FAISS index and id->text map"""
        load_path = os.path.join("backend", "vectorstore.pkl")
        with open(load_path, "rb") as f:
            self.index, self.id_to_text = pickle.load(f)

    def search(self, query: str, top_k: int = 3):
        """Returns top-k most relevant chunks for a query"""
        query_vec = model.encode([query])
        D, I = self.index.search(query_vec, top_k)
        return [self.id_to_text[i] for i in I[0] if i != -1]


# ✅ Helper function for LLM prompt context injection
def fetch_context_from_rag(query: str, top_k: int = 3) -> str:
    rag = RAGEngine("domain_docs")
    rag.load_index()
    results = rag.search(query, top_k=top_k)
    return "\n\n".join(results)
