@echo off
:: run_app.bat - Easy launcher for Ancient Civ Review
setlocal enabledelayedexpansion

echo 🚀 Starting Ancient Civilizations Review...

:: Create virtual environment if it doesn't exist
if not exist .venv (
    echo 📦 Creating a safe environment (.venv)...
    python -m venv .venv
)

:: Activate venv
call .venv\Scripts\activate

:: Install/Update requirements
echo ⚙️ Checking for required tools...
pip install -r requirements.txt --quiet

:: Run the app
echo 🌐 Launching the app... please wait for your browser to open.
streamlit run app.py

pause