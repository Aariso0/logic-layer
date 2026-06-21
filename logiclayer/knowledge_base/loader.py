import os
import json
import sqlite3
from pathlib import Path
from logiclayer.knowledge_base.schema import Fact, Source

DB_PATH = Path("local-knowledge-base/knowledge_base.db")
FACTS_DIR = Path("local-knowledge-base/facts")
SOURCES_DIR = Path("local-knowledge-base/sources")

def check_orphan_facts():
    """Validates that every fact JSON points to a source_id that actually exists."""
    print("🔍 Running orphan-fact check...")
    
    valid_source_ids = set()
    for source_file in SOURCES_DIR.glob("*.json"):
        with open(source_file, "r", encoding="utf-8") as f:
            source = Source(**json.load(f))
            valid_source_ids.add(source.source_id)
            
    has_orphans = False
    FACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    for fact_file in FACTS_DIR.glob("*.json"):
        with open(fact_file, "r", encoding="utf-8") as f:
            fact = Fact(**json.load(f))
            if fact.source_id not in valid_source_ids:
                print(f"❌ Error: Orphan fact found in {fact_file.name}! Source ID '{fact.source_id}' does not exist.")
                has_orphans = True
                
    if not has_orphans:
        print("✅ Orphan-fact check passed! Every fact successfully maps to a valid source.")
    else:
        raise ValueError("Database load aborted due to orphan facts.")

def init_db():
    """Initializes the SQLite database tables matching your JSON properties."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            source_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT,
            domain TEXT,
            category TEXT,
            retrieved_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            fact_id TEXT PRIMARY KEY,
            claim TEXT NOT NULL,
            value TEXT NOT NULL,
            source_id TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES sources (source_id)
        )
    """)
    
    conn.commit()
    conn.close()

def load_data():
    """Loads validated JSON files into the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    sources_count = 0
    for source_file in SOURCES_DIR.glob("*.json"):
        with open(source_file, "r", encoding="utf-8") as f:
            source = Source(**json.load(f))
            cursor.execute(
                "INSERT OR REPLACE INTO sources VALUES (?, ?, ?, ?, ?, ?)",
                (source.source_id, source.name, source.url, source.domain, source.category, source.retrieved_at)
            )
            sources_count += 1
            
    facts_count = 0
    for fact_file in FACTS_DIR.glob("*.json"):
        with open(fact_file, "r", encoding="utf-8") as f:
            fact = Fact(**json.load(f))
            cursor.execute(
                "INSERT OR REPLACE INTO facts VALUES (?, ?, ?, ?)",
                (fact.fact_id, fact.claim, fact.value, fact.source_id)
            )
            facts_count += 1
            
    conn.commit()
    print(f"💾 Successfully loaded {sources_count} sources and {facts_count} facts into database at: {DB_PATH}")
    conn.close()

if __name__ == "__main__":
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    FACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        check_orphan_facts()
        init_db()
        load_data()
    except Exception as e:
        print(f"💥 Execution failed: {e}")