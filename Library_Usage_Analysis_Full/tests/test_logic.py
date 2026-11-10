from datetime import date, timedelta
import pandas as pd
from analysis import most_borrowed, monthly_circulation, category_summary, overdue_list
from library import loan_status


def sample_df():
    return pd.DataFrame([
        {"loan_id":1,"book_id":1,"title":"Clean Code","author":"Martin","category":"Programming","borrower_name":"A","issue_date":pd.Timestamp("2026-01-05"),"due_date":pd.Timestamp("2026-01-19"),"return_date":pd.Timestamp("2026-01-15")},
        {"loan_id":2,"book_id":1,"title":"Clean Code","author":"Martin","category":"Programming","borrower_name":"B","issue_date":pd.Timestamp("2026-02-05"),"due_date":pd.Timestamp("2026-02-19"),"return_date":pd.Timestamp("2026-02-22")},
        {"loan_id":3,"book_id":2,"title":"Sapiens","author":"Harari","category":"History","borrower_name":"C","issue_date":pd.Timestamp("2026-03-05"),"due_date":pd.Timestamp("2026-03-19"),"return_date":pd.NaT},
    ])


def test_status():
    assert loan_status(date(2026,1,1), date(2026,1,10), date(2026,1,9), date(2026,1,20)) == "Returned"
    assert loan_status(date(2026,1,1), date(2026,1,10), date(2026,1,12), date(2026,1,20)) == "Returned Late"
    assert loan_status(date(2026,1,1), date(2026,1,10), None, date(2026,1,5)) == "Active"
    assert loan_status(date(2026,1,1), date(2026,1,10), None, date(2026,1,20)) == "Overdue"


def test_analysis():
    d = sample_df()
    assert most_borrowed(d).iloc[0]["title"] == "Clean Code"
    assert monthly_circulation(d)["loans"].sum() == 3
    assert category_summary(d).iloc[0]["category"] == "Programming"
    assert len(overdue_list(d, date(2026,3,25))) == 1
