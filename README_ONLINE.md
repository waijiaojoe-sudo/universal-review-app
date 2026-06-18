# Online Version – Kid‑Friendly Steps

## What this is
A fun quiz about ancient civilizations that you can run **on the internet** (like a website). It saves your scores in the cloud, so you can see them from any computer.

## Files in this folder
- `app.py` – the program that runs the quiz
- `requirements.txt` – tells the computer what extra tools it needs
- `README.md` – this paper (you’re reading it!)

## How to put it on the internet (Super Simple!)

1. **Make a GitHub account** (ask a grown‑up if you need help).  
2. Click the green **“Code” → Download ZIP** button on this page, unzip it, and drag the whole folder into a *new* repository on GitHub.  
3. Go to **[Streamlit Community Cloud](https://share.streamlit.io/)** and log in with the same GitHub account.  
4. Press **“New app”**.
   - Choose the repo you just made.
   - Set **Main file path** to `app.py`.
   - Click **Deploy**.
5. While it’s building, open **Settings → Secrets** in Streamlit and add these secret names (you can type any placeholder text like “test” if you don’t have real keys yet):
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `OLLAMA_URL`
   - `OLLAMA_MODEL`
   - `OLLAMA_API_KEY`

   *(If you don’t have those keys, the app still works – just without cloud scoring.)*

6. When the build finishes you’ll get a link like `https://your‑name‑app.streamlit.app`. Click it – the quiz is ready!

## Test it on your own computer (optional)

```bash
# Create a safe place for the program
python3 -m venv .venv
source .venv/bin/activate   # on Windows use: .venv\Scripts\activate

# Install what it needs
pip install -r requirements.txt

# Run the quiz
streamlit run app.py
```

A window will open at `http://localhost:8501`. You can play the quiz even without the internet, but your scores won’t be saved online.

---

Enjoy learning about ancient Greece, Rome, Egypt and more! 🎉