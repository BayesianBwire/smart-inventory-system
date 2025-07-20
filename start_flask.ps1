# PowerShell script to run Flask properly
Write-Host "🚀 Starting RahaSoft with Flask..." -ForegroundColor Green

# Set environment variables
$env:FLASK_APP = "app.py"
$env:FLASK_DEBUG = "1"

Write-Host "📍 FLASK_APP: $env:FLASK_APP" -ForegroundColor Cyan
Write-Host "🔧 FLASK_DEBUG: $env:FLASK_DEBUG" -ForegroundColor Cyan
Write-Host ""

# Try flask run first, fallback to python app.py
try {
    Write-Host "🌟 Attempting to run with 'flask run'..." -ForegroundColor Yellow
    flask run
} catch {
    Write-Host "⚠️  Flask command failed, using python app.py instead..." -ForegroundColor Yellow
    python app.py
}

Read-Host "Press Enter to exit..."
