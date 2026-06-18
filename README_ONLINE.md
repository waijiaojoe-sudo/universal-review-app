# Online Version – Quick Start Guide

## What this is
A quiz about any subject that you can run on the internet (like a website). It saves your scores in the cloud, so you can see them from any computer.

## Files in this folder
- `app.py` – the program that runs the quiz
- `requirements.txt` – tells the computer which extra tools it needs
- `README.md` – this guide (you’re reading it!)

## How to put it on the internet (Step-by-Step)

1. **Create a GitHub account** (if you don't have one already).  
2. **Upload the project**: Download the project ZIP, unzip it, and upload the folder to a new repository on GitHub.  
3. Go to **[Streamlit Community Cloud](https://share.streamlit.io/)** and log in with your GitHub account.  
4. Press **“New app”**.
   - Choose the repo you just made.
   - Set **Main file path** to `app.py`.
   - Click **Deploy**.
5. While it’s building, open **Settings → Secrets** in Streamlit and add these secret names (you can use placeholder text like `test` if you don’t have real keys yet):
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

A window will open at `http://localhost:8501`. You can play even without the internet, but your scores won’t be saved online.

---

Happy studying! 🎉