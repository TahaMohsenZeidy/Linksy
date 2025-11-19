#!/bin/bash
set -e

echo "🚀 Starting Linksy Backend..."

# Extract PostgreSQL connection info from DATABASE_URL if not set
if [ -z "$POSTGRES_HOST" ] && [ -n "$DATABASE_URL" ]; then
    # Parse DATABASE_URL: postgresql://user:pass@host:port/dbname
    POSTGRES_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    POSTGRES_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    POSTGRES_PASSWORD=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    POSTGRES_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
fi

# Default values
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "✅ PostgreSQL is ready!"

# Initialize Keycloak database
echo "🔧 Initializing Keycloak database..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres <<EOF
SELECT 'CREATE DATABASE keycloak'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak')\gexec
EOF
echo "✅ Keycloak database ready!"

# Run Alembic migrations
echo "📦 Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete!"

# Start the application
echo "🎯 Starting FastAPI application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000

