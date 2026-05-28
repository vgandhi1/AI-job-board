#!/bin/bash
# Install Playwright system dependencies (Ubuntu 24.04 / Noble).
#
# `playwright install-deps` does not currently work on Ubuntu 24.04 because
# upstream still references package names that were renamed in Noble. This
# script installs the explicit package set instead.

set -e

echo "Installing Playwright system dependencies for Ubuntu 24.04..."

sudo apt-get update && sudo apt-get install -y \
  libnss3 \
  libnspr4 \
  libatk1.0-0t64 \
  libatk-bridge2.0-0t64 \
  libatspi2.0-0t64 \
  libcups2t64 \
  libdrm2 \
  libxkbcommon0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libasound2t64 \
  libpango-1.0-0 \
  libcairo2 \
  libgtk-3-0t64 \
  libgdk-pixbuf-2.0-0 \
  libxss1 \
  libxshmfence1 \
  libglib2.0-0t64 \
  libpng16-16t64

echo "Playwright system dependencies installed."
echo "Next: cd backend && uv run playwright install chromium"
