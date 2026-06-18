# Ancient Civilizations — Final Exam Review 🏛️

A fun, interactive quiz about ancient civilizations for 6‑7th‑grade students.  
You can run it **online** (so scores are saved in the cloud) **or** **locally** on your own computer.

---

## 📡 Online Version – Kid‑Friendly Steps

### What this is
A quiz you can launch on the internet (like a website). Your scores are stored in the cloud, so you can see them from any computer.

### Files in this folder
- `app.py` – the program that runs the quiz
- `requirements.txt` – tells the computer which extra tools it needs
- `README.md` – this file (you’re reading it!)

### How to put it on the internet (Super Simple!)
1. **Make a GitHub account** (ask a grown‑up if you need help).  
2. Click the green **“Code” → Download ZIP** button on this page, unzip it, and drag the whole folder into a *new* repository on GitHub.  
3. Go to **[Streamlit Community Cloud](https://share.streamlit.io/)** and log in with the same GitHub account.  
4. Press **“New app**”.
   - Choose the repo you just made.
   - Set **Main file path** to `app.py`.
   - Click **Deploy**.
5. While it’s building, open **Settings → Secrets** in Streamlit and add these secret names (you can type any placeholder like `test` if you don’t have real keys yet):
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `OLLAMA_URL`
   - `OLLAMA_MODEL`
   - `OLLAMA_API_KEY`
   *(If you don’t have those keys, the app still works – just without cloud scoring.)*
6. When the build finishes you’ll get a link like `https://your‑name‑app.streamlit.app`. Click it – the quiz is ready!

### Test it on your own computer (optional)
```bash
# Create a safe place for the program
python3 -m venv .venv
source .venv/bin/activate   # on Windows use: .venv\Scripts\activate

# Install what it needs
pip install -r requirements.txt

# Run the quiz
streamlit run app.py
```
A browser window will open at `http://localhost:8501`. You can play even without the internet, but your scores won’t be saved online.

---

## 💻 Local Version – Kid‑Friendly Steps

### What this is
A simple quiz you can run **right on your own computer**. It stores your scores in a tiny hidden file, so you can keep playing over and over.

### Files you’ll see
- `app.py` – the program that runs the quiz
- `requirements.txt` – a short list of extra tools the program needs
- `README.md` – this paper (you’re reading it!)

### How to start the quiz (super easy!)
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

### What happens behind the scenes?
- The program creates a tiny file called **`progress.db`** in this folder. It’s just a little notebook that stores your name, streaks, and how many questions you got right.
- You can close the browser or the terminal; the next time you run the steps again, your scores will still be there.

### Want more questions?
All the question files (`ancient_civ_questions.json`, etc.) live right here in this folder. If you add or edit those JSON files, the quiz will automatically use the new questions the next time you start it.

---

Enjoy learning about ancient Greece, Rome, Egypt and more! 🎉