@echo off
echo Starting EDA Agent Backend...
echo.
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
