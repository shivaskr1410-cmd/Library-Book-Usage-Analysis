"""MySQL connection and database initialization helpers."""
import os
import mysql.connector
from config import DB_CONFIG

SCHEMA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql", "schema.sql")


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Create/reset the database objects using sql/schema.sql."""
    cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()
    try:
        with open(SCHEMA_FILE, encoding="utf-8") as f:
            script = f.read()
        for stmt in script.split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)
        conn.commit()
    finally:
        cur.close()
        conn.close()
