# 🚀 RahaSoft ERP - Flask Run Script
# ===================================

# Activate virtual environment
& .\venv\Scripts\Activate.ps1

# Set Flask environment variables
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"

# Display configuration
Write-Host "✅ Flask App: $env:FLASK_APP" -ForegroundColor Green
Write-Host "✅ Flask Environment: $env:FLASK_ENV" -ForegroundColor Green
Write-Host "✅ Debug Mode: $env:FLASK_DEBUG" -ForegroundColor Green
Write-Host "✅ Server: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host ""

# Run Flask application
Write-Host "🌐 Starting Flask development server..." -ForegroundColor Cyan
flask run --host=127.0.0.1 --port=5000
