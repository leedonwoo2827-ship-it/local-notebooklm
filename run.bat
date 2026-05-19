@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" goto :no_venv
if not exist ".venv\Scripts\streamlit.exe" goto :no_streamlit
if not exist ".env" copy .env.example .env >nul

echo Starting Local NotebookLM... your browser will open automatically.
echo To stop: press Ctrl+C in this window.
echo.

call .venv\Scripts\activate.bat
.venv\Scripts\streamlit.exe run app.py

echo.
echo ============================================================
echo  Streamlit has exited. See messages above for any errors.
echo ============================================================
pause
goto :eof

:no_venv
echo [ERROR] Virtual environment folder .venv not found.
echo         Run setup.bat first.
pause
exit /b 1

:no_streamlit
echo [ERROR] Streamlit is not installed in .venv.
echo         Run setup.bat first to install dependencies.
pause
exit /b 1
