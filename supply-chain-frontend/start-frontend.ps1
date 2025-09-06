# Start Supply Chain Frontend Development Server
Write-Host "🚀 Starting Supply Chain Frontend..." -ForegroundColor Cyan
Write-Host "=" * 60

Write-Host "📦 Installing dependencies (if needed)..." -ForegroundColor Yellow
cmd /c "npm install"

Write-Host "🌐 Starting Next.js development server..." -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Green
Write-Host "Make sure your backend is running at: http://localhost:8000" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "=" * 60

# Start the development server
try {
    cmd /c "npm run dev"
} catch {
    Write-Host "❌ Error starting frontend: $_" -ForegroundColor Red
}

Write-Host "👋 Frontend stopped" -ForegroundColor Gray
