@echo off
TITLE Disaster Relief & Resource Management System
echo ======================================================================
echo    DISASTER RELIEF AND RESOURCE MANAGEMENT SYSTEM
echo    Starting application server...
echo ======================================================================

:: Attempt standard python first
python --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    SET PY_CMD=python
    GOTO RUN_APP
)

:: Check direct install path of Python 3.12
IF EXIST "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    SET PY_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    GOTO RUN_APP
)

:: Check standard py launcher
py -3 --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    SET PY_CMD=py -3
    GOTO RUN_APP
)

echo [ERROR] Python was not found in your system PATH!
echo Please install Python 3.10+ from python.org or ensure it is added to your PATH.
pause
exit /b 1

:RUN_APP
echo Using Python: %PY_CMD%
echo Installing dependencies (if needed)...
%PY_CMD% -m pip install -r requirements.txt --quiet

echo.
echo Launching your browser at: http://127.0.0.1:5000
start http://127.0.0.1:5000

echo.
echo Server running! Press Ctrl+C in this window to stop the server anytime.
echo.
%PY_CMD% app.py
pause
