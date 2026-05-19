@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
    echo [에러] 가상환경(.venv)이 없습니다. 먼저 "설치.bat" 을 실행하세요.
    pause
    exit /b 1
)

if not exist ".env" (
    copy .env.example .env >nul
)

echo Local NotebookLM 실행 중... (브라우저가 자동으로 열립니다)
echo 종료: 이 창에서 Ctrl+C
echo.

call .venv\Scripts\activate.bat
streamlit run app.py

endlocal
