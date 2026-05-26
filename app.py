#!/usr/bin/env python3
"""
Ancient Civilizations — Final Exam Review
A Streamlit app with Supabase score tracking, streaks, and leaderboard.

Deploy: Streamlit Community Cloud (connected to GitHub repo)
Backend: Supabase (Syntaxiom Edu project, separate tables)
"""

import json
import random
import os
import streamlit as st
from supabase import create_client, Client

# ─── Config ───────────────────────────────────────────────────────────────────

def _get_secret(key, default=""):
    """Get a value from Streamlit secrets, falling back to env vars."""
    try:
        return st.secrets[key]
    except (KeyError, AttributeError):
        return os.environ.get(key, default)

SUPABASE_URL = _get_secret("SUPABASE_URL", "https://rfkivouxupijlddrvhjg.supabase.co")
SUPABASE_KEY = _get_secret("SUPABASE_KEY", "")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTION_FILES = [
    "ancient_civ_questions.json",
    "ancient_civ_people_places_questions.json",
    "ancient_civ_key_events_questions.json",
]

CHAPTERS = [
    "Ancient Greece",
    "Golden Age of Greece",
    "Ancient India",
    "Ancient China",
    "Early Romans",
    "The Roman Empire",
    "Christianity & Legacies of Rome",
]

CATEGORIES = [
    {"name": "Vocabulary", "file": "ancient_civ_questions.json", "icon": "📖"},
    {"name": "People & Places", "file": "ancient_civ_people_places_questions.json", "icon": "👤"},
    {"name": "Key Events", "file": "ancient_civ_key_events_questions.json", "icon": "⚡"},
]


# ─── Load Questions ────────────────────────────────────────────────────────────

@st.cache_data
def load_all_questions():
    questions = []
    for qfile in QUESTION_FILES:
        qpath = os.path.join(SCRIPT_DIR, qfile)
        if os.path.exists(qpath):
            with open(qpath, "r", encoding="utf-8") as f:
                questions.extend(json.load(f))
    return questions


# ─── Supabase ──────────────────────────────────────────────────────────────────

def get_supabase() -> Client:
    if not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


def get_or_create_player(supabase: Client, name: str) -> dict | None:
    """Get existing player or create new one. Returns player dict with id."""
    if not supabase or not name.strip():
        return None
    name = name.strip()[:50]

    try:
        # Check if player exists
        result = supabase.table("ancient_civ_players").select("*").eq("name", name).execute()
        if result.data:
            return result.data[0]

        # Create new player
        result = supabase.table("ancient_civ_players").insert({"name": name}).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None


def record_answer(supabase: Client, player_id: int, question_term: str, chapter: str,
                  category: str, correct: bool, streak: int):
    """Record a single answer to Supabase."""
    if not supabase:
        return
    try:
        supabase.table("ancient_civ_scores").insert({
            "player_id": player_id,
            "question_term": question_term,
            "chapter": chapter,
            "category": category,
            "correct": correct,
            "streak": streak,
        }).execute()
    except Exception:
        pass  # Don't break the quiz if DB write fails


def get_leaderboard(supabase: Client, limit: int = 20) -> list:
    """Get top players by best streak and total correct."""
    if not supabase:
        return []
    try:
        result = supabase.table("ancient_civ_scores").select("player_id, correct, streak, ancient_civ_players(name)").execute()
        if not result.data:
            return []

        # Aggregate in Python (Supabase doesn't support complex aggregates via REST)
        players = {}
        for row in result.data:
            pid = row["player_id"]
            if pid not in players:
                pname = row.get("ancient_civ_players", {})
                if isinstance(pname, dict):
                    pname = pname.get("name", "???")
                players[pid] = {"name": pname, "correct": 0, "total": 0, "best_streak": 0}

            players[pid]["total"] += 1
            if row["correct"]:
                players[pid]["correct"] += 1
            players[pid]["best_streak"] = max(players[pid]["best_streak"], row.get("streak", 0))

        # Sort by best_streak desc, then correct desc
        sorted_players = sorted(
            players.values(),
            key=lambda p: (-p["best_streak"], -p["correct"])
        )
        return sorted_players[:limit]
    except Exception:
        return []


def get_player_stats(supabase: Client, player_id: int) -> dict:
    """Get stats for a specific player."""
    if not supabase:
        return {}
    try:
        result = supabase.table("ancient_civ_scores").select("correct, streak, chapter, category").eq("player_id", player_id).execute()
        if not result.data:
            return {"total": 0, "correct": 0, "best_streak": 0, "chapters": {}, "categories": {}}

        stats = {"total": 0, "correct": 0, "best_streak": 0, "chapters": {}, "categories": {}}
        for row in result.data:
            stats["total"] += 1
            if row["correct"]:
                stats["correct"] += 1
            stats["best_streak"] = max(stats["best_streak"], row.get("streak", 0))

            ch = row.get("chapter", "Unknown")
            if ch not in stats["chapters"]:
                stats["chapters"][ch] = {"total": 0, "correct": 0}
            stats["chapters"][ch]["total"] += 1
            if row["correct"]:
                stats["chapters"][ch]["correct"] += 1

            cat = row.get("category", "Unknown")
            if cat not in stats["categories"]:
                stats["categories"][cat] = {"total": 0, "correct": 0}
            stats["categories"][cat]["total"] += 1
            if row["correct"]:
                stats["categories"][cat]["correct"] += 1

        return stats
    except Exception:
        return {}


# ─── Session State Init ────────────────────────────────────────────────────────

def init_session_state():
    defaults = {
        "player_name": "",
        "player_id": None,
        "current_questions": [],
        "current_index": 0,
        "current_streak": 0,
        "best_streak": 0,
        "session_correct": 0,
        "session_total": 0,
        "session_missed": [],
        "quiz_active": False,
        "quiz_title": "",
        "category_label": "",
        "answered_current": False,
        "selected_answer": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─── Quiz Logic ────────────────────────────────────────────────────────────────

def start_quiz(questions: list, title: str, category_label: str = ""):
    """Initialize a new quiz session."""
    shuffled = questions[:]
    random.shuffle(shuffled)
    st.session_state.current_questions = shuffled
    st.session_state.current_index = 0
    st.session_state.current_streak = 0
    st.session_state.best_streak = 0
    st.session_state.session_correct = 0
    st.session_state.session_total = 0
    st.session_state.session_missed = []
    st.session_state.quiz_active = True
    st.session_state.quiz_title = title
    st.session_state.category_label = category_label
    st.session_state.answered_current = False
    st.session_state.selected_answer = None


def check_answer(question: dict, choice_index: int) -> bool:
    """Check if the selected choice is correct."""
    return choice_index == question["answer"]


# ─── UI Pages ──────────────────────────────────────────────────────────────────

def page_login():
    """Player name entry."""
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>🏛️ Ancient Civilizations</h1>
        <h2 style='font-size: 1.3rem; color: #888; font-weight: normal;'>Final Exam Review</h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 👋 Enter your name to start")
    st.markdown("Your scores and streaks will be tracked on the leaderboard!")

    name = st.text_input("Your name:", key="name_input", placeholder="Enter your name...")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Review", type="primary", use_container_width=True, disabled=not name.strip()):
            supabase = get_supabase()
            if supabase:
                player = get_or_create_player(supabase, name.strip())
                if player:
                    st.session_state.player_name = name.strip()
                    st.session_state.player_id = player["id"]
                else:
                    st.session_state.player_name = name.strip()
                    st.session_state.player_id = None
                    st.warning("⚠️ Could not connect to score database. You can still practice, but scores won't be saved.")
            else:
                st.session_state.player_name = name.strip()
                st.session_state.player_id = None
                st.warning("⚠️ Score database not configured. You can still practice, but scores won't be saved.")

            st.rerun()


def page_menu():
    """Main menu after login."""
    all_questions = load_all_questions()

    # Header
    st.markdown(f"""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1 style='font-size: 2rem; margin-bottom: 0.3rem;'>🏛️ Ancient Civilizations Review</h1>
        <p style='color: #888;'>Welcome, <strong>{st.session_state.player_name}</strong> • {len(all_questions)} questions ready</p>
    </div>
    """, unsafe_allow_html=True)

    # Stats bar
    supabase = get_supabase()
    if supabase and st.session_state.player_id:
        stats = get_player_stats(supabase, st.session_state.player_id)
        if stats and stats.get("total", 0) > 0:
            pct = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            st.markdown(f"""
            <div style='display: flex; justify-content: center; gap: 2rem; padding: 0.5rem 0;'>
                <span>📊 <strong>{stats['total']}</strong> questions answered</span>
                <span>✅ <strong>{pct:.0f}%</strong> correct</span>
                <span>🔥 <strong>{stats['best_streak']}</strong> best streak</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")

    # Quick start - random mix
    st.markdown("### 🎲 Quick Start")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔀 10 Random Questions", use_container_width=True):
            sample = random.sample(all_questions, min(10, len(all_questions)))
            start_quiz(sample, "10 Random Questions", "Mixed")
            st.rerun()
    with col2:
        if st.button("🔀 20 Random Questions", use_container_width=True):
            sample = random.sample(all_questions, min(20, len(all_questions)))
            start_quiz(sample, "20 Random Questions", "Mixed")
            st.rerun()

    st.markdown("---")

    # Review by Chapter
    st.markdown("### 📖 Review by Chapter")
    chapter_cols = st.columns(2)
    for i, chapter in enumerate(CHAPTERS):
        ch_questions = [q for q in all_questions if q["chapter"] == chapter]
        with chapter_cols[i % 2]:
            if st.button(f"{chapter} ({len(ch_questions)})", key=f"ch_{i}", use_container_width=True):
                start_quiz(ch_questions, chapter, chapter)
                st.rerun()

    st.markdown("---")

    # Review by Category
    st.markdown("### 📝 Review by Category")
    cat_cols = st.columns(3)
    for i, cat in enumerate(CATEGORIES):
        cat_questions = [q for q in all_questions if
                        any(q.get("term", "") in json.dumps(cq.get("term", "")) for cq in
                            [q] if os.path.exists(os.path.join(SCRIPT_DIR, cat["file"])))]
        # Simpler: load from file directly
        cat_path = os.path.join(SCRIPT_DIR, cat["file"])
        if os.path.exists(cat_path):
            with open(cat_path, "r", encoding="utf-8") as f:
                cat_qs = json.load(f)
        else:
            cat_qs = []
        with cat_cols[i]:
            if st.button(f"{cat['icon']} {cat['name']} ({len(cat_qs)})", key=f"cat_{i}", use_container_width=True):
                start_quiz(cat_qs, cat["name"], cat["name"])
                st.rerun()

    st.markdown("---")

    # Missed questions
    st.markdown("### 🔥 Review Missed Questions")
    if supabase and st.session_state.player_id:
        missed_result = supabase.table("ancient_civ_scores").select("question_term, chapter").eq("player_id", st.session_state.player_id).eq("correct", False).execute()
        if missed_result.data:
            missed_terms = set(row["question_term"] for row in missed_result.data)
            missed_qs = [q for q in all_questions if q["term"] in missed_terms]
            if missed_qs:
                if st.button(f"❌ Review {len(missed_qs)} Missed Questions", use_container_width=True):
                    start_quiz(missed_qs, "Missed Questions", "Missed")
                    st.rerun()
            else:
                st.info("No missed questions found! 🎉")
        else:
            st.info("No missed questions found! 🎉")
    else:
        if st.session_state.session_missed:
            if st.button(f"❌ Review {len(st.session_state.session_missed)} Missed Questions (this session)", use_container_width=True):
                start_quiz(st.session_state.session_missed, "Missed Questions", "Missed")
                st.rerun()
        else:
            st.info("No missed questions yet this session.")

    st.markdown("---")

    # Leaderboard
    st.markdown("### 🏆 Leaderboard")
    if supabase:
        leaderboard = get_leaderboard(supabase)
        if leaderboard:
            for i, player in enumerate(leaderboard):
                rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
                pct = (player["correct"] / player["total"] * 100) if player["total"] > 0 else 0
                highlight = "font-weight: bold; color: #1f77b4;" if player["name"] == st.session_state.player_name else ""
                st.markdown(
                    f"<span style='{highlight}'>{rank_emoji} <strong>{player['name']}</strong> — "
                    f"🔥 {player['best_streak']} streak • ✅ {player['correct']}/{player['total']} ({pct:.0f}%)</span>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No scores yet. Be the first!")
    else:
        st.info("Leaderboard requires database connection.")

    # Logout
    st.markdown("---")
    if st.button("🚪 Log Out"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def page_quiz():
    """Active quiz page."""
    questions = st.session_state.current_questions
    idx = st.session_state.current_index

    if idx >= len(questions):
        # Quiz complete
        page_results()
        return

    q = questions[idx]
    total = len(questions)

    # Progress bar
    progress = (idx) / total
    st.progress(progress)

    # Header
    pct = (st.session_state.session_correct / st.session_state.session_total * 100) if st.session_state.session_total > 0 else 0
    streak_display = f"🔥 {st.session_state.current_streak}" if st.session_state.current_streak > 0 else ""
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <span><strong>{st.session_state.quiz_title}</strong> • Q{idx+1}/{total}</span>
        <span>✅ {pct:.0f}% {streak_display}</span>
    </div>
    """, unsafe_allow_html=True)

    # Streak celebration
    if st.session_state.current_streak >= 5:
        st.markdown(f"🔥 **{st.session_state.current_streak} STREAK! Keep it going!** 🔥")
    if st.session_state.current_streak >= 10:
        st.markdown("⚡ **UNSTOPPABLE! 10+ streak!** ⚡")

    st.markdown("---")

    # Question
    st.markdown(f"### {q['question']}")
    if st.session_state.category_label and st.session_state.category_label not in ("Mixed", "Missed", q.get("chapter", "")):
        st.caption(f"📖 {q['chapter']} • {st.session_state.category_label}")
    else:
        st.caption(f"📖 {q['chapter']}")

    # Answer choices
    labels = ["A", "B", "C", "D"]
    choices = q["choices"]

    if not st.session_state.answered_current:
        # Show choices as buttons
        for i, choice in enumerate(choices):
            if st.button(f"**{labels[i]})** {choice}", key=f"choice_{i}", use_container_width=True):
                st.session_state.selected_answer = i
                st.session_state.answered_current = True

                correct = check_answer(q, i)
                st.session_state.session_total += 1

                if correct:
                    st.session_state.session_correct += 1
                    st.session_state.current_streak += 1
                    st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.current_streak)
                else:
                    st.session_state.current_streak = 0
                    st.session_state.session_missed.append(q)

                # Record to Supabase
                supabase = get_supabase()
                if supabase and st.session_state.player_id:
                    record_answer(
                        supabase, st.session_state.player_id,
                        q["term"], q["chapter"], st.session_state.category_label,
                        correct, st.session_state.current_streak
                    )

                st.rerun()
    else:
        # Show result
        selected = st.session_state.selected_answer
        correct = check_answer(q, selected)

        for i, choice in enumerate(choices):
            if i == q["answer"]:
                st.markdown(f"✅ **{labels[i]}) {choice}**")
            elif i == selected and not correct:
                st.markdown(f"❌ ~~{labels[i]}) {choice}~~")
            else:
                st.markdown(f"&nbsp;&nbsp;&nbsp;{labels[i]}) {choice}")

        st.markdown("---")

        if correct:
            st.success(f"✅ Correct! 🎉")
        else:
            st.error(f"❌ Not quite. The correct answer is **{labels[q['answer']]})**")

        # Explanation
        if q.get("explanation"):
            st.info(f"💡 {q['explanation']}")

        # Streak indicator
        if st.session_state.current_streak >= 3:
            st.markdown(f"🔥 **{st.session_state.current_streak} in a row!**")

        # Next button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("➡️ Next Question", type="primary", use_container_width=True):
                st.session_state.current_index += 1
                st.session_state.answered_current = False
                st.session_state.selected_answer = None
                st.rerun()


def page_results():
    """Show results after completing a quiz."""
    correct = st.session_state.session_correct
    total = st.session_state.session_total
    pct = (correct / total * 100) if total > 0 else 0

    # Emoji based on score
    if pct >= 90:
        emoji = "🏆"
        message = "Outstanding! You're ready for the final!"
    elif pct >= 75:
        emoji = "🎉"
        message = "Great job! Almost there!"
    elif pct >= 60:
        emoji = "💪"
        message = "Good effort! Keep practicing!"
    else:
        emoji = "📚"
        message = "Keep studying — you'll get there!"

    st.markdown(f"""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1>{emoji} Quiz Complete!</h1>
        <h2>{pct:.0f}%</h2>
        <p style='font-size: 1.2rem; color: #888;'>{correct} out of {total} correct</p>
        <p style='font-size: 1.1rem;'>{message}</p>
    </div>
    """, unsafe_allow_html=True)

    # Streak display
    if st.session_state.best_streak >= 3:
        st.markdown(f"<div style='text-align: center;'><p>🔥 Best streak: <strong>{st.session_state.best_streak}</strong> in a row!</p></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Missed questions review
    if st.session_state.session_missed:
        st.markdown("### ❌ Questions You Missed")
        for q in st.session_state.session_missed:
            labels = ["A", "B", "C", "D"]
            st.markdown(f"**{q['term']}** ({q['chapter']})")
            st.markdown(f"→ Correct answer: **{labels[q['answer']]}) {q['choices'][q['answer']]}**")
            if q.get("explanation"):
                st.caption(f"💡 {q['explanation']}")
            st.markdown("")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Retry Missed Questions", use_container_width=True):
                missed = st.session_state.session_missed[:]
                start_quiz(missed, "Missed Questions (Retry)", "Missed")
                st.rerun()
        with col2:
            if st.button("🏠 Back to Menu", use_container_width=True):
                st.session_state.quiz_active = False
                st.rerun()
    else:
        st.markdown("""
        <div style='text-align: center;'>
            <p style='font-size: 1.2rem;'>🌟 Perfect score! You didn't miss any questions!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🏠 Back to Menu", type="primary", use_container_width=True):
            st.session_state.quiz_active = False
            st.rerun()


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Ancient Civilizations Review",
        page_icon="🏛️",
        layout="centered",
    )

    # Custom CSS
    st.markdown("""
    <style>
        .stButton > button {
            text-align: left;
            padding: 0.75rem 1rem;
        }
        div[data-testid="stMarkdownContainer"] strong {
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    init_session_state()

    # Route to correct page
    if not st.session_state.player_name:
        page_login()
    elif st.session_state.quiz_active:
        page_quiz()
    else:
        page_menu()


if __name__ == "__main__":
    main()