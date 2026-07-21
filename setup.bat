@echo off
setlocal EnableDelayedExpansion
title AI Formater — Full Auto Setup
color 0A

:: ─────────────────────────────────────────────────────────────────────────────
::  AI Formater — Full Automatic Installer
::  Downloads and installs Python + Node.js silently, then installs all packages.
::  No manual steps needed. Just run this once.
:: ─────────────────────────────────────────────────────────────────────────────

:: Versions to install if not found
set PYTHON_VERSION=3.12.10
set PYTHON_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
set PYTHON_INSTALLER=%TEMP%\python_installer.exe

set NODE_VERSION=22.17.1
set NODE_URL=https://nodejs.org/dist/v22.17.1/node-v22.17.1-x64.msi
set NODE_INSTALLER=%TEMP%\node_installer.msi

:: Working directory = folder where this bat lives
set ROOT=%~dp0
set ROOT=%ROOT:~0,-1%

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║       AI Formater — Automatic Setup Installer            ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo  This will automatically:
echo    - Install Python %PYTHON_VERSION% (if needed)
echo    - Install Node.js %NODE_VERSION% LTS  (if needed)
echo    - Install all backend Python packages
echo    - Install all frontend Node packages
echo.
echo  Internet connection required.
echo  This may take 5-10 minutes on first run.
echo.
pause

:: ─────────────────────────────────────────────
::  Admin check deferred until needed
:: ─────────────────────────────────────────────

:: ─────────────────────────────────────────────
::  STEP 1 — Install Python (if missing)
:: ─────────────────────────────────────────────
echo.
echo  ══════════════════════════════════════════
echo  [STEP 1/4] Checking Python 3.12...
echo  ══════════════════════════════════════════

py -3.12 --version >nul 2>&1
if %errorlevel% EQU 0 (
    echo  [OK] Already installed: Python 3.12
    set PYTHON_CMD=py -3.12
    goto :python_done
)

python --version 2>nul | findstr "3.12" >nul
if %errorlevel% EQU 0 (
    echo  [OK] Already installed: Python 3.12
    set PYTHON_CMD=python
    goto :python_done
)

echo  Python not found. Downloading Python %PYTHON_VERSION%...
echo  Source: %PYTHON_URL%
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [!] Administrator privileges required to install Python.
    echo      Right-click setup.bat and select "Run as administrator".
    echo.
    pause
    exit /b 1
)


powershell -NoProfile -Command "Write-Host '  Downloading Python installer...' -ForegroundColor Cyan; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing; Write-Host '  Download complete.' -ForegroundColor Green"

if not exist "%PYTHON_INSTALLER%" (
    echo  [ERROR] Failed to download Python installer.
    echo  Check your internet connection and try again.
    pause
    exit /b 1
)

echo  Installing Python silently...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_launcher=1

if %errorlevel% neq 0 (
    echo  [ERROR] Python installation failed.
    pause
    exit /b 1
)

del /f /q "%PYTHON_INSTALLER%" >nul 2>&1

:: Refresh PATH so python is found in this session
call :refresh_path

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python installed but still not detected. Please restart and re-run setup.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [OK] Installed: %%v

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [OK] Installed: %%v
set PYTHON_CMD=python

:python_done

:: ─────────────────────────────────────────────
::  STEP 2 — Install Node.js (if missing)
:: ─────────────────────────────────────────────
echo.
echo  ══════════════════════════════════════════
echo  [STEP 2/4] Checking Node.js...
echo  ══════════════════════════════════════════

node --version >nul 2>&1
if %errorlevel% EQU 0 (
    for /f "tokens=*" %%v in ('node --version 2^>^&1') do set NODE_FOUND=%%v
    echo  [OK] Already installed: Node.js !NODE_FOUND!
    goto :node_done
)

echo  Node.js not found. Downloading Node.js %NODE_VERSION% LTS...
echo  Source: %NODE_URL%
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [!] Administrator privileges required to install Node.js.
    echo      Right-click setup.bat and select "Run as administrator".
    echo.
    pause
    exit /b 1
)


powershell -NoProfile -Command "Write-Host '  Downloading Node.js installer...' -ForegroundColor Cyan; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%NODE_URL%' -OutFile '%NODE_INSTALLER%' -UseBasicParsing; Write-Host '  Download complete.' -ForegroundColor Green"

if not exist "%NODE_INSTALLER%" (
    echo  [ERROR] Failed to download Node.js installer.
    echo  Check your internet connection and try again.
    pause
    exit /b 1
)

echo  Installing Node.js silently...
msiexec /i "%NODE_INSTALLER%" /quiet /norestart ADDLOCAL=ALL

if %errorlevel% neq 0 (
    echo  [ERROR] Node.js installation failed (code %errorlevel%).
    pause
    exit /b 1
)

del /f /q "%NODE_INSTALLER%" >nul 2>&1

:: Refresh PATH
call :refresh_path

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] Node.js installed but needs a restart to be detected.
    echo      Please restart your computer, then run this setup again.
    pause
    exit /b 0
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo  [OK] Installed: Node.js %%v

:node_done

:: ─────────────────────────────────────────────
::  STEP 3 — Install Python backend packages
:: ─────────────────────────────────────────────
echo.
echo  ══════════════════════════════════════════
echo  [STEP 3/4] Installing Python packages...
echo  ══════════════════════════════════════════

cd /d "%ROOT%\backend"

echo  Upgrading pip...
!PYTHON_CMD! -m pip install --upgrade pip --quiet

echo  Installing backend requirements...
!PYTHON_CMD! -m pip install -r requirements.txt --quiet

if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install Python packages.
    pause
    exit /b 1
)
echo  [OK] All Python packages installed.

:: ─────────────────────────────────────────────
::  STEP 4 — Install Node frontend packages
:: ─────────────────────────────────────────────
echo.
echo  ══════════════════════════════════════════
echo  [STEP 4/4] Installing frontend packages...
echo  ══════════════════════════════════════════

cd /d "%ROOT%\frontend"

echo  Running npm install...
call npm install --silent

if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install npm packages.
    pause
    exit /b 1
)
echo  [OK] All frontend packages installed.

:: ─────────────────────────────────────────────
::  Write setup marker
:: ─────────────────────────────────────────────
echo setup_complete > "%ROOT%\.setup_done"

:: ─────────────────────────────────────────────
::  DONE
:: ─────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║                  Setup Complete!                         ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║                                                          ║
echo  ║  Everything is installed and ready.                      ║
echo  ║                                                          ║
echo  ║  To launch the app, run:  run_app.bat                    ║
echo  ║                                                          ║
echo  ║  You will NOT need to run setup again.                   ║
echo  ║                                                          ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
pause
exit /b 0

:: ─────────────────────────────────────────────
::  Helper: Refresh PATH from registry
:: ─────────────────────────────────────────────
:refresh_path
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set SYS_PATH=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set USR_PATH=%%b
if defined USR_PATH (
    set PATH=%SYS_PATH%;%USR_PATH%
) else (
    set PATH=%SYS_PATH%
)
exit /b 0
