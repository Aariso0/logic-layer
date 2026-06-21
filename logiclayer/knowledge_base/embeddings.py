import sqlite3
import numpy as np
import faiss
from pathlib import Path

# Setup paths relative to the project root
DB_PATH = Path("local-knowledge-base/knowledge_base.db")
INDEX_PATH = Path("local-knowledge-base/embeddings/faiss_index.bin")
MAP_PATH = Path("local-knowledge-base/embeddings/fact_mapping.txt")

def generate_simple_embedding(text: str, dimensions: int = 128) -> np.ndarray:
    """
    A lightweight deterministic embedding simulator for local development.
    Converts text characters into a normalized vector array.
    """
    state = np.random.RandomState(sum(ord(c) for c in text) % 2**32)
    vector = state.randn(dimensions).astype('float32')
    return vector / np.linalg.norm(vector)  # Normalize for cosine similarity

def build_embeddings_index():
    """Reads facts from SQLite, generates vectors, and saves a FAISS index."""
    print("🤖 Initializing semantic embedding pipeline...")
    
    # Ensure output folder exists
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Read facts from SQLite database
    if not DB_PATH.exists():
        print(f"❌ Error: Database file not found at {DB_PATH}. Run loader.py first!")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT fact_id, claim FROM facts")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("⚠️ No facts found in the database to index.")
        return
        
    print(f"📖 Found {len(rows)} facts to process. Generating vectors...")
    
    fact_ids = []
    vectors = []
    
    # 2. Process text into vectors
    for fact_id, claim in rows:
        vector = generate_simple_embedding(claim)
        vectors.append(vector)
        fact_ids.append(fact_id)
        
    # Convert vector list to a contiguous float32 numpy matrix for FAISS
    vectors_matrix = np.vstack(vectors)
    dimensions = vectors_matrix.shape[1]
    
    # 3. Initialize and populate FAISS FlatL2 Index
    index = faiss.IndexFlatL2(dimensions)
    index.add(vectors_matrix)
    
    # 4. Persist index binary and ID mapping files to disk
    faiss.write_index(index, str(INDEX_PATH))
    
    with open(MAP_PATH, "w", encoding="utf-8") as f:
        for f_id in fact_ids:
            f.write(f"{f_id}\n")
            
    print(f"✅ Success! FAISS index saved at: {INDEX_PATH}")
    print(f"🗺️ Fact index mappings saved at: {MAP_PATH}")

if __name__ == "__main__":
    try:
        build_embeddings_index()
    except Exception as e:
        print(f"💥 Embedding generation failed: {e}")