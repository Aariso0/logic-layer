<<<<<<< Updated upstream
<<<<<<< Updated upstream
#Log Infrastructure and seperate code with Log management
=======
#Log Management
>>>>>>> Stashed changes
=======
#Log Management
>>>>>>> Stashed changes

import os
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict

<<<<<<< Updated upstream
<<<<<<< Updated upstream
# Define paths relative to this project 
=======
# Define paths relative to this project setup
>>>>>>> Stashed changes
=======
# Define paths relative to this project setup
>>>>>>> Stashed changes
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "local-knowledge-base"))
DB_PATH = os.path.join(DB_DIR, "audit_logs.db")
JSON_LOG_PATH = os.path.join(DB_DIR, "pipeline_logs.jsonl")

<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
def is_connected(conn) :
    """Check if SQLite3 is connected, it is active and valid returns False otherwise"""

    try:
        conn.execute("SELECT 1;")
        return True
    
    except (sqlite3.ProgrammingError, sqlite3.OperationalError, sqlite3.Error):
        return False

    except AttributeError:
        return False

<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
def init_logger():
    """
    Ensures directory paths exist and creates the SQLite database tables if they haven't been initialized yet.
    """
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    os.makedirs(DB_DIR, exist_ok=True)
    

    connector = sqlite3.connect(DB_PATH)
    cursor = connector.cursor()
    
    # Table for tracking user sessions and queries
    cursor.execute
    (
        """
        CREATE TABLE IF NOT EXISTS queries 
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            query_text TEXT NOT NULL
        )
        """
    )
    
    # Table for capturing nested AI tool choices and execution payloads
    cursor.execute
    (
        """
        CREATE TABLE IF NOT EXISTS tool_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
=======
=======
>>>>>>> Stashed changes
    # Create local storage directory if missing
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Initialize SQLite schema with failure management
    sqlite3.Connection.is_connected = is_connected
    try:
        connector = sqlite3.connect(DB_PATH)

        if connector.is_connected():
            logging.info("SQLite3 database connection established successfully")
            
        else:
            logging.error("SQLite3 connection failed after opening")

    except sqlite3.Error as e:
        logging.critical(f"failed to open database file : {e}")


    cursor = connector.cursor()
    
    # Table for tracking user sessions and queries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            query_text TEXT NOT NULL
        )
    """)
    
    # Table for capturing nested AI tool choices and execution payloads
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            timestamp TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            arguments TEXT NOT NULL,
            result TEXT NOT NULL
        )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """
    )
=======
    """)
>>>>>>> Stashed changes
=======
    """)
>>>>>>> Stashed changes
    
    connector.commit()
    connector.close()

<<<<<<< Updated upstream
<<<<<<< Updated upstream
# Run initialization when this file is imported by the orchestrator
init_logger()


def log_query(session_id: str, query_text: str):
    """Logs the entry point raw text query into both SQLite and JSONL formats (since it was an option so i chose both)."""
    timestamp = datetime.utcnow().isoformat()
    

=======
=======
>>>>>>> Stashed changes
# Automatically run initialization when this file is imported by the orchestrator
init_logger()


def log_query(query_text: str):
    """Logs the entry point raw text query into both SQLite and JSONL formats."""
    timestamp = datetime.utcnow().isoformat()
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    # 1. SQLite Write
    try:
        connector = sqlite3.connect(DB_PATH)
        cursor = connector.cursor()
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        cursor.execute("INSERT INTO queries (session_id, timestamp, query_text) VALUES (?, ?, ?)",(session_id, timestamp, query_text))
        connector.commit()
        connector.close()

    except Exception as e:
        print(f"[Logger Error] SQLite query logging failed: {e}")


=======
=======
>>>>>>> Stashed changes
        cursor.execute(
            "INSERT INTO queries (timestamp, query_text) VALUES (?, ?)",
            (timestamp, query_text)
        )
        connector.commit()
        connector.close()
    except Exception as e:
        print(f"[Logger Error] SQLite query logging failed: {e}")

<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    # 2. JSONL Write (Appends structured logs cleanly line-by-line)
    try:
        log_entry = {
            "type": "user_query",
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            "session_id": session_id,
            "timestamp": timestamp,
            "query": query_text
        }

        with open(JSON_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

=======
=======
>>>>>>> Stashed changes
            "timestamp": timestamp,
            "query": query_text
        }
        with open(JSON_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    except Exception as e:
        print(f"[Logger Error] JSON query logging failed: {e}")


<<<<<<< Updated upstream
<<<<<<< Updated upstream
def log_tool_call(session_id: str, tool_name: str, arguments: Dict[str, Any], result: str):

    timestamp = datetime.utcnow().isoformat()
    args_json = json.dumps(arguments)
    

=======
=======
>>>>>>> Stashed changes
def log_tool_call(tool_name: str, arguments: Dict[str, Any], result: str):
    """Logs the inner step model tool selections into both SQLite and JSONL formats."""
    timestamp = datetime.utcnow().isoformat()
    args_json = json.dumps(arguments)
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    # 1. SQLite Write
    try:
        connector = sqlite3.connect(DB_PATH)
        cursor = connector.cursor()
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        cursor.execute("INSERT INTO tool_calls (session_id, timestamp, tool_name, arguments, result) VALUES (?, ?, ?, ?, ?)",(session_id, timestamp, tool_name, args_json, result))
        connector.commit()
        connector.close()

    except Exception as e:
        print(f"[Logger Error] SQLite tool logging failed: {e}")


=======
=======
>>>>>>> Stashed changes
        cursor.execute(
            "INSERT INTO tool_calls (timestamp, tool_name, arguments, result) VALUES (?, ?, ?, ?)",
            (timestamp, tool_name, args_json, result)
        )
        connector.commit()
        connector.close()
    except Exception as e:
        print(f"[Logger Error] SQLite tool logging failed: {e}")

<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    # 2. JSONL Write
    try:
        log_entry = {
            "type": "tool_execution",
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            "session_id": session_id,
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            "timestamp": timestamp,
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result
        }
        with open(JSON_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    
    except Exception as e:
        print(f"[Logger Error] JSON tool logging failed: {e}")
=======
    except Exception as e:
        print(f"[Logger Error] JSON tool logging failed: {e}")
>>>>>>> Stashed changes
=======
    except Exception as e:
        print(f"[Logger Error] JSON tool logging failed: {e}")
>>>>>>> Stashed changes
