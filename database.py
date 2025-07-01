import sqlite3
from datetime import datetime

DATABASE_NAME = "jarvis_history.db"

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Enable foreign key support to ensure cascade deletes work
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, role TEXT NOT NULL, content TEXT NOT NULL,
            timestamp TEXT, FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def save_chat_session(title, messages):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_sessions (title) VALUES (?)", (title,))
    session_id = cursor.lastrowid
    cursor.executemany("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                       [(session_id, m['role'], m['content'], m.get('timestamp', '')) for m in messages])
    conn.commit()
    conn.close()
    return session_id

def update_chat_session(session_id, new_title, messages):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?",
                   (new_title, datetime.now(), session_id))
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.executemany("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                       [(session_id, m['role'], m['content'], m.get('timestamp', '')) for m in messages])
    conn.commit()
    conn.close()

def get_chat_sessions():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, updated_at FROM chat_sessions ORDER BY updated_at DESC")
    sessions = cursor.fetchall()
    conn.close()
    return sessions

def get_messages_for_session(session_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    messages = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1], "timestamp": row[2]} for row in messages]

# --- NEW FUNCTIONS ---
def delete_chat_session(session_id):
    """Deletes a chat session and all its associated messages."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # With "ON DELETE CASCADE" enabled, this will also delete all associated messages
    cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    print(f"Deleted chat session with ID: {session_id}")

def rename_chat_session(session_id, new_title):
    """Renames a specific chat session."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?",
                   (new_title, datetime.now(), session_id))
    conn.commit()
    conn.close()
    print(f"Renamed chat session {session_id} to '{new_title}'")