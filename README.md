# Ancient Civilizations — Final Exam Review 🏛️

Interactive review app for 6th-7th grade Ancient Civilizations final exam.

**322 review questions** across three categories:
- 📖 **Vocabulary** — 131 terms and definitions
- 👤 **People & Places** — 132 key people, places, and civilizations
- ⚡ **Key Events** — 59 major events and developments

## Features
- Practice by chapter, category, or random mix
- Score tracking with Supabase backend
- 🔥 Streak tracking — bonus motivation for competitive students
- 🏆 Leaderboard — see who's on top
- ❌ Missed question review — automatically tracks what you got wrong

## Deployment

### 1. Set up Supabase tables
Run `supabase_schema.sql` in your Supabase SQL Editor.

### 2. Deploy to Streamlit Community Cloud
1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect the repo
4. Add secret: `SUPABASE_KEY` = your Supabase anon key

### 3. Share the app URL with students!

## Local Development
```bash
pip install -r requirements.txt
export SUPABASE_KEY="your-anon-key"
streamlit run app.py
```

## Questions?
Built for Joe's after-school Ancient Civilizations course.