@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment (.venv) not found.
    echo         Run setup.bat first.
    pause
    exit /b 1
)

if not exist ".env" (
    copy .env.example .env >nul
)

echo Starting Local NotebookLM... your browser will open automatically.
echo To stop: press Ctrl+C in this window.
echo.

call .venv\Scripts\activate.bat
streamlit run app.py

endlocal
