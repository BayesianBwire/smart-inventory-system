@echo off
echo 🚀 Starting RahaSoft ERP Application...
echo.
echo 📍 Project: RahaSoft Enterprise Resource Planning
echo 🌐 URL: http://localhost:5000
echo 📧 Support: rahasoft.app@gmail.com
echo.

REM Activate virtual environment and run Flask app
call venv\Scripts\activate.bat

REM Set Flask environment variables
set FLASK_APP=app.py
set FLASK_DEBUG=1

echo ⚙️  Starting Flask with environment variables...
echo FLASK_APP=%FLASK_APP%
echo.

echo Choose how to run your app:
echo [1] Python directly (recommended - always works)
echo [2] Flask run command (using full path)
echo.
choice /c 12 /m "Select option (1 or 2): "

if errorlevel 2 goto flaskrun
if errorlevel 1 goto pythonrun

:pythonrun
echo.
echo 🐍 Starting with Python directly...
C:\Users\BWIRE\rahasoft-erp\venv\Scripts\python.exe app.py
goto end

:flaskrun
echo.
echo ⚡ Starting with Flask run command...
C:\Users\BWIRE\rahasoft-erp\venv\Scripts\python.exe -m flask run
goto end

:end
pause
