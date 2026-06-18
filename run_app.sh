#!/bin/bash
# run_app.sh - Easy launcher for Ancient Civ Review
# This script handles the virtual environment and launches Streamlit

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Define venv path
VENV_DIR=".venv"

echo "🚀 Starting Ancient Civilizations Review..."

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating a safe environment (.venv)..."
    python3 -m venv $VENV_DIR
fi

# Activate venv
source $VENV_DIR/bin/activate

# Install/Update requirements
echo "⚙️ Checking for required tools..."
pip install -r requirements.txt --quiet

# Run the app
echo "🌐 Launching the app... please wait for your browser to open."
streamlit run app.py
