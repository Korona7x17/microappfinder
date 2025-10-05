#!/bin/bash
# T046: Database migration script
# Run Alembic migrations to create all tables

set -e

# Use PostgreSQL 17 path if available
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"

echo "=== Reddit Pain Point Discovery - Database Setup ==="
echo ""

# Check if PostgreSQL is running
echo "Checking PostgreSQL connection..."
if ! psql postgres -c "SELECT 1" > /dev/null 2>&1; then
    echo "Error: PostgreSQL is not running or not accessible"
    echo "Please ensure PostgreSQL is running and accessible"
    exit 1
fi

echo "✓ PostgreSQL is running"
echo ""

# Create database if it doesn't exist
echo "Creating database (if needed)..."
psql postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'microappfinder'" | grep -q 1 || \
    psql postgres -c "CREATE DATABASE microappfinder"

echo "✓ Database exists"
echo ""

# Run Alembic migrations
echo "Running Alembic migrations..."

# Activate API venv if it exists
API_VENV="$(dirname "$0")/../apps/api/venv"
if [ -f "$API_VENV/bin/activate" ]; then
    source "$API_VENV/bin/activate"
fi

# Set PYTHONPATH to include apps/api directory
export PYTHONPATH="$(dirname "$0")/../apps/api:$PYTHONPATH"

cd "$(dirname "$0")/../infra/migrations"

# Check current revision
echo "Current database revision:"
alembic current || echo "No revision applied yet"
echo ""

# Run upgrade
echo "Applying migrations..."
alembic upgrade head

echo ""
echo "✓ Migrations complete"
echo ""

# Verify tables
echo "Verifying tables created..."
TABLES=$(psql -d microappfinder -tc "
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('users', 'topics', 'search_runs', 'search_run_topics', 'reddit_posts', 'pain_points')
")

if [ "$TABLES" -eq 6 ]; then
    echo "✓ All 6 tables created successfully"
else
    echo "⚠ Warning: Expected 6 tables, found $TABLES"
fi

echo ""
echo "=== Database setup complete ==="
