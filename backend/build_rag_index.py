from rag_engine import RAGEngine

rag = RAGEngine("domain_docs")
rag.load_and_split_docs()
rag.embed_and_store()

print("✅ Vector index built and saved.")
