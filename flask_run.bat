@echo off
echo 🚀 Starting RahaSoft ERP with Flask Run Command
echo ================================================

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Set Flask environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Display configuration
echo ✅ Flask App: %FLASK_APP%
echo ✅ Flask Environment: %FLASK_ENV%
echo ✅ Debug Mode: %FLASK_DEBUG%
echo ✅ Server: http://127.0.0.1:5000
echo.

REM Run Flask application
echo 🌐 Starting Flask development server...
flask run --host=127.0.0.1 --port=5000

pause
