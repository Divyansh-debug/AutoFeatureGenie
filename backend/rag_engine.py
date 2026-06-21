"""
RAG Engine — upgraded with LangChain RecursiveCharacterTextSplitter + ChromaDB
Replaces naive 300-char slicing with proper semantic chunking and a persistent
vector store.
"""
import os
from pathlib import Path
from typing import List

from src.utils.logger import logger

# ---------------------------------------------------------------------------
# Optional heavy imports — guarded so the app still starts if packages are
# missing (they will be installed via pyproject.toml).
# ---------------------------------------------------------------------------
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain / ChromaDB not installed; RAG will use legacy FAISS fallback.")

try:
    import faiss
    import pickle
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


# ---------------------------------------------------------------------------
# ChromaDB-backed RAG engine (primary)
# ---------------------------------------------------------------------------

CHROMA_PERSIST_DIR = os.path.join("data", "chroma_db")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


class RAGEngine:
    """
    Semantic RAG engine backed by ChromaDB.
    Falls back to FAISS if LangChain is unavailable.
    """

    def __init__(self, doc_folder: str = "domain_docs"):
        self.doc_folder = doc_folder
        self._use_chroma = LANGCHAIN_AVAILABLE
        self._vectorstore = None
        self._legacy_index = None
        self._legacy_id_to_text: dict = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_and_index(self, force_reindex: bool = False) -> None:
        """
        Load domain documents, split them intelligently, embed, and persist.
        Skips re-indexing if the vector store already exists (unless forced).
        """
        if self._use_chroma:
            self._chroma_load_and_index(force_reindex)
        else:
            self._legacy_load_and_index()

    def load_index(self) -> None:
        """Load an existing persisted index (for backward compat)."""
        if self._use_chroma:
            self._chroma_load()
        else:
            self._legacy_load()

    def search(self, query: str, top_k: int = 3) -> List[str]:
        """Return top-k most relevant text chunks for *query*."""
        if self._use_chroma and self._vectorstore is not None:
            return self._chroma_search(query, top_k)
        elif not self._use_chroma and self._legacy_index is not None:
            return self._legacy_search(query, top_k)
        else:
            logger.warning("RAG index not loaded; returning empty context.")
            return []

    # ------------------------------------------------------------------
    # ChromaDB implementation
    # ------------------------------------------------------------------

    def _chroma_load_and_index(self, force_reindex: bool) -> None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

        # If persisted store exists and not forcing, just load it
        if not force_reindex and os.path.exists(os.path.join(CHROMA_PERSIST_DIR, "chroma.sqlite3")):
            logger.info("ChromaDB store found — loading from disk.")
            self._vectorstore = Chroma(
                persist_directory=CHROMA_PERSIST_DIR,
                embedding_function=embeddings,
            )
            return

        logger.info("Building ChromaDB index from domain documents…")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=64,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        all_docs = []
        for filepath in Path(self.doc_folder).glob("*.txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            chunks = splitter.create_documents([text], metadatas=[{"source": filepath.name}])
            all_docs.extend(chunks)

        if not all_docs:
            logger.warning(f"No .txt files found in '{self.doc_folder}'. RAG context will be empty.")
            return

        self._vectorstore = Chroma.from_documents(
            documents=all_docs,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
        )
        self._vectorstore.persist()
        logger.info(f"ChromaDB indexed {len(all_docs)} chunks from {self.doc_folder}.")

    def _chroma_load(self) -> None:
        """Load an already-persisted ChromaDB store."""
        if not os.path.exists(CHROMA_PERSIST_DIR):
            logger.warning("ChromaDB persist dir not found — running full index build.")
            self._chroma_load_and_index(force_reindex=False)
            return
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        self._vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
        )
        logger.info("ChromaDB store loaded.")

    def _chroma_search(self, query: str, top_k: int) -> List[str]:
        results = self._vectorstore.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]

    # ------------------------------------------------------------------
    # Legacy FAISS fallback
    # ------------------------------------------------------------------

    def _legacy_load_and_index(self) -> None:
        """Naive 300-char splitting + FAISS (fallback when LangChain absent)."""
        if not FAISS_AVAILABLE:
            logger.error("Neither LangChain nor FAISS is available. RAG disabled.")
            return
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        chunks = []
        for filepath in Path(self.doc_folder).glob("*.txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            chunks.extend([text[i : i + 300] for i in range(0, len(text), 300)])
        if not chunks:
            return
        embeddings = _model.encode(chunks)
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        self._legacy_index = index
        self._legacy_id_to_text = {i: c for i, c in enumerate(chunks)}
        save_path = os.path.join("backend", "vectorstore.pkl")
        with open(save_path, "wb") as f:
            pickle.dump((index, self._legacy_id_to_text), f)
        logger.info(f"FAISS index built with {len(chunks)} chunks.")

    def _legacy_load(self) -> None:
        load_path = os.path.join("backend", "vectorstore.pkl")
        if not os.path.exists(load_path):
            logger.warning("vectorstore.pkl not found — running legacy index build.")
            self._legacy_load_and_index()
            return
        with open(load_path, "rb") as f:
            self._legacy_index, self._legacy_id_to_text = pickle.load(f)
        logger.info("FAISS index loaded from vectorstore.pkl.")

    def _legacy_search(self, query: str, top_k: int) -> List[str]:
        if not FAISS_AVAILABLE:
            return []
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        query_vec = _model.encode([query])
        D, I = self._legacy_index.search(query_vec, top_k)
        return [self._legacy_id_to_text[i] for i in I[0] if i != -1]


# ---------------------------------------------------------------------------
# Module-level singleton helper (used by feature_engine.py)
# ---------------------------------------------------------------------------

def fetch_context_from_rag(query: str, top_k: int = 3) -> str:
    """Convenience function: create a fresh RAGEngine, load index, search."""
    rag = RAGEngine("domain_docs")
    rag.load_index()
    results = rag.search(query, top_k=top_k)
    return "\n\n".join(results)
