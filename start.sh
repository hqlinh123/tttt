#!/bin/bash
set -e

echo "🚀 Starting backend project..."

if [ ! -d "venv_new" ]; then
  echo "❌ venv not found"
  exit 1
fi

source venv_new/bin/activate
echo "🐍 Python: $(which python)"

# Install requirements if requirements.txt exists
if [ -f "requirements.txt" ]; then
  echo "📦 Installing requirements..."
  pip install -r requirements.txt
fi

# load env
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "🗄️ Running migrations..."
# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
  echo "❌ alembic not found. Installing..."
  pip install alembic
fi

# Run migrations
alembic revision --autogenerate -m "init" 2>/dev/null || echo "No changes detected"
alembic upgrade head
echo "✅ DB migrated"

uvicorn main:app --reload