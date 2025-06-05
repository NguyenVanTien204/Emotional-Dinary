$ErrorActionPreference = "Stop"

Write-Host "Setting up development environment..." -ForegroundColor Green

# Check if Python is installed
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed. Please install Python 3.8 or later." -ForegroundColor Red
    exit 1
}

# Check if MongoDB is installed
if (!(Get-Command mongod -ErrorAction SilentlyContinue)) {
    Write-Host "MongoDB is not installed. Please install MongoDB Community Server." -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
.\venv\Scripts\Activate

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create .env file if it doesn't exist
if (!(Test-Path .env)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "Please update .env file with your configurations." -ForegroundColor Yellow
}

# Initialize MongoDB
Write-Host "Initializing MongoDB..." -ForegroundColor Yellow
mongo localhost:27017/emotional_diary_db ./Setup/MongoDB_Setup.js

Write-Host "`nSetup completed!" -ForegroundColor Green
Write-Host "To start the application:"
Write-Host "1. Activate virtual environment: .\venv\Scripts\Activate"
Write-Host "2. Run the application: python main.py"
Write-Host "3. Visit http://localhost:5000 in your browser"
