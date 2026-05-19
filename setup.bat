@echo off
setlocal

cd /d "%~dp0"

echo ============================================================
echo  Local NotebookLM - Setup (Windows)
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo         Install Python 3.10+ from https://www.python.org/downloads/
    echo         and check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [1/4] Python %PYVER% detected.

if exist ".venv\Scripts\python.exe" (
    echo [2/4] Virtual environment already exists. Skipping.
) else (
    echo [2/4] Creating virtual environment (.venv) ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [3/4] Installing dependencies (may take 10-15 minutes) ...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -e .
if errorlevel 1 (
    echo [ERROR] Dependency install failed. Check the log above.
    pause
    exit /b 1
)

if exist ".env" (
    echo [4/4] .env already exists.
) else (
    copy .env.example .env >nul
    echo [4/4] Created .env from .env.example.
)

echo.
echo ============================================================
echo  Setup complete. Now double-click  run.bat
echo ============================================================
echo.
pause
endlocal
