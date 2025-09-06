# Docker Installation Verification and Backend Startup Script
Write-Host "🐳 Checking Docker Installation..." -ForegroundColor Cyan

# Check if Docker is installed
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found. Please install Docker Desktop first." -ForegroundColor Red
    Write-Host "Download from: https://docs.docker.com/desktop/install/windows/" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running!" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    Write-Host "Look for Docker Desktop in your Start menu and launch it." -ForegroundColor Yellow
    exit 1
}

# Check if docker-compose is available
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose found: $composeVersion" -ForegroundColor Green
} catch {
    try {
        $composeVersion = docker compose version
        Write-Host "✅ Docker Compose found: $composeVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker Compose not found." -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n🚀 Starting Supply Chain Command Center Backend..." -ForegroundColor Cyan

# Start the backend services
try {
    # Try new docker compose syntax first
    docker compose up -d
} catch {
    # Fall back to old docker-compose syntax
    docker-compose up -d
}

Write-Host "`n✅ Backend services starting up!" -ForegroundColor Green
Write-Host "🌐 API will be available at: http://localhost:8000" -ForegroundColor Yellow
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "🗄️ MongoDB Admin: http://localhost:8081" -ForegroundColor Yellow

Write-Host "`n⏳ Waiting for services to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Check if API is responding
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 30
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API is ready and responding!" -ForegroundColor Green
        Write-Host "`n🎉 Your Supply Chain Command Center Backend is now running!" -ForegroundColor Green
        
        Write-Host "`nNext steps:" -ForegroundColor Cyan
        Write-Host "1. Visit http://localhost:8000/docs to explore the API" -ForegroundColor White
        Write-Host "2. Set up your Next.js frontend to connect to this backend" -ForegroundColor White
        Write-Host "3. Use the API endpoints for inventory, forecasting, and logistics" -ForegroundColor White
    }
} catch {
    Write-Host "⚠️ API is starting up. Please wait a moment and check http://localhost:8000" -ForegroundColor Yellow
}

Write-Host "`nTo stop the services later, run: docker compose down" -ForegroundColor Gray
