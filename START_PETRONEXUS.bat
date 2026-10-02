@echo off
setlocal EnableExtensions
title PetroNexus - SIH 26121

cd /d "%~dp0"

echo.
echo ============================================================
echo                    PETRONEXUS
echo              SIH 26121 - NWIS Platform
echo ============================================================
echo.

REM ------------------------------------------------------------
REM 1. Check Python
REM ------------------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH.
    echo Install Python 3.11+ and enable "Add Python to PATH".
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM 2. Use existing virtual environment if available
REM ------------------------------------------------------------
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    echo [OK] Using .venv Python environment.
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON=venv\Scripts\python.exe"
    echo [OK] Using venv Python environment.
) else (
    set "PYTHON=python"
    echo [INFO] No virtual environment detected.
    echo [INFO] Using system Python.
)

REM ------------------------------------------------------------
REM 3. Check required dependencies
REM ------------------------------------------------------------
echo.
echo [INFO] Checking FastAPI/Uvicorn...

%PYTHON% -c "import fastapi,uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Required Python packages are missing.
    echo [INFO] Installing backend requirements...

    if exist "backend\requirements.txt" (
        %PYTHON% -m pip install -r backend\requirements.txt
        if errorlevel 1 (
            echo.
            echo [ERROR] Dependency installation failed.
            pause
            exit /b 1
        )
    ) else (
        echo [ERROR] backend\requirements.txt was not found.
        pause
        exit /b 1
    )
)

REM ------------------------------------------------------------
REM 4. Start PetroNexus
REM ------------------------------------------------------------
echo.
echo ============================================================
echo Starting PetroNexus...
echo ============================================================
echo.
echo Dashboard:
echo   http://127.0.0.1:8000/
echo.
echo AI Assistant:
echo   http://127.0.0.1:8000/assistant.html
echo.
echo API Docs:
echo   http://127.0.0.1:8000/docs
echo.
echo Press CTRL+C in this window to stop PetroNexus.
echo.

REM Open browser after a short delay while the server starts.
start "" /b cmd /c "timeout /t 3 /nobreak >nul & start "" http://127.0.0.1:8000/"

%PYTHON% main.py

echo.
echo ============================================================
echo PetroNexus has stopped.
echo ============================================================
pause
