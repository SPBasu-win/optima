# Start Supply Chain Backend Server
Write-Host "🚀 Starting Supply Chain Command Center Backend..." -ForegroundColor Cyan
Write-Host "=" * 60

# Activate virtual environment
if (Test-Path "venv\Scripts\activate.bat") {
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
    cmd /c "venv\Scripts\activate.bat"
}

Write-Host "🌐 Starting server at http://localhost:8000" -ForegroundColor Green
Write-Host "📚 API Documentation will be at http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "=" * 60

# Start the server
try {
    uvicorn main_dev:app --host 0.0.0.0 --port 8000 --reload
} catch {
    Write-Host "❌ Error starting server: $_" -ForegroundColor Red
}

Write-Host "👋 Server stopped" -ForegroundColor Gray
