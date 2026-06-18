# Universal Review App 📚

A fun, interactive quiz tool that lets you build study guides for any subject.  
You can run it **online** (cloud scores) **or** **locally** on your own computer (offline scores).

---

## 📡 Online Version – Quick Start Guide

### What this is
A quiz you can launch on the internet (like a website). Your scores are stored in the cloud, so you can see them from any computer.

### How to put it on the internet (Step-by-Step)
1. **Create a GitHub account** (if you don't have one already).  
2. **Upload the project**: Download the project ZIP, unzip it, and upload the folder to a new repository on GitHub.  
3. Go to **[Streamlit Community Cloud](https://share.streamlit.io/)** and log in with your GitHub account.  
4. Press **“New app”**.
   - Choose the repo you just made.
   - Set **Main file path** to `app.py`.
   - Click **Deploy**.
5. While it’s building, open **Settings → Secrets** in Streamlit and add these secret names (use placeholder text like `test` if you don’t have real keys yet):
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

---

## 💻 Local Version – Quick Start Guide

### What this is
A simple quiz you can run **right on your own computer**. It stores your scores in a tiny hidden file, so you can keep playing over and over.

### How to set up and start the quiz (Step-by-Step)

**1. Get the files on your computer**
The easiest way is to put the folder in your **Documents**.

- **Fast Setup (using Git):**
  ```bash
  cd ~/Documents
  git clone https://github.com/waijiaojoe-sudo/universal-review-app.git
  cd universal-review-app
  ```
- **Manual Setup:** Download the project ZIP, unzip it, and move it to `~/Documents/universal-review-app`.

**2. Start the App**
To make it easy, use the **`run_app.sh`** (macOS/Linux) or **`run_app.bat`** (Windows) file.
- **macOS/Linux:** Double-click `run_app.sh` or run `./run_app.sh` in the terminal.
- **Windows:** Double-click `run_app.bat`.

**3. Play!**
Your web browser will open a page at `http://localhost:8501`. Type your name and start reviewing!

---

### ⚙️ Behind the Scenes
- **Saving Progress:** The app creates a file called `progress.db` to remember your streaks and correct answers.
- **Adding Subjects:** Create a folder in `subjects/` (e.g., `subjects/Math/`) and add your `.json` question files there.

Happy studying! 🎉