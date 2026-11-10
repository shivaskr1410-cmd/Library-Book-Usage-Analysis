CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

DROP VIEW IF EXISTS v_active_loans;
DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS borrowers;
DROP TABLE IF EXISTS books;

CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    isbn VARCHAR(20) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(120) NOT NULL,
    category VARCHAR(60) NOT NULL,
    total_copies INT NOT NULL DEFAULT 1,
    copies_available INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_total CHECK (total_copies >= 1),
    CONSTRAINT chk_avail CHECK (copies_available >= 0 AND copies_available <= total_copies)
) ENGINE=InnoDB;

CREATE TABLE borrowers (
    borrower_id INT AUTO_INCREMENT PRIMARY KEY,
    borrower_name VARCHAR(100) NOT NULL,
    roll_no VARCHAR(30) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    borrower_id INT NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_loan_book FOREIGN KEY (book_id) REFERENCES books(book_id),
    CONSTRAINT fk_loan_borrower FOREIGN KEY (borrower_id) REFERENCES borrowers(borrower_id),
    CONSTRAINT chk_due CHECK (due_date >= issue_date),
    CONSTRAINT chk_return CHECK (return_date IS NULL OR return_date >= issue_date),
    INDEX idx_loans_book (book_id),
    INDEX idx_loans_borrower (borrower_id),
    INDEX idx_loans_issue (issue_date)
) ENGINE=InnoDB;

CREATE VIEW v_active_loans AS
SELECT l.loan_id, l.book_id, l.borrower_id, b.title, br.borrower_name, br.roll_no,
       l.issue_date, l.due_date,
       GREATEST(DATEDIFF(CURDATE(), l.due_date), 0) AS days_overdue
FROM loans l
JOIN books b ON b.book_id = l.book_id
JOIN borrowers br ON br.borrower_id = l.borrower_id
WHERE l.return_date IS NULL;
