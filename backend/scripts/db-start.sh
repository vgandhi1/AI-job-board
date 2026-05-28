#!/bin/bash
# Start the PostgreSQL (pgvector) container defined in the project-root
# docker-compose.yml. Loads .env from the project root automatically.

set -e

# Resolve project root (../../ from this script's directory).
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$PROJECT_ROOT"

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

if [ ! -f docker-compose.yml ]; then
    echo "Error: docker-compose.yml not found at $PROJECT_ROOT"
    exit 1
fi

echo "Starting database container via docker compose (project: $PROJECT_ROOT) ..."
docker compose up -d postgres

echo "Waiting for database to be ready..."
for i in {1..30}; do
    if docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-postgres}" >/dev/null 2>&1; then
        echo "Database is ready."
        exit 0
    fi
    sleep 1
done

echo "Warning: database did not become ready within 30 seconds. Check 'docker compose logs postgres'."
