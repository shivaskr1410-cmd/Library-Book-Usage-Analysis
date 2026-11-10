"""One-command database setup helper."""
import argparse
import db
import seed_data

parser = argparse.ArgumentParser(description="Set up the Library Usage Analysis database")
parser.add_argument("--reset", action="store_true", help="Reset tables before loading demo data")
args = parser.parse_args()

db.init_db()
print("Database/tables initialized.")
seed_data.seed()
print("Setup complete. Start the frontend with: streamlit run app.py")
