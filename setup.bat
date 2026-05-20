@echo off
setlocal

cd /d "%~dp0"

echo ============================================================
echo  Local NotebookLM - Setup (Windows)
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 goto :no_python

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [1/4] Python %PYVER% detected.

if exist ".venv\Scripts\python.exe" goto :venv_ok
echo [2/4] Creating virtual environment in folder .venv ...
python -m venv .venv
if errorlevel 1 goto :venv_fail
goto :install_deps

:venv_ok
echo [2/4] Virtual environment already exists. Skipping.

:install_deps
echo [3/5] Installing dependencies. This may take 10-15 minutes ...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -e .
if errorlevel 1 goto :install_fail

echo [4/5] Installing Playwright Chromium (for cardnews PNG capture) ...
python -m playwright install chromium
if errorlevel 1 (
    echo [WARN] Playwright Chromium install failed. Cardnews PNG capture will be disabled.
    echo        You can retry later:  .venv\Scripts\python.exe -m playwright install chromium
)

if exist ".env" (
    echo [5/5] .env already exists.
) else (
    copy .env.example .env >nul
    echo [5/5] Created .env from .env.example.
)

echo.
echo ============================================================
echo  Setup complete. Now double-click run.bat
echo ============================================================
echo.
pause
goto :eof

:no_python
echo [ERROR] Python is not installed.
echo         Install Python 3.10+ from https://www.python.org/downloads/
echo         and check "Add Python to PATH" during installation.
pause
exit /b 1

:venv_fail
echo [ERROR] Failed to create virtual environment.
pause
exit /b 1

:install_fail
echo [ERROR] Dependency install failed. Check the log above.
pause
exit /b 1
