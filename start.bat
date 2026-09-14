@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Gujarat Police Sentinel - Starting...

:: ============================================================================
::  Setup ANSI escape character
:: ============================================================================
for /f %%A in ('echo prompt $E ^| cmd') do set "E=%%A"

cls
echo.
echo   %E%[94m=======================================================================%E%[0m
echo   %E%[94m||%E%[0m                                                               %E%[94m||%E%[0m
echo   %E%[94m||%E%[0m   %E%[1;97m  GUJARAT POLICE SENTINEL  %E%[0m                                %E%[94m||%E%[0m
echo   %E%[94m||%E%[0m   %E%[96m  Surveillance ^& AI Intelligence Platform%E%[0m                   %E%[94m||%E%[0m
echo   %E%[94m||%E%[0m                                                               %E%[94m||%E%[0m
echo   %E%[94m||%E%[0m   %E%[2mOfficer CIPHER Command Center ^& Citizen Safety Portal%E%[0m      %E%[94m||%E%[0m
echo   %E%[94m||%E%[0m                                                               %E%[94m||%E%[0m
echo   %E%[94m=======================================================================%E%[0m
echo.

:: ============================================================================
::  STEP 1 : CHECK PYTHON
:: ============================================================================
echo   %E%[93m[STEP 1/4]%E%[0m  %E%[97mChecking Python Installation...%E%[0m
echo   %E%[2m----------------------------------------------------------------------%E%[0m

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :no_python

for /f "tokens=*" %%V in ('python --version 2^>^&1') do set "PY_VER=%%V"
echo   %E%[92m  OK%E%[0m  %E%[97mFound: %E%[96m%PY_VER%%E%[0m
echo.
goto :step2

:no_python
echo.
echo   %E%[41;97m ERROR %E%[0m  %E%[91mPython is not installed or not in PATH!%E%[0m
echo.
echo   %E%[97mTo fix this:%E%[0m
echo     %E%[96m1.%E%[0m Download Python from %E%[94mhttps://www.python.org/downloads/%E%[0m
echo     %E%[96m2.%E%[0m During installation, check %E%[93m"Add Python to PATH"%E%[0m
echo     %E%[96m3.%E%[0m Restart your computer and run this file again
echo.
pause
exit /b 1

:: ============================================================================
::  STEP 2 : SETUP VIRTUAL ENVIRONMENT
:: ============================================================================
:step2
echo   %E%[93m[STEP 2/4]%E%[0m  %E%[97mSetting Up Virtual Environment...%E%[0m
echo   %E%[2m----------------------------------------------------------------------%E%[0m

if exist ".venv\Scripts\python.exe" goto :venv_exists

echo   %E%[93m  ..%E%[0m  %E%[97mCreating virtual environment %E%[2m(first-time setup)%E%[0m
python -m venv .venv
if %ERRORLEVEL% NEQ 0 goto :venv_fail
set "PYTHON_EXE=.venv\Scripts\python.exe"
echo   %E%[92m  OK%E%[0m  %E%[97mVirtual environment created successfully%E%[0m
echo.
goto :step3

:venv_exists
set "PYTHON_EXE=.venv\Scripts\python.exe"
echo   %E%[92m  OK%E%[0m  %E%[97mVirtual environment found at %E%[96m.venv\%E%[0m
echo.
goto :step3

:venv_fail
echo   %E%[41;97m ERROR %E%[0m  %E%[91mFailed to create virtual environment!%E%[0m
pause
exit /b 1

:: ============================================================================
::  STEP 3 : INSTALL DEPENDENCIES
:: ============================================================================
:step3
echo   %E%[93m[STEP 3/4]%E%[0m  %E%[97mChecking Dependencies...%E%[0m
echo   %E%[2m----------------------------------------------------------------------%E%[0m

"%PYTHON_EXE%" -c "import fastapi; import uvicorn" >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :install_deps

echo   %E%[92m  OK%E%[0m  %E%[97mAll dependencies are already installed%E%[0m
echo.
goto :step4

:install_deps
echo   %E%[93m  ..%E%[0m  %E%[97mInstalling required packages from %E%[96mrequirements.txt%E%[0m
echo   %E%[2m      This may take a minute on first run...%E%[0m
echo.
"%PYTHON_EXE%" -m pip install --upgrade pip --quiet >nul 2>&1
"%PYTHON_EXE%" -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 goto :deps_fail

echo   %E%[92m  OK%E%[0m  %E%[97mAll packages installed successfully%E%[0m
echo.
goto :step4

:deps_fail
echo.
echo   %E%[41;97m ERROR %E%[0m  %E%[91mFailed to install dependencies!%E%[0m
echo   %E%[97mTry running manually: %E%[96m.venv\Scripts\pip install -r requirements.txt%E%[0m
pause
exit /b 1

:: ============================================================================
::  STEP 4 : LAUNCH SERVER
:: ============================================================================
:step4
echo   %E%[93m[STEP 4/4]%E%[0m  %E%[97mStarting Sentinel Server...%E%[0m
echo   %E%[2m----------------------------------------------------------------------%E%[0m
echo.

:: Open both portals in browser after a short delay
start "" /min cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:8000/cipher & start http://localhost:8000/"

echo   %E%[42;97m READY %E%[0m  %E%[1;92mServer is starting on port 8000%E%[0m
echo.
echo   %E%[2m-----------------------------------------------------------------------%E%[0m
echo.
echo   %E%[1;97m  Access Points:%E%[0m
echo.
echo     %E%[95mOfficer CIPHER%E%[0m  %E%[2mAdmin Command Center%E%[0m
echo     %E%[96m  http://localhost:8000/cipher%E%[0m
echo.
echo     %E%[95mCitizen Portal%E%[0m  %E%[2mPublic Safety Services%E%[0m
echo     %E%[96m  http://localhost:8000/%E%[0m
echo.
echo   %E%[2m-----------------------------------------------------------------------%E%[0m
echo.
echo   %E%[1;97m  Officer CIPHER Credentials (Case-Sensitive):%E%[0m
echo     %E%[2mUsername:%E%[0m  %E%[92mOfficer_CIPHER%E%[0m
echo     %E%[2mEmail:%E%[0m     %E%[96mofficercipher.gujaratpolice@gov.in%E%[0m
echo     %E%[2mPasscode:%E%[0m  %E%[93mOfficier_CIPHER@404%E%[0m
echo     %E%[2mOr click%E%[0m  %E%[93m"Quick Login"%E%[0m %E%[2mbutton for instant 1-click access%E%[0m
echo.
echo   %E%[2m-----------------------------------------------------------------------%E%[0m
echo.
echo   %E%[97m  Press %E%[91mCtrl+C%E%[0m%E%[97m to stop the server.%E%[0m
echo   %E%[2m  Browser tabs will open automatically in a few seconds.%E%[0m
echo.
echo   %E%[94m=======================================================================%E%[0m
echo.

title Gujarat Police Sentinel - LIVE on http://localhost:8000

:: Launch the actual server
cd backend
"%~dp0.venv\Scripts\python.exe" -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

:: If server exits
echo.
echo   %E%[93m  Server has stopped.%E%[0m
echo.
pause
