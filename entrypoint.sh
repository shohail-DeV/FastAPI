#!/bin/sh

echo "🚀 Starting FastAPI application..."

# Step 1: Validate environment
if [ -z "$DATABASE_URL" ]; then
  echo "❌ ERROR: DATABASE_URL not set"
  exit 1
fi

echo "✅ Environment validated"

# Step 2: Wait for database (with retry logic)
echo "⏳ Waiting for MySQL database..."

until python -c "
import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import os

try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    conn = engine.connect()
    conn.close()
    print('✅ Database connection successful')
except OperationalError as e:
    print(f'⚠️  Database not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
  echo "🔄 Retrying database connection..."
  sleep 3
done

echo "✅ Database is ready!"

# Step 3: Start application
echo "🚀 Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000