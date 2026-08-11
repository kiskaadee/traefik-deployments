import os
import sqlite3

DB_PATH = "/app/db/authme.db"
DB_READY = False

def get_db():
    # Set a 5-second busy timeout for concurrent write queuing
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    # Enable Write-Ahead Logging (WAL) for concurrent read/write optimization
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create roles table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            username VARCHAR(255) PRIMARY KEY,
            role VARCHAR(50) NOT NULL DEFAULT 'player'
        )
    """)
    
    # Create reset requests table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reset_requests (
            username VARCHAR(255) PRIMARY KEY,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Seed default admins
    cursor.execute("""
        INSERT OR IGNORE INTO user_roles (username, role) 
        VALUES ('kiskaadee', 'admin')
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO user_roles (username, role) 
        VALUES ('admin', 'admin')
    """)
    
    conn.commit()
    conn.close()

def check_db_ready() -> bool:
    global DB_READY
    if DB_READY:
        return True
        
    # Check if the database file exists first (non-blocking file check)
    if not os.path.exists(DB_PATH):
        return False
        
    try:
        # Check if authme table exists
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='authme'")
        table_exists = cursor.fetchone() is not None
        conn.close()
        
        if table_exists:
            # Run our auxiliary table initializations
            init_db()
            DB_READY = True
            return True
    except Exception:
        # Ignore errors during initial boot phase
        pass
        
    return False
