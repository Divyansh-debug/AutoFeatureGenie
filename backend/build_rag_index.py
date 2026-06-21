"""
Script to build (or rebuild) the RAG vector index from domain documents.
Run this once before starting the backend, or any time you add new docs to domain_docs/.

Usage:
    python backend/build_rag_index.py [--force]
"""

import os
import sys

# Ensure project root is in the path when called from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rag_engine import RAGEngine

force = "--force" in sys.argv

rag = RAGEngine("domain_docs")
rag.load_and_index(force_reindex=force)

print("✅ RAG index built/refreshed successfully.")
print(f"   Using ChromaDB: {rag._use_chroma}")
print(
    f"   Persist path:   {os.path.abspath('data/chroma_db') if rag._use_chroma else 'backend/vectorstore.pkl'}"
)
