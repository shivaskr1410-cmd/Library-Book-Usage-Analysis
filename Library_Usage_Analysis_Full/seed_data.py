"""Load realistic demo data: books, borrowers and about 12 months of circulation."""
import random
from datetime import date, timedelta
from db import get_connection
from config import LOAN_PERIOD_DAYS

BOOKS = [
    ("9780131103627", "The C Programming Language", "Kernighan & Ritchie", "Programming", 4),
    ("9780132350884", "Clean Code", "Robert C. Martin", "Programming", 5),
    ("9781491957660", "Python for Data Analysis", "Wes McKinney", "Data Science", 5),
    ("9781449369415", "Python Data Science Handbook", "Jake VanderPlas", "Data Science", 3),
    ("9780262033848", "Introduction to Algorithms", "Cormen et al.", "Computer Science", 4),
    ("9780134685991", "Effective Java", "Joshua Bloch", "Programming", 3),
    ("9780073523323", "Database System Concepts", "Silberschatz et al.", "Databases", 4),
    ("9780321884497", "Learning SQL", "Alan Beaulieu", "Databases", 3),
    ("9780140449136", "Crime and Punishment", "Fyodor Dostoevsky", "Fiction", 3),
    ("9780061120084", "To Kill a Mockingbird", "Harper Lee", "Fiction", 4),
    ("9780743273565", "The Great Gatsby", "F. Scott Fitzgerald", "Fiction", 3),
    ("9780553380163", "A Brief History of Time", "Stephen Hawking", "Science", 3),
    ("9780062316097", "Sapiens", "Yuval Noah Harari", "History", 4),
    ("9780735211292", "Atomic Habits", "James Clear", "Self-Help", 5),
    ("9780132126953", "Computer Networks", "Andrew Tanenbaum", "Computer Science", 4),
    ("9780134494166", "Artificial Intelligence: A Modern Approach", "Russell & Norvig", "AI", 3),
    ("9781492051367", "Designing Data-Intensive Applications", "Martin Kleppmann", "Data Engineering", 3),
    ("9781617294945", "Spring in Action", "Craig Walls", "Java", 3),
    ("9781617292231", "Head First Java", "Kathy Sierra", "Java", 4),
    ("9780135166307", "Effective Python", "Brett Slatkin", "Python", 4),
]

NAMES = [
    "Aarav Sharma", "Diya Reddy", "Vikram Kumar", "Ananya Rao", "Rohit Varma",
    "Sneha Patel", "Karthik Naidu", "Meera Iyer", "Arjun Singh", "Priya Nair",
    "Suresh Babu", "Lakshmi Devi", "Ravi Teja", "Divya Sri", "Manoj Kumar",
    "Harini R", "Nikhil Reddy", "Keerthi S", "Aditya Rao", "Pooja K",
    "Sai Charan", "Tanvi M", "Abhinav G", "Ishita P",
]


def seed(n_loans=360, seed_value=42):
    random.seed(seed_value)
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM books")
        if cur.fetchone()[0] > 0:
            print("Database already contains data. Run `python setup.py --reset` if you want a fresh demo database.")
            return

        book_ids = {}
        for isbn, title, author, cat, copies in BOOKS:
            cur.execute(
                "INSERT INTO books (isbn,title,author,category,total_copies,copies_available) VALUES (%s,%s,%s,%s,%s,%s)",
                (isbn, title, author, cat, copies, copies),
            )
            book_ids[cur.lastrowid] = copies

        borrower_ids = []
        for i, name in enumerate(NAMES, 1):
            cur.execute("INSERT INTO borrowers (borrower_name,roll_no) VALUES (%s,%s)", (name, f"24CSE{i:03d}"))
            borrower_ids.append(cur.lastrowid)

        avail = dict(book_ids)
        active = set()
        today = date.today()
        ids = list(book_ids)
        # First generate historical transactions so charts have a useful 12-month trend.
        for _ in range(n_loans):
            issue = today - timedelta(days=random.randint(0, 365))
            book = random.choices(ids, weights=[1 + (i % 5) * 0.7 for i in range(len(ids))])[0]
            borrower = random.choice(borrower_ids)
            if (book, borrower) in active:
                continue
            due = issue + timedelta(days=LOAN_PERIOD_DAYS)
            old_enough = (today - issue).days > 25
            should_return = old_enough and random.random() < 0.88
            if not should_return and avail[book] < 1:
                continue
            if should_return:
                late = random.random() < 0.20
                extra = random.randint(1, 8) if late else -random.randint(0, 5)
                ret = min(max(issue + timedelta(days=max(1, LOAN_PERIOD_DAYS + extra)), issue), today)
                cur.execute(
                    "INSERT INTO loans (book_id,borrower_id,issue_date,due_date,return_date) VALUES (%s,%s,%s,%s,%s)",
                    (book, borrower, issue, due, ret),
                )
            else:
                cur.execute(
                    "INSERT INTO loans (book_id,borrower_id,issue_date,due_date) VALUES (%s,%s,%s,%s)",
                    (book, borrower, issue, due),
                )
                avail[book] -= 1
                active.add((book, borrower))

        for book_id, available in avail.items():
            cur.execute("UPDATE books SET copies_available=%s WHERE book_id=%s", (available, book_id))
        conn.commit()
        print(f"Sample data loaded: {len(BOOKS)} books, {len(NAMES)} borrowers and demo loans.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    seed()
