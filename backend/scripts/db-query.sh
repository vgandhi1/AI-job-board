#!/bin/bash
# Run a single SQL query against the project's postgres container.
#
# Usage: ./backend/scripts/db-query.sh "SELECT COUNT(*) FROM jobs;"
#
# NOTE: the SQL is passed via -c, which executes it as a parameterless statement
# inside psql. Do NOT interpolate untrusted input into the query string from
# outside this script. For repeatable or parameterized queries, use a .sql
# file or psql variables.

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 'SELECT * FROM jobs LIMIT 5;'"
    exit 1
fi

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

docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"
