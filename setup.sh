#!/bin/bash
#
# Unified setup script for the AI Job Board (backend + frontend).
# Run from the project root:
#
#     ./setup.sh
#
# What it does:
#   1. Creates a Python venv for the backend (uv preferred, falls back to venv).
#   2. Installs backend deps from backend/requirements.txt.
#   3. Installs Playwright Chromium for the scraper subsystem.
#   4. Installs frontend deps via npm.
#   5. Creates a root .env file if one does not already exist.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

command_exists() { command -v "$1" >/dev/null 2>&1; }

echo -e "${BLUE}Setting up AI Job Board (project root: $SCRIPT_DIR)${NC}"

# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------
echo -e "\n${BLUE}[1/4] Backend - Python environment${NC}"
cd "$SCRIPT_DIR/backend" || { echo -e "${RED}backend/ not found${NC}"; exit 1; }

if ! command_exists python3; then
    echo -e "${RED}python3 is not installed${NC}"
    exit 1
fi

USE_UV=false
if command_exists uv; then
    USE_UV=true
    echo "Using uv for package management."
    [ -d ".venv" ] || uv venv
    uv pip install --upgrade pip
    uv pip install -r requirements.txt
else
    if python3 -m venv --help >/dev/null 2>&1; then
        echo "uv not found - falling back to python -m venv."
        [ -d "venv" ] || python3 -m venv venv
        # shellcheck disable=SC1091
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        echo -e "${YELLOW}Neither uv nor python3-venv is available.${NC}"
        echo -e "${YELLOW}Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Playwright
# ---------------------------------------------------------------------------
echo -e "\n${BLUE}[2/4] Backend - Playwright Chromium${NC}"
if [ "$USE_UV" = true ]; then
    uv run playwright install chromium || \
        echo -e "${YELLOW}Playwright install failed. Try: ./backend/scripts/install-playwright-deps.sh${NC}"
else
    python -m playwright install chromium || \
        echo -e "${YELLOW}Playwright install failed. Try: ./backend/scripts/install-playwright-deps.sh${NC}"
fi

cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------
echo -e "\n${BLUE}[3/4] Frontend - npm install${NC}"
cd "$SCRIPT_DIR/frontend" || { echo -e "${RED}frontend/ not found${NC}"; exit 1; }

if ! command_exists npm; then
    echo -e "${RED}npm is not installed${NC}"
    exit 1
fi
npm install

cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# .env
# ---------------------------------------------------------------------------
echo -e "\n${BLUE}[4/4] Root .env${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}.env created from .env.example. Edit it and set OPENAI_API_KEY.${NC}"
    else
        echo -e "${YELLOW}.env.example missing - skipping .env creation.${NC}"
    fi
else
    echo ".env already exists."
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo -e "\n${GREEN}Setup complete.${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env and set OPENAI_API_KEY."
echo "  2. Start everything with: docker compose up -d"
echo "     (or run backend/frontend manually, see README.md)"
