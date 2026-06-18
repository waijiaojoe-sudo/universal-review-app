# Local Version – Quick Start Guide

## What this is
A simple quiz you can run **right on your own computer**. It stores your scores in a tiny hidden file, so you can keep playing over and over without an internet connection.

## Files you’ll see
- `app.py` – the program that runs the quiz
- `requirements.txt` – a short list of extra tools the program needs
- `README.md` – this guide (you’re reading it!)

## How to set up and start the quiz (Step-by-Step)

### 1. Get the files on your computer
The easiest way is to put the folder in your **Documents**.

**Fast Setup (using Git):**
If you have Git installed, open your terminal and run these commands:
```bash
cd ~/Documents
git clone https://github.com/waijiaojoe-sudo/universal-review-app.git
cd universal-review-app
```

**Manual Setup:**
Download the project ZIP, unzip it, and move the folder to `~/Documents/universal-review-app`. Then open your terminal and type:
```bash
cd ~/Documents/universal-review-app
```

### 2. Start the App
To make it easy, use the **`run_app.sh`** (macOS/Linux) or **`run_app.bat`** (Windows) file.
- **macOS/Linux:** Double-click `run_app.sh` or run `./run_app.sh` in the terminal.
- **Windows:** Double-click `run_app.bat`.

### 3. Play!
Your web browser will open a page at `http://localhost:8501`. Click around, type your name, and start answering questions.

## What happens behind the scenes?
- The program creates a tiny file called **`progress.db`** in this folder. It’s like a little notebook that stores your name, streaks, and how many questions you got right.
- You can close the browser or the terminal; the next time you run the app, your scores will still be there.

## Want more questions?
All the question files live in the `subjects/` folder. Just create a new folder for your subject (like `subjects/Science/`) and drop your `.json` question files inside it. The app will automatically find them!

## 🧹 Cleaning Up (Uninstalling)
If you want to remove the app from your computer, it's very simple:
- Just **delete the `universal-review-app` folder**. 
- Because the app is "portable," everything (including your scores in `progress.db` and the tools in `.venv`) is kept inside that one folder. Deleting the folder removes everything completely.
