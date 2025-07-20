@echo off
echo 🔧 Fixing Flask Launcher Issue...

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Reinstall Flask to fix the launcher paths
echo 📦 Reinstalling Flask to fix launcher paths...
pip uninstall -y flask
pip install flask

echo ✅ Flask launcher fixed! You can now use 'flask run' command.
echo.
echo 💡 To run your app, use either:
echo    1. python app.py
echo    2. flask run (after setting FLASK_APP=app.py)
echo    3. Double-click start_rahasoft.bat
echo.
pause
