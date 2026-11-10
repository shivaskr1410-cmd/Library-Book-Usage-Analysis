# Library Book Usage Analysis System — Full Stack College Project

A beginner-friendly library management and usage-analysis project with a **Streamlit frontend**, **Python backend**, **MySQL database**, sample data, reports and analytics.

## Features

- Dashboard with total titles, copies, borrowers, loans, active loans and overdue loans
- Book management: add/search books and track available copies
- Borrower registration and search
- Issue and return books with validation
- Automatic due dates and overdue detection
- Active/all/overdue loan records
- Most-borrowed books analysis
- Monthly circulation trend
- Category-wise analysis
- NumPy descriptive statistics
- CSV report generation
- Sample database data: 20 books, 24 borrowers and hundreds of demo loans
- Command-line interface retained for testing/admin use
- Automated tests

## Technology

- Frontend: Streamlit
- Backend: Python 3.10+
- Database: MySQL 8+
- Database GUI: SQLyog (optional)
- Analysis: Pandas + NumPy
- Charts: Streamlit charts; Plotly is included for future custom charts

## Project structure

```text
Library_Usage_Analysis_Full/
├── app.py                 # Streamlit frontend
├── setup.py               # one-command database initialization + demo data
├── main.py                # command-line interface
├── config.py              # MySQL settings
├── db.py                  # database connection/setup
├── library.py             # book/borrower/issue/return business logic
├── analysis.py            # Pandas/NumPy analysis and CSV reports
├── seed_data.py           # sample books, students and loans
├── requirements.txt
├── .env.example
├── run_app.bat
├── sql/schema.sql
├── tests/test_logic.py
└── output/
```

## Windows setup — easiest method

### 1. Open the project in VS Code

Open this folder in VS Code and open **Terminal → New Terminal**.

### 2. Create the virtual environment

```powershell
python -m venv .venv
```

### 3. Activate it

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can skip activation and use `.venv\Scripts\python.exe` directly for every command.

### 4. Install packages

```powershell
python -m pip install -r requirements.txt
```

### 5. Configure MySQL

Make sure **MySQL Server is running**. SQLyog can be used to view/manage the database, but SQLyog itself is not the database server.

Open `config.py` and enter your MySQL password:

```python
"password": "YOUR_MYSQL_PASSWORD",
```

Or use environment variables from `.env.example`.

### 6. Create database and load sample data

```powershell
python setup.py
```

This creates/resets `library_db`, creates the tables and loads demo books, borrowers and loans.

**Important:** `setup.py` resets the tables. Do not run it again after entering data you want to keep.

### 7. Start the frontend

```powershell
python -m streamlit run app.py
```

If you skipped activation:

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

Or double-click `run_app.bat` after creating the virtual environment.

Streamlit will show a local address such as:

```text
http://localhost:8501
```

Open it in Chrome.

## If Pandas gives the Windows error

If you see:

```text
DLL load failed while importing _cyutility
An Application Control policy has blocked this file
```

this is a Windows application-control policy issue, not a library-project database error. First try:

```powershell
python -m pip uninstall pandas -y
python -m pip install --no-cache-dir pandas
python -c "import pandas; print(pandas.__version__)"
```

If Windows still reports that a `.pyd` file is blocked, the machine's security policy must be checked by the device administrator/IT support. Reinstalling repeatedly will not bypass a policy block.

## CLI commands

```powershell
python main.py books
python main.py borrowers
python main.py active
python main.py overdue
python main.py summary
python main.py check
python main.py report
```

Examples:

```powershell
python main.py add-book 9781234567890 "My Book" "Some Author" Programming --copies 2
python main.py add-borrower "Ram" 24CSE099
python main.py issue 1 3
python main.py return 1
```

## Tests

```powershell
python -m pytest
```

## Main database tables

- `books` — book details and copy counts
- `borrowers` — student/borrower details
- `loans` — issue, due and return history
- `v_active_loans` — convenient view of currently borrowed books

## Suggested presentation explanation

**Frontend:** Streamlit provides the web interface.

**Backend:** Python modules validate operations and communicate with MySQL.

**Database:** MySQL stores books, borrowers and loan transactions.

**Analysis:** Pandas groups and filters the loan history; NumPy calculates descriptive statistics.

**Reports:** The system generates CSV reports and usage insights.

This is a college/educational system, not production banking/library infrastructure.
