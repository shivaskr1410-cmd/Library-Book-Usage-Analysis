"""Command-line interface kept for testing/admin use."""
import argparse
from datetime import datetime
import db, library, analysis, seed_data


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


p = argparse.ArgumentParser(description="Library Book Usage Analysis System")
sub = p.add_subparsers(dest="cmd", required=True)
sub.add_parser("init-db")
sub.add_parser("seed")
sub.add_parser("books")
sub.add_parser("borrowers")
sub.add_parser("active")
sub.add_parser("overdue")
sub.add_parser("summary")
sub.add_parser("check")
sub.add_parser("report")
a = sub.add_parser("add-book"); a.add_argument("isbn"); a.add_argument("title"); a.add_argument("author"); a.add_argument("category"); a.add_argument("--copies", type=int, default=1)
a = sub.add_parser("add-borrower"); a.add_argument("name"); a.add_argument("roll_no")
a = sub.add_parser("issue"); a.add_argument("book_id", type=int); a.add_argument("borrower_id", type=int); a.add_argument("--date"); a.add_argument("--days", type=int)
a = sub.add_parser("return"); a.add_argument("loan_id", type=int); a.add_argument("--date")
args = p.parse_args()

try:
    if args.cmd == "init-db": db.init_db(); print("Database initialized/reset.")
    elif args.cmd == "seed": seed_data.seed()
    elif args.cmd == "books": print(library.list_books())
    elif args.cmd == "borrowers": print(library.list_borrowers())
    elif args.cmd == "active": print(library.active_loans())
    elif args.cmd == "overdue": print(library.overdue_loans())
    elif args.cmd == "summary": print(library.summary())
    elif args.cmd == "check": print(library.check_consistency())
    elif args.cmd == "report": print(analysis.generate_reports())
    elif args.cmd == "add-book": print("Book ID:", library.add_book(args.isbn, args.title, args.author, args.category, args.copies))
    elif args.cmd == "add-borrower": print("Borrower ID:", library.add_borrower(args.name, args.roll_no))
    elif args.cmd == "issue": print("Loan ID:", library.issue_book(args.book_id, args.borrower_id, parse_date(args.date), args.days))
    elif args.cmd == "return": print(library.return_book(args.loan_id, parse_date(args.date)))
except Exception as exc:
    print("ERROR:", exc)
    raise SystemExit(1)
