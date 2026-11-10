"""Streamlit frontend for the Library Book Usage Analysis System."""
import os
from datetime import date
import pandas as pd
import streamlit as st

import analysis
import db
import library
from config import LOAN_PERIOD_DAYS, OUTPUT_DIR
from library import LibraryError

st.set_page_config(page_title="Library Usage Analysis", page_icon="📚", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.small-note {font-size: 0.9rem; opacity: 0.75;}
</style>
""", unsafe_allow_html=True)


def df(rows):
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def database_ready():
    try:
        library.summary()
        return True
    except Exception:
        return False


def show_table(rows, height=420):
    data = df(rows)
    if data.empty:
        st.info("No records found.")
    else:
        st.dataframe(data, use_container_width=True, height=height, hide_index=True)


def dashboard():
    st.title("📚 Library Book Usage Analysis System")
    st.caption("Manage books, borrowers and circulation while analysing library usage patterns.")
    if not database_ready():
        st.error("Database is not ready. Run `python setup.py` from the project folder first.")
        return
    s = library.summary()
    cols = st.columns(6)
    metrics = [
        ("Total Titles", s["total_books"]), ("Total Copies", s["total_copies"]),
        ("Borrowers", s["total_borrowers"]), ("Total Loans", s["total_loans"]),
        ("Active Loans", s["active_loans"]), ("Overdue", s["overdue_loans"]),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)

    try:
        data = analysis.load_loans_df()
        if data.empty:
            st.info("No loan history yet. Add or seed data to see analytics.")
            return
        st.subheader("Usage overview")
        c1, c2 = st.columns(2)
        monthly = analysis.monthly_circulation(data).copy()
        monthly["month"] = monthly["month"].astype(str)
        c1.line_chart(monthly.set_index("month")["loans"])
        popular = analysis.most_borrowed(data, 8).set_index("title")["times_borrowed"]
        c2.bar_chart(popular)
        c3, c4 = st.columns(2)
        cats = analysis.category_summary(data).set_index("category")["total_loans"]
        c3.bar_chart(cats)
        overdue = analysis.overdue_list(data)
        c4.subheader("Top overdue loans")
        show_table(overdue.head(8).to_dict("records"), height=300)
    except Exception as exc:
        st.warning(f"Analytics could not be loaded: {exc}")


def books_page():
    st.title("📖 Books")
    c1, c2 = st.columns([2, 1])
    search = c1.text_input("Search by title, author or ISBN")
    rows = library.list_books(search=search)
    show_table(rows)
    st.subheader("Add a new book")
    with st.form("add_book"):
        a, b = st.columns(2)
        isbn = a.text_input("ISBN")
        title = b.text_input("Title")
        author = a.text_input("Author")
        category = b.selectbox("Category", ["Programming", "Python", "Java", "Data Science", "Databases", "Computer Science", "AI", "Data Engineering", "Science", "History", "Fiction", "Self-Help", "Other"])
        copies = a.number_input("Number of copies", min_value=1, max_value=100, value=1)
        if st.form_submit_button("Add Book"):
            try:
                book_id = library.add_book(isbn, title, author, category, int(copies))
                st.success(f"Book added successfully. Book ID: {book_id}")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def borrowers_page():
    st.title("👨‍🎓 Borrowers")
    search = st.text_input("Search by name or roll number")
    show_table(library.list_borrowers(search=search))
    st.subheader("Register borrower")
    with st.form("add_borrower"):
        name = st.text_input("Student name")
        roll = st.text_input("Roll number")
        if st.form_submit_button("Register"):
            try:
                borrower_id = library.add_borrower(name, roll)
                st.success(f"Borrower registered. ID: {borrower_id}")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def circulation_page():
    st.title("🔄 Issue / Return")
    books = library.list_books()
    borrowers = library.list_borrowers()
    if not books or not borrowers:
        st.warning("Add books and borrowers first.")
        return
    tab1, tab2 = st.tabs(["Issue Book", "Return Book"])
    with tab1:
        available = [b for b in books if b["copies_available"] > 0]
        if not available:
            st.warning("No copies are currently available.")
        else:
            with st.form("issue_form"):
                book_options = {f"{b['title']} — {b['author']} (available: {b['copies_available']})": b["book_id"] for b in available}
                borrower_options = {f"{b['borrower_name']} — {b['roll_no']}": b["borrower_id"] for b in borrowers}
                book_label = st.selectbox("Book", list(book_options))
                borrower_label = st.selectbox("Borrower", list(borrower_options))
                issue_date = st.date_input("Issue date", value=date.today(), max_value=date.today())
                days = st.number_input("Loan period (days)", min_value=1, max_value=90, value=LOAN_PERIOD_DAYS)
                if st.form_submit_button("Issue Book"):
                    try:
                        loan_id = library.issue_book(book_options[book_label], borrower_options[borrower_label], issue_date, int(days))
                        st.success(f"Book issued successfully. Loan ID: {loan_id}")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
    with tab2:
        active = library.active_loans()
        show_table(active, height=300)
        if active:
            labels = {f"#{r['loan_id']} — {r['title']} — {r['borrower_name']}": r["loan_id"] for r in active}
            with st.form("return_form"):
                label = st.selectbox("Select active loan", list(labels))
                return_date = st.date_input("Return date", value=date.today(), max_value=date.today())
                if st.form_submit_button("Return Book"):
                    try:
                        result = library.return_book(labels[label], return_date)
                        if result["late_days"]:
                            st.warning(f"Returned. Late by {result['late_days']} day(s).")
                        else:
                            st.success("Returned on time.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


def loans_page():
    st.title("📋 Loan Records")
    tab1, tab2, tab3 = st.tabs(["All Loans", "Active", "Overdue"])
    with tab1:
        show_table(library.all_loans())
    with tab2:
        show_table(library.active_loans())
    with tab3:
        overdue = library.overdue_loans()
        show_table(overdue)
        if overdue:
            st.download_button("Download overdue CSV", pd.DataFrame(overdue).to_csv(index=False), "overdue_loans.csv", "text/csv")


def analytics_page():
    st.title("📊 Analytics & Reports")
    try:
        data = analysis.load_loans_df()
        if data.empty:
            st.info("No loan data available.")
            return
        top_n = st.slider("Number of popular books", 5, 15, 10)
        popular = analysis.most_borrowed(data, top_n)
        monthly = analysis.monthly_circulation(data).copy()
        monthly["month"] = monthly["month"].astype(str)
        category = analysis.category_summary(data)
        c1, c2 = st.columns(2)
        c1.subheader("Most borrowed books")
        c1.bar_chart(popular.set_index("title")["times_borrowed"])
        c2.subheader("Monthly circulation")
        c2.line_chart(monthly.set_index("month")["loans"])
        st.subheader("Category analysis")
        st.dataframe(category, use_container_width=True, hide_index=True)
        st.subheader("Descriptive statistics")
        stats = analysis.descriptive_stats(data)
        st.json(stats)
        if st.button("Generate CSV reports"):
            analysis.generate_reports(data)
            st.success(f"Reports generated in `{OUTPUT_DIR}`.")
    except Exception as exc:
        st.error(f"Analysis error: {exc}")


def reports_page():
    st.title("📥 Reports")
    if not os.path.isdir(OUTPUT_DIR):
        st.info("No reports generated yet. Open Analytics and click Generate CSV reports.")
        return
    files = sorted(x for x in os.listdir(OUTPUT_DIR) if x != ".gitkeep")
    if not files:
        st.info("No reports available yet.")
        return
    for name in files:
        path = os.path.join(OUTPUT_DIR, name)
        with open(path, "rb") as f:
            st.download_button(f"Download {name}", f.read(), name, key=name)


def help_page():
    st.title("⚙️ Setup & Project Information")
    st.markdown("""
### Project stack
- **Frontend:** Streamlit
- **Backend:** Python
- **Database:** MySQL 8+
- **Database tool:** SQLyog (optional)
- **Analysis:** Pandas + NumPy
- **Charts:** Streamlit charts / Plotly-ready data workflow

### First-time setup
1. Install MySQL Server and make sure it is running.
2. Open `config.py` and enter your MySQL password, or set `LIB_DB_PASSWORD`.
3. In the project terminal run `python setup.py`.
4. Start the website with `streamlit run app.py`.

### Important
`python setup.py` resets the project tables because the demo schema intentionally recreates them. Do not run it after entering data you want to keep.
""")


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "home"

if not st.session_state.logged_in:

    
    st.markdown("""
    <style>
    .hero {
        background: linear-gradient(120deg, #10243e, #24527a);
        padding: 65px 30px;
        border-radius: 18px;
        text-align: center;
        color: white;
    }
    .hero h1 {
        color: white;
        font-size: 42px;
    }
    .hero p {
        color: #e0eaf5;
        font-size: 18px;
    }
    .section-title {
        text-align: center;
        font-size: 30px;
        font-weight: bold;
        margin-top: 35px;
    }
    </style>
    """, unsafe_allow_html=True)

    nav1, nav2 = st.columns([5, 1])

    with nav1:
        st.title("📚 Library Usage")

    with nav2:
        if st.button("Admin Login"):
            st.session_state.page = "login"
            st.rerun()

    st.markdown("""
    <div class="hero">
        <h1>Library Book Usage Analysis</h1>
        <p>Smart Library Management and Analytics System</p>
        <p>Manage Books • Track Borrowers • Analyze Usage</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    if st.button("Get Started →", type="primary"):
        st.session_state.page = "login"
        st.rerun()

    st.markdown('<div class="section-title">About Our Project</div>',
                unsafe_allow_html=True)

    st.write("""
    The Library Book Usage Analysis System simplifies library
    management. It helps administrators manage books, borrowers,
    book circulation and overdue records while analyzing
    borrowing patterns and generating useful reports.
    """)

    st.divider()

    st.markdown('<div class="section-title">Our Key Features</div>',
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    c1.info("📖 **Book Management**\n\nAdd, view and search books.")
    c2.info("👨‍🎓 **Borrower Management**\n\nRegister and manage borrowers.")
    c3.info("🔄 **Issue & Return**\n\nTrack book circulation.")

    c4, c5, c6 = st.columns(3)

    c4.info("⏰ **Overdue Tracking**\n\nIdentify overdue books.")
    c5.info("📊 **Usage Analytics**\n\nAnalyze popular books and trends.")
    c6.info("📥 **Reports**\n\nGenerate downloadable reports.")

    st.divider()

    st.markdown('<div class="section-title">How It Works</div>',
                unsafe_allow_html=True)

    a, b, c, d = st.columns(4)

    a.metric("01", "Add Books")
    b.metric("02", "Register Users")
    c.metric("03", "Issue Books")
    d.metric("04", "Analyze Data")

    st.divider()

    st.markdown('<div class="section-title">Technologies Used</div>',
                unsafe_allow_html=True)

    t1, t2, t3 = st.columns(3)

    t1.success("🐍 Python\n\nApplication logic")
    t2.success("🌐 Streamlit\n\nUser interface")
    t3.success("🗄️ MySQL\n\nDatabase")

    t4, t5, t6 = st.columns(3)

    t4.success("🐼 Pandas\n\nData analysis")
    t5.success("🔢 NumPy\n\nNumerical operations")
    t6.success("📈 Plotly\n\nInteractive visualization")

    st.divider()

    st.markdown('<div class="section-title">Why Choose Our System?</div>',
                unsafe_allow_html=True)

    st.write("""
    - Easy management of library books and borrowers.
    - Faster book issuing and returning.
    - Better tracking of available and overdue books.
    - Identification of popular books.
    - Monthly and category-wise analysis.
    - Downloadable reports.
    """)

    st.divider()

    st.markdown("""
    <div style="text-align:center; padding:25px;">
        <h3>📚 Library Book Usage Analysis System</h3>
        <p>Making Library Management Smarter and Simpler</p>
        <p>Academic Project | B.Tech Computer Science</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.page == "login":

        st.divider()
        st.subheader("🔐 Admin Login")

        with st.form("admin_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            submit = st.form_submit_button("Login")

            if submit:
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid username or password")

else:

    st.sidebar.title("📚 Library System")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "home"
        st.rerun()

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Books", "Borrowers", "Issue / Return",
         "Loan Records", "Analytics", "Reports", "Setup Help"]
    )

    st.sidebar.markdown(
        f"Default loan period: {LOAN_PERIOD_DAYS} days"
    )

    try:
        if page == "Dashboard":
            dashboard()
        elif page == "Books":
            books_page()
        elif page == "Borrowers":
            borrowers_page()
        elif page == "Issue / Return":
            circulation_page()
        elif page == "Loan Records":
            loans_page()
        elif page == "Analytics":
            analytics_page()
        elif page == "Reports":
            reports_page()
        else:
            help_page()

    except Exception as exc:
        st.error("The application could not complete this operation.")
        st.exception(exc)

