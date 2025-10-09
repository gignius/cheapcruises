#!/bin/bash
# Quick start script for local development

echo "🚀 CheapCruises.io Quick Start"
echo "================================"

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 not found. Please install Python 3.11+"
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    # Use SQLite for development
    echo "DATABASE_URL=sqlite+aiosqlite:///./cruises.db" > .env
    cat .env.example | grep -v DATABASE_URL >> .env
fi

# Initialize database
echo "💾 Initializing database..."
python -c "import asyncio; from database_async import init_db; asyncio.run(init_db())"

# Initialize promo codes
echo "🎟️  Initializing promo codes..."
python init_promo_codes.py

# Run initial scrape
echo "🔍 Running initial scrape (this may take a minute)..."
python run_scraper.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting development server..."
echo "   Visit: http://localhost:8000"
echo "   API Docs: http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the server
python app.py



