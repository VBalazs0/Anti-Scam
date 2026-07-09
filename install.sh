#!/usr/bin/env bash
set -euo pipefail

echo "============================================"
echo "  AntiScam - Discord Bot Installer"
echo "============================================"
echo ""

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "[ERROR] Python is not installed or not in PATH."
    echo "Please install Python 3.10+ from https://www.python.org/"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)

echo "[1/3] Creating virtual environment..."
"$PYTHON" -m venv venv
source venv/bin/activate

echo "[2/3] Installing dependencies..."
pip install -r requirements.txt

echo "[3/3] Setting up configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "  Created .env from .env.example"
        echo "  [IMPORTANT] Edit .env and set your Discord bot TOKEN!"
    fi
else
    echo "  .env already exists, skipping."
fi

echo ""
echo "============================================"
echo "  Installation complete!"
echo "============================================"
echo ""
echo "  Next steps:"
echo "  1. Edit .env and paste your bot token:  TOKEN=your_token_here"
echo "  2. Add reference scam images to the img/ folder"
echo "  3. Run the bot:  venv/bin/python bot.py"
echo ""
