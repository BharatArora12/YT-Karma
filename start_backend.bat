@echo off
echo Starting YT Shorts Management System Backend...
cd backend
if not exist .venv (
    echo Virtual environment not found. Creating .venv...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

if not exist .env (
    echo Copying .env.example to .env...
    copy .env.example .env
)

echo Running FastAPI on http://localhost:8000...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
