@echo off
setlocal EnableDelayedExpansion
title AI Formater
color 0A

echo.
echo  ============================================
echo         AI Formater — Launching...
echo  ============================================
echo.

:: ─────────────────────────────────────────────
::  Check if setup has been run
:: ─────────────────────────────────────────────
if not exist "%~dp0.setup_done" (
    echo  [!] Setup has not been run yet.
    echo.
    echo  Please run setup.bat first to install dependencies.
    echo.
    choice /C YN /M "Run setup now?"
    if !errorlevel! EQU 1 (
        call "%~dp0setup.bat"
        if !errorlevel! neq 0 exit /b 1
    ) else (
        echo Exiting.
        pause
        exit /b 1
    )
)

:: ─────────────────────────────────────────────
::  Quick sanity checks
:: ─────────────────────────────────────────────
py -3.12 --version >nul 2>&1
if %errorlevel% EQU 0 (
    set PYTHON_CMD=py -3.12
) else (
    python --version 2>nul | findstr "3.12" >nul
    if %errorlevel% EQU 0 (
        set PYTHON_CMD=python
    ) else (
        echo  [ERROR] Python 3.12 not found. Please run setup.bat again.
        pause
        exit /b 1
    )
)

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Node.js not found. Please run setup.bat again.
    pause
    exit /b 1
)

:: ─────────────────────────────────────────────
::  Kill any leftover servers on port 8000 / 5173
:: ─────────────────────────────────────────────
echo  Cleaning up any old server instances...
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":8000 "') do (
    taskkill /PID %%p /F >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":5173 "') do (
    taskkill /PID %%p /F >nul 2>&1
)

:: ─────────────────────────────────────────────
::  Start Backend
:: ─────────────────────────────────────────────
echo.
echo  [1/2] Starting Backend (port 8000)...
start "AI Formater — Backend" cmd /k "cd /d ""%~dp0backend"" && echo Backend starting... && !PYTHON_CMD! -m uvicorn main:app --reload --port 8000"

:: ─────────────────────────────────────────────
::  Start Frontend
:: ─────────────────────────────────────────────
echo  [2/2] Starting Frontend (port 5173)...
start "AI Formater — Frontend" cmd /k "cd /d ""%~dp0frontend"" && echo Frontend starting... && npm run dev"

:: ─────────────────────────────────────────────
::  Wait then open browser
:: ─────────────────────────────────────────────
echo.
echo  Waiting for servers to start...
timeout /t 5 /nobreak >nul

echo  Opening browser at http://localhost:5173 ...
start http://localhost:5173

echo.
echo  ============================================
echo    AI Formater is running!
echo.
echo    Frontend:  http://localhost:5173
echo    Backend:   http://localhost:8000
echo.
echo    Close the "Backend" and "Frontend" windows
echo    to stop the app.
echo  ============================================
echo.
pause
