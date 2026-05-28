#!/bin/bash
# Open an interactive psql session against the project's postgres container,
# using credentials from the project-root .env.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$PROJECT_ROOT"

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-jobboard}"

echo "Connecting as user='$POSTGRES_USER' to db='$POSTGRES_DB' ..."
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
