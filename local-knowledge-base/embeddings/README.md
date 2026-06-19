# README — local-knowledge-base/embeddings/
#
# Vector index files for the local-check layer. Regenerated from the contents
# of ../facts/ + ../sources/ by scripts/db_updater.py. NOT committed to git
# (see .gitignore).
#
# Expected artifacts when present locally:
#   - chroma/                (ChromaDB persistent store)
#   - faiss.index + faiss.pkl (FAISS index + metadata, if backend == faiss)