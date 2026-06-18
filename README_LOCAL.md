# Local Version – Quick Start Guide

## What this is
A simple quiz you can run **right on your own computer**. It stores your scores in a tiny hidden file, so you can keep playing over and over without an internet connection.

## Files you’ll see
- `app.py` – the program that runs the quiz
- `requirements.txt` – a short list of extra tools the program needs
- `README.md` – this guide (you’re reading it!)

## How to set up and start the quiz (Step-by-Step)

### 1. Get the files on your computer
The easiest way is to download the folder to your **Documents** folder.

**Fast Setup (using Git):**
If you have Git installed, open your terminal and run these commands:
```bash
cd ~/Documents
git clone https://github.com/waijiaojoe-sudo/ancient-civ-review.git
cd ancient-civ-review
```

**Manual Setup:**
Download the project ZIP, unzip it, and move the folder to `~/Documents/ancient-civ-review`. Then open your terminal and type:
```bash
cd ~/Documents/ancient-civ-review
```

### 2. Start the App
Since this program uses a "virtual environment" (a safe bubble for the code), you can run it with one click using the script provided in this folder.

**On macOS / Linux:**
1. Right-click the file `run_app.sh` and choose **Open With → Terminal**.
2. Or run it from the terminal:
   ```bash
   chmod +x run_app.sh
   ./run_app.sh
   ```

**On Windows:**
1. Double-click the file `run_app.bat`.

### 3. Play!
Your web browser will open a page at `http://localhost:8501`. Click around, type your name, and start answering questions.

## What happens behind the scenes?
- The program creates a tiny file called **`progress.db`** in this folder. It’s like a little notebook that stores your name, streaks, and how many questions you got right.
- You can close the browser or the terminal; the next time you run the app, your scores will still be there.

## Want more questions?
All the question files (`ancient_civ_questions.json`, etc.) are in this folder. If you edit those JSON files, the quiz will automatically use the new questions the next time you start it.

---

Enjoy learning about ancient Greece, Rome, Egypt and more! 🎉