@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0\.."

echo ============================================================
echo  Local NotebookLM - 설치 스크립트 (Windows)
echo ============================================================
echo.

REM 1) Python 확인
where python >nul 2>nul
if errorlevel 1 (
    echo [에러] Python이 설치되어 있지 않습니다.
    echo        https://www.python.org/downloads/ 에서 3.10 이상 설치 후 다시 실행하세요.
    echo        설치 시 "Add Python to PATH" 체크 필수.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [1/4] Python %PYVER% 확인 완료

REM 2) 가상환경
if exist ".venv\Scripts\python.exe" (
    echo [2/4] 가상환경(.venv)이 이미 존재합니다. 건너뜀.
) else (
    echo [2/4] 가상환경 생성 중...
    python -m venv .venv
    if errorlevel 1 (
        echo [에러] 가상환경 생성 실패.
        pause
        exit /b 1
    )
)

REM 3) pip 업그레이드 + 의존성 설치
echo [3/4] 의존성 설치 중 (10~15분 소요됩니다, 인터넷 속도에 따라 다름)...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -e .
if errorlevel 1 (
    echo [에러] 의존성 설치 실패. 로그를 확인하세요.
    pause
    exit /b 1
)

REM 4) .env 준비
if exist ".env" (
    echo [4/4] .env 파일이 이미 존재합니다.
) else (
    copy .env.example .env >nul
    echo [4/4] .env 파일 생성 완료. (앱 첫 실행 시 화면에서 URL/키 입력)
)

echo.
echo ============================================================
echo  설치 완료. 이제 "실행.bat" 또는 "scripts\run.bat" 을 실행하세요.
echo ============================================================
echo.
pause
endlocal
