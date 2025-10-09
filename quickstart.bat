@echo off
REM Quick start script for Windows

echo 🚀 CheapCruises.io Quick Start
echo ================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.11+
    exit /b 1
)

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Create .env if it doesn't exist
if not exist ".env" (
    echo ⚙️  Creating .env file...
    echo DATABASE_URL=sqlite+aiosqlite:///./cruises.db > .env
    echo ENVIRONMENT=development >> .env
    echo LOG_LEVEL=INFO >> .env
)

REM Initialize database
echo 💾 Initializing database...
python -c "import asyncio; from database_async import init_db; asyncio.run(init_db())"

REM Initialize promo codes
echo 🎟️  Initializing promo codes...
python init_promo_codes.py

REM Run initial scrape
echo 🔍 Running initial scrape (this may take a minute)...
set PYTHONIOENCODING=utf-8
python run_scraper.py

echo.
echo ✅ Setup complete!
echo.
echo 🚀 Starting development server...
echo    Visit: http://localhost:8000
echo    API Docs: http://localhost:8000/api/docs
echo.
echo Press Ctrl+C to stop
echo.

REM Start the server
python app.py


