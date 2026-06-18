# Local Version – Kid‑Friendly Steps

## What this is
A simple quiz you can run **right on your own computer**. It saves your scores in a tiny hidden file, so you can keep playing over and over.

## Files you’ll see
- `app.py` – the program that runs the quiz
- `requirements.txt` – a short list of extra tools the program needs
- `README.md` – this paper (you’re reading it!)

## How to start the quiz (super easy!)
1. **Open a terminal** (ask a grown‑up if you’re not sure).  
2. **Go to the folder** that has the files (replace the path if needed):
   ```bash
   cd /Users/joe/Downloads/ancient-civ-review
   ```
3. **Make a safe “bubble” for the program** so it doesn’t affect anything else:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # on Windows use: .venv\Scripts\activate
   ```
4. **Give the program the tools it needs**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the quiz!**
   ```bash
   streamlit run app.py
   ```
6. Your web browser will open a page at `http://localhost:8501`. Click around, type your name, and start answering questions.

## What happens behind the scenes?
- The program creates a tiny file called **`progress.db`** in this folder. It’s just a little notebook that stores your name, streaks, and how many questions you got right.
- You can close the browser or the terminal; the next time you run the steps again, your scores will still be there.

## Want more questions?
All the question files (`ancient_civ_questions.json`, etc.) live right here in this folder. If you add or edit those JSON files, the quiz will automatically use the new questions the next time you start it.

---

Enjoy learning about ancient Greece, Rome, Egypt and more! 🎉