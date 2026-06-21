import sqlite3
import numpy as np
import faiss
from pathlib import Path
from logiclayer.knowledge_base.embeddings import generate_simple_embedding

# Setup paths relative to the project root
DB_PATH = Path("local-knowledge-base/knowledge_base.db")
INDEX_PATH = Path("local-knowledge-base/embeddings/faiss_index.bin")
MAP_PATH = Path("local-knowledge-base/embeddings/fact_mapping.txt")

def check_local_db(claim: str):
    """
    Checks the local database for a claim.
    1. Tries an exact text match against the SQLite database first.
    2. Falls back to FAISS semantic vector search if no exact match is found.
    """
    print(f"\n🧐 Running verification pipeline for claim: '{claim}'")
    
    # Ensure database file exists
    if not DB_PATH.exists():
        print("❌ Error: Database file missing. Run loader.py first.")
        return None

    # ==========================================
    # STRATEGY 1: EXACT TEXT MATCH (SQLite)
    # ==========================================
    print("⚡ Step 1: Checking for exact text match in SQLite...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT f.fact_id, f.claim, f.value, s.name 
        FROM facts f
        JOIN sources s ON f.source_id = s.source_id
        WHERE LOWER(f.claim) = LOWER(?)
    """, (claim.strip(),))
    
    exact_match = cursor.fetchone()
    
    if exact_match:
        fact_id, matched_claim, value, source_name = exact_match
        print("🎯 Found an EXACT match in the database!")
        print("=" * 60)
        print(f"🆔 FACT ID      : {fact_id}")
        print(f"📝 CLAIM        : {matched_claim}")
        print(f"💡 DETAIL VALUE : {value}")
        print(f"📚 SOURCE       : {source_name}")
        print("=" * 60)
        conn.close()
        return exact_match

    # ==========================================
    # STRATEGY 2: SEMANTIC FALLBACK (FAISS)
    # ==========================================
    print("🔄 No exact match found. Falling back to Step 2: FAISS Semantic Search...")
    conn.close() # Close connection while processing vectors
    
    if not INDEX_PATH.exists() or not MAP_PATH.exists():
        print("⚠️ Semantic lookup failed: FAISS index or mappings missing. Run embeddings.py!")
        return None
        
    # Generate vector matrix for user input
    query_vector = generate_simple_embedding(claim).reshape(1, -1)
    
    # Read FAISS layers
    index = faiss.read_index(str(INDEX_PATH))
    distances, indices = index.search(query_vector, 1) # Get the closest neighbor
    
    # Load sequential ID mappings list
    with open(MAP_PATH, "r", encoding="utf-8") as f:
        fact_id_mapping = [line.strip() for line in f.readlines()]
        
    match_index = indices[0][0]
    distance_score = float(distances[0][0])
    
    if match_index < 0 or match_index >= len(fact_id_mapping):
        print("❌ Semantic lookup: No vector matches found.")
        return None
        
    matched_fact_id = fact_id_mapping[match_index]
    
    # Pull the semantic match info from SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.claim, f.value, s.name 
        FROM facts f
        JOIN sources s ON f.source_id = s.source_id
        WHERE f.fact_id = ?
    """, (matched_fact_id,))
    
    semantic_match = cursor.fetchone()
    conn.close()
    
    if semantic_match:
        matched_claim, value, source_name = semantic_match
        print("🤖 Found a SEMANTIC match via vector neighborhood layers!")
        print("=" * 60)
        print(f"🆔 FACT ID      : {matched_fact_id}")
        print(f"📝 CLOSEST CLAIM: {matched_claim}")
        print(f"💡 DETAIL VALUE : {value}")
        print(f"📚 SOURCE       : {source_name}")
        print(f"📊 DISTANCE SCORE: {distance_score:.4f}")
        print("=" * 60)
        return semantic_match
    else:
        print("❌ Vector entry exists, but corresponding row was missing from SQLite tables.")
        return None

if __name__ == "__main__":
    # Test 1: Test with an exact string match
    check_local_db("Python was created by Guido van Rossum")
    
    # Test 2: Test semantic fallback (using different words for the same idea)
    check_local_db("Who designed the python programming language")