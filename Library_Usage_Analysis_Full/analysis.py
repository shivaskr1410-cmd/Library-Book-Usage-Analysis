"""Pandas/NumPy analysis and CSV/chart report generation."""
import os
from datetime import date
import numpy as np
import pandas as pd
from config import OUTPUT_DIR


def load_loans_df():
    from db import get_connection
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT l.loan_id,l.book_id,b.title,b.author,b.category,l.borrower_id,br.borrower_name,"
            "l.issue_date,l.due_date,l.return_date FROM loans l "
            "JOIN books b ON b.book_id=l.book_id JOIN borrowers br ON br.borrower_id=l.borrower_id"
        )
        rows = cur.fetchall()
    finally:
        conn.close()
    return prepare_df(pd.DataFrame(rows))


def prepare_df(df):
    df = df.copy()
    if df.empty:
        for c in ("issue_date", "due_date", "return_date"):
            df[c] = pd.Series(dtype="datetime64[ns]")
        df["month"] = pd.Series(dtype="period[M]")
        return df
    for c in ("issue_date", "due_date", "return_date"):
        df[c] = pd.to_datetime(df[c])
    df["month"] = df["issue_date"].dt.to_period("M")
    return df


def most_borrowed(df, top_n=10):
    return (df.groupby(["book_id", "title", "author"]).size().reset_index(name="times_borrowed")
            .sort_values(["times_borrowed", "title"], ascending=[False, True]).head(top_n).reset_index(drop=True))


def monthly_circulation(df):
    s = df.groupby("month").size().rename("loans")
    if s.empty:
        return s.reset_index()
    full = pd.period_range(s.index.min(), s.index.max(), freq="M")
    out = s.reindex(full, fill_value=0).reset_index()
    out.columns = ["month", "loans"]
    return out


def category_summary(df, as_of=None):
    as_of = pd.Timestamp(as_of or date.today())
    d = df.copy()
    d["is_active"] = d["return_date"].isna()
    d["is_overdue"] = d["is_active"] & (d["due_date"] < as_of)
    return (d.groupby("category").agg(total_loans=("loan_id", "count"), unique_books=("book_id", "nunique"),
                                      active_loans=("is_active", "sum"), overdue_loans=("is_overdue", "sum"))
            .reset_index().sort_values("total_loans", ascending=False).reset_index(drop=True))


def overdue_list(df, as_of=None):
    as_of = pd.Timestamp(as_of or date.today())
    d = df[df["return_date"].isna() & (df["due_date"] < as_of)].copy()
    d["days_overdue"] = (as_of - d["due_date"]).dt.days
    cols = ["loan_id", "title", "borrower_name", "issue_date", "due_date", "days_overdue"]
    return d[cols].sort_values("days_overdue", ascending=False).reset_index(drop=True)


def descriptive_stats(df):
    out = {}
    returned = df.dropna(subset=["return_date"])
    if len(returned):
        days = (returned["return_date"] - returned["issue_date"]).dt.days.to_numpy()
        out["loan_duration_days"] = {
            "count": int(days.size), "mean": float(np.mean(days)), "median": float(np.median(days)),
            "std": float(np.std(days)), "min": int(np.min(days)), "max": int(np.max(days)),
            "p90": float(np.percentile(days, 90)),
        }
    monthly = monthly_circulation(df)["loans"].to_numpy()
    if monthly.size:
        out["monthly_loans"] = {
            "months": int(monthly.size), "mean": float(np.mean(monthly)), "median": float(np.median(monthly)),
            "std": float(np.std(monthly)), "min": int(np.min(monthly)), "max": int(np.max(monthly)),
        }
    return out


def generate_reports(df=None, out_dir=OUTPUT_DIR, as_of=None):
    os.makedirs(out_dir, exist_ok=True)
    df = load_loans_df() if df is None else df
    if df.empty:
        raise ValueError("No loan data available to analyse.")
    most_borrowed(df).to_csv(os.path.join(out_dir, "most_borrowed_books.csv"), index=False)
    overdue_list(df, as_of).to_csv(os.path.join(out_dir, "overdue_loans.csv"), index=False)
    category_summary(df, as_of).to_csv(os.path.join(out_dir, "category_summary.csv"), index=False)
    monthly_circulation(df).to_csv(os.path.join(out_dir, "monthly_circulation.csv"), index=False)
    stats = descriptive_stats(df)
    with open(os.path.join(out_dir, "descriptive_stats.txt"), "w", encoding="utf-8") as f:
        for section, vals in stats.items():
            f.write(f"[{section}]\n")
            for k, v in vals.items():
                f.write(f"  {k}: {v:.2f}\n" if isinstance(v, float) else f"  {k}: {v}\n")
    return stats
