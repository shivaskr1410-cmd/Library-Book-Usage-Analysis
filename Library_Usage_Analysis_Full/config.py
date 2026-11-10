"""Application configuration. Environment variables override these defaults."""
import os

DB_CONFIG = {
    "host": os.getenv("LIB_DB_HOST", "localhost"),
    "port": int(os.getenv("LIB_DB_PORT", "3306")),
    "user": os.getenv("LIB_DB_USER", "root"),
    "password": os.getenv("LIB_DB_PASSWORD", "shiva@123"),
    "database": os.getenv("LIB_DB_NAME", "library_db"),
}

LOAN_PERIOD_DAYS = int(os.getenv("LIB_LOAN_DAYS", "14"))
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

