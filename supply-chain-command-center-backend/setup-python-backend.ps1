# Supply Chain Backend Setup Script (Python Version)
Write-Host "🐍 Setting up Supply Chain Command Center Backend with Python" -ForegroundColor Cyan
Write-Host "=" * 60

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -like "*Python 3.*") {
        Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ Python 3 not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

# Create virtual environment
Write-Host "`n📦 Creating Python virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists" -ForegroundColor Gray
} else {
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n🔧 Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "❌ Could not activate virtual environment" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "`n📥 Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

try {
    # Use the simplified requirements file
    python -m pip install --upgrade pip
    python -m pip install -r requirements-dev.txt
    Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Error installing dependencies" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Create uploads and temp directories
Write-Host "`n📁 Creating necessary directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "temp" | Out-Null
New-Item -ItemType Directory -Force -Path "models" | Out-Null
Write-Host "✅ Directories created" -ForegroundColor Green

Write-Host "`n🚀 Starting the backend server..." -ForegroundColor Cyan
Write-Host "Server will be available at:" -ForegroundColor White
Write-Host "🌐 API: http://localhost:8000" -ForegroundColor Green
Write-Host "📚 Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "=" * 60

# Start the development server
try {
    python main_dev.py
} catch {
    Write-Host "`n❌ Error starting the server" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host "`n👋 Backend stopped" -ForegroundColor Gray
