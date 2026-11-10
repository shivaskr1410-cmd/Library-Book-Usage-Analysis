@echo off
if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Create it with: python -m venv .venv
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m streamlit run app.py
