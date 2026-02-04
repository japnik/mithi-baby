#!/bin/bash

# Define environment directory
VENV_DIR=".venv"

echo "🚀 Mithi Baby Server Launcher"
echo "============================="

# 1. Check/Create Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating isolated Python environment (.venv)..."
    python3 -m venv $VENV_DIR
    echo "✅ Environment created."
else
    echo "✅ Found existing environment."
fi

# 2. Activate & Upgrade Pip (Quietly)
source $VENV_DIR/bin/activate
pip install --upgrade pip > /dev/null 2>&1

# 3. Install Dependencies
echo "📥 Checking dependencies..."
pip install -r backend/requirements.txt | grep -v 'Requirement already satisfied'

# 4. Start Server
echo "============================="
echo "🎵 Starting Server on Port 8080..."
echo "✅ Python: $(which python)"
python backend/server.py
