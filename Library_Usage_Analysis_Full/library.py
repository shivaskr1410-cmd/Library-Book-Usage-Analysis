"""Core library operations used by both the CLI and Streamlit frontend."""
from datetime import date, timedelta
from db import get_connection
from config import LOAN_PERIOD_DAYS


class LibraryError(Exception):
    pass


def _query(sql, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return cur.fetchall()
    finally:
        conn.close()


def add_book(isbn, title, author, category, copies=1):
    if not all(str(x).strip() for x in (isbn, title, author, category)):
        raise LibraryError("All book fields are required.")
    if copies < 1:
        raise LibraryError("Copies must be at least 1.")
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT book_id FROM books WHERE isbn=%s", (isbn,))
        if cur.fetchone():
            raise LibraryError(f"A book with ISBN {isbn} already exists.")
        cur.execute(
            "INSERT INTO books (isbn,title,author,category,total_copies,copies_available) VALUES (%s,%s,%s,%s,%s,%s)",
            (isbn, title, author, category, copies, copies),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_borrower(name, roll_no):
    if not str(name).strip() or not str(roll_no).strip():
        raise LibraryError("Name and roll number are required.")
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT borrower_id FROM borrowers WHERE roll_no=%s", (roll_no,))
        if cur.fetchone():
            raise LibraryError(f"Roll number {roll_no} is already registered.")
        cur.execute("INSERT INTO borrowers (borrower_name,roll_no) VALUES (%s,%s)", (name, roll_no))
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_books(search=None, category=None):
    sql = "SELECT book_id,isbn,title,author,category,total_copies,copies_available FROM books WHERE 1=1"
    params = []
    if search:
        sql += " AND (title LIKE %s OR author LIKE %s OR isbn LIKE %s)"
        like = f"%{search}%"
        params += [like, like, like]
    if category and category != "All":
        sql += " AND category=%s"
        params.append(category)
    sql += " ORDER BY title"
    return _query(sql, params)


def list_borrowers(search=None):
    sql = "SELECT borrower_id,borrower_name,roll_no FROM borrowers WHERE 1=1"
    params = []
    if search:
        sql += " AND (borrower_name LIKE %s OR roll_no LIKE %s)"
        like = f"%{search}%"
        params += [like, like]
    sql += " ORDER BY borrower_name"
    return _query(sql, params)


def issue_book(book_id, borrower_id, issue_date=None, loan_days=None):
    issue_date = issue_date or date.today()
    loan_days = LOAN_PERIOD_DAYS if loan_days is None else loan_days
    if issue_date > date.today():
        raise LibraryError("Issue date cannot be in the future.")
    if loan_days < 1:
        raise LibraryError("Loan period must be at least 1 day.")
    due_date = issue_date + timedelta(days=loan_days)
    conn = get_connection()
    try:
        conn.start_transaction()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT copies_available FROM books WHERE book_id=%s FOR UPDATE", (book_id,))
        book = cur.fetchone()
        if not book:
            raise LibraryError(f"Book {book_id} does not exist.")
        cur.execute("SELECT borrower_id FROM borrowers WHERE borrower_id=%s", (borrower_id,))
        if not cur.fetchone():
            raise LibraryError(f"Borrower {borrower_id} does not exist.")
        if book["copies_available"] < 1:
            raise LibraryError("No copies available for this book.")
        cur.execute(
            "SELECT loan_id FROM loans WHERE book_id=%s AND borrower_id=%s AND return_date IS NULL",
            (book_id, borrower_id),
        )
        if cur.fetchone():
            raise LibraryError("This borrower already has an active loan for this book.")
        cur.execute(
            "INSERT INTO loans (book_id,borrower_id,issue_date,due_date) VALUES (%s,%s,%s,%s)",
            (book_id, borrower_id, issue_date, due_date),
        )
        loan_id = cur.lastrowid
        cur.execute("UPDATE books SET copies_available=copies_available-1 WHERE book_id=%s", (book_id,))
        conn.commit()
        return loan_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def return_book(loan_id, return_date=None):
    return_date = return_date or date.today()
    conn = get_connection()
    try:
        conn.start_transaction()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM loans WHERE loan_id=%s FOR UPDATE", (loan_id,))
        loan = cur.fetchone()
        if not loan:
            raise LibraryError(f"Loan {loan_id} does not exist.")
        if loan["return_date"] is not None:
            raise LibraryError("This loan has already been returned.")
        if return_date < loan["issue_date"]:
            raise LibraryError("Return date cannot be before the issue date.")
        if return_date > date.today():
            raise LibraryError("Return date cannot be in the future.")
        cur.execute("UPDATE loans SET return_date=%s WHERE loan_id=%s", (return_date, loan_id))
        cur.execute("UPDATE books SET copies_available=copies_available+1 WHERE book_id=%s", (loan["book_id"],))
        conn.commit()
        return {"loan_id": loan_id, "late_days": max((return_date - loan["due_date"]).days, 0)}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def active_loans():
    return _query(
        "SELECT l.loan_id,b.title,br.borrower_name,br.roll_no,l.issue_date,l.due_date "
        "FROM loans l JOIN books b ON b.book_id=l.book_id JOIN borrowers br ON br.borrower_id=l.borrower_id "
        "WHERE l.return_date IS NULL ORDER BY l.due_date"
    )


def overdue_loans(as_of=None):
    as_of = as_of or date.today()
    return _query(
        "SELECT l.loan_id,b.title,br.borrower_name,br.roll_no,l.issue_date,l.due_date,DATEDIFF(%s,l.due_date) AS days_overdue "
        "FROM loans l JOIN books b ON b.book_id=l.book_id JOIN borrowers br ON br.borrower_id=l.borrower_id "
        "WHERE l.return_date IS NULL AND l.due_date < %s ORDER BY days_overdue DESC",
        (as_of, as_of),
    )


def all_loans():
    return _query(
        "SELECT l.loan_id,l.book_id,b.title,b.author,b.category,l.borrower_id,br.borrower_name,br.roll_no,"
        "l.issue_date,l.due_date,l.return_date "
        "FROM loans l JOIN books b ON b.book_id=l.book_id JOIN borrowers br ON br.borrower_id=l.borrower_id "
        "ORDER BY l.issue_date DESC"
    )


def summary(as_of=None):
    as_of = as_of or date.today()
    rows = _query(
        "SELECT (SELECT COUNT(*) FROM books) AS total_books, "
        "(SELECT COALESCE(SUM(total_copies),0) FROM books) AS total_copies, "
        "(SELECT COUNT(*) FROM borrowers) AS total_borrowers, "
        "(SELECT COUNT(*) FROM loans WHERE return_date IS NULL) AS active_loans, "
        "(SELECT COUNT(*) FROM loans WHERE return_date IS NULL AND due_date < %s) AS overdue_loans, "
        "(SELECT COUNT(*) FROM loans) AS total_loans",
        (as_of,),
    )
    return rows[0]


def check_consistency():
    return _query(
        "SELECT b.book_id,b.title,b.total_copies,b.copies_available,COUNT(l.loan_id) AS active_loans "
        "FROM books b LEFT JOIN loans l ON l.book_id=b.book_id AND l.return_date IS NULL "
        "GROUP BY b.book_id,b.title,b.total_copies,b.copies_available "
        "HAVING b.copies_available <> b.total_copies-COUNT(l.loan_id)"
    )
