@echo off
chcp 65001 >nul
title NexusRAG Backend

REM Lay thu muc chua script nay
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM Kiem tra venv tai backend\.venv
set VENV_PYTHON=%SCRIPT_DIR%\backend\.venv\Scripts\python.exe
if not exist "%VENV_PYTHON%" (
    echo [LOI] Khong tim thay venv tai: %VENV_PYTHON%
    echo Vui long tao venv truoc:
    echo   cd %SCRIPT_DIR%\backend
    echo   python -m venv .venv
    echo   uv pip install -r requirements.txt
    pause
    exit /b 1
)

REM Chay tu thu muc backend
cd /d "%SCRIPT_DIR%\backend"
echo Dang khoi dong NexusRAG Backend tren port 8082...
"%VENV_PYTHON%" -m uvicorn app.main:app --reload --port 8082
