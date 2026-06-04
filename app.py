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

SA_QUESTIONS_FILE = "short_answer_questions.json"

OLLAMA_URL = _get_secret("OLLAMA_URL", "https://navigation-vid-rely-institutes.trycloudflare.com")
OLLAMA_MODEL = _get_secret("OLLAMA_MODEL", "glm-5.1:cloud")
OLLAMA_API_KEY = _get_secret("OLLAMA_API_KEY", "")


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


# ─── Shuffle choices ───────────────────────────────────────────────────────────

def shuffle_choices(question: dict) -> dict:
    """Return a copy of the question with shuffled choices and updated answer index."""
    choices = question["choices"][:]
    correct_text = choices[question["answer"]]
    random.shuffle(choices)
    new_answer = choices.index(correct_text)
    return {
        **question,
        "choices": choices,
        "answer": new_answer,
    }


# ─── Supabase ─────────────────────────────────────────────────────────────────

def get_supabase() -> Client:
    if not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


def get_or_create_player(supabase: Client, name: str) -> dict | None:
    """Get existing player or create new one. Returns player dict with id and streaks."""
    if not supabase or not name.strip():
        return None
    name = name.strip()[:50]

    try:
        result = supabase.table("ancient_civ_players").select("*").eq("name", name).execute()
        if result.data:
            return result.data[0]

        result = supabase.table("ancient_civ_players").insert({"name": name}).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None


def update_player_streak(supabase: Client, player_id: int, current_streak: int, best_streak: int):
    """Update player's streaks in the database."""
    if not supabase:
        return
    try:
        supabase.table("ancient_civ_players").update({
            "current_streak": current_streak,
            "best_streak": best_streak,
        }).eq("id", player_id).execute()
    except Exception:
        pass


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
        pass


def get_leaderboard(supabase: Client, limit: int = 20) -> list:
    """Get top players by best streak and total correct."""
    if not supabase:
        return []
    try:
        # Use the leaderboard view if available, otherwise fall back
        result = supabase.table("ancient_civ_players").select("id, name, best_streak, current_streak").order("best_streak", desc=True).limit(limit).execute()
        if not result.data:
            return []

        players = []
        for p in result.data:
            # Get score counts
            scores = supabase.table("ancient_civ_scores").select("correct").eq("player_id", p["id"]).execute()
            total = len(scores.data) if scores.data else 0
            correct = sum(1 for s in (scores.data or []) if s.get("correct"))

            players.append({
                "name": p["name"],
                "correct": correct,
                "total": total,
                "best_streak": p.get("best_streak", 0),
                "current_streak": p.get("current_streak", 0),
            })

        players.sort(key=lambda p: (-p["best_streak"], -p["correct"]))
        return players[:limit]
    except Exception:
        return []


def get_player_stats(supabase: Client, player_id: int) -> dict:
    """Get stats for a specific player."""
    if not supabase:
        return {}
    try:
        result = supabase.table("ancient_civ_scores").select("correct, streak, chapter, category").eq("player_id", player_id).execute()
        if not result.data:
            return {"total": 0, "correct": 0, "best_streak": 0, "current_streak": 0, "chapters": {}, "categories": {}}

        stats = {"total": 0, "correct": 0, "best_streak": 0, "current_streak": 0, "chapters": {}, "categories": {}}
        for row in result.data:
            stats["total"] += 1
            if row["correct"]:
                stats["correct"] += 1
            stats["best_streak"] = max(stats["best_streak"], row.get("streak", 0))
            stats["current_streak"] = max(stats["current_streak"], row.get("streak", 0))

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

        # Override with player table streaks (authoritative)
        player = supabase.table("ancient_civ_players").select("current_streak, best_streak").eq("id", player_id).execute()
        if player.data:
            stats["current_streak"] = player.data[0].get("current_streak", 0)
            stats["best_streak"] = player.data[0].get("best_streak", 0)

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
        "sa_active": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─── Quiz Logic ────────────────────────────────────────────────────────────────

def get_answered_questions(supabase: Client, player_id: int) -> dict:
    """Get sets of question terms the player has answered correctly and incorrectly."""
    if not supabase or not player_id:
        return {"correct": set(), "incorrect": set(), "all": set()}
    try:
        result = supabase.table("ancient_civ_scores").select("question_term, correct").eq("player_id", player_id).execute()
        correct_terms = set()
        incorrect_terms = set()
        for row in (result.data or []):
            if row.get("correct"):
                correct_terms.add(row["question_term"])
            else:
                incorrect_terms.add(row["question_term"])
        return {"correct": correct_terms, "incorrect": incorrect_terms, "all": correct_terms | incorrect_terms}
    except Exception:
        return {"correct": set(), "incorrect": set(), "all": set()}


def prioritize_questions(all_questions: list, player_id: int, count: int) -> list:
    """Prioritize unanswered, then missed, then correct. Returns up to `count` questions."""
    supabase = get_supabase()
    if supabase and player_id:
        answered = get_answered_questions(supabase, player_id)

        untried = [q for q in all_questions if q["term"] not in answered["all"]]
        missed = [q for q in all_questions if q["term"] in answered["incorrect"] and q["term"] not in answered["correct"]]
        mastered = [q for q in all_questions if q["term"] in answered["correct"] and q["term"] not in answered["incorrect"]]
        # Questions that were answered both correctly and incorrectly — prioritize as missed
        mixed = [q for q in all_questions if q["term"] in answered["correct"] and q["term"] in answered["incorrect"]]

        random.shuffle(untried)
        random.shuffle(missed)
        random.shuffle(mixed)
        random.shuffle(mastered)

        # Priority: untried > missed > mixed > mastered
        prioritized = untried + missed + mixed + mastered
    else:
        # No database — just shuffle
        prioritized = all_questions[:]
        random.shuffle(prioritized)

    return prioritized[:count]


def start_quiz(questions: list, title: str, category_label: str = ""):
    """Initialize a new quiz session."""
    # Prioritize untried/missed questions
    count = len(questions)
    prioritized = prioritize_questions(questions, st.session_state.player_id, count)

    # Shuffle question order AND shuffle each question's choices
    shuffled_qs = [shuffle_choices(q) for q in prioritized]

    supabase = get_supabase()
    db_streak = 0
    db_best = 0
    if supabase and st.session_state.player_id:
        player = get_or_create_player(supabase, st.session_state.player_name)
        if player:
            db_streak = player.get("current_streak", 0)
            db_best = player.get("best_streak", 0)

    st.session_state.current_questions = shuffled_qs
    st.session_state.current_index = 0
    st.session_state.current_streak = db_streak  # Resume from database
    st.session_state.best_streak = db_best
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
                    st.session_state.current_streak = player.get("current_streak", 0)
                    st.session_state.best_streak = player.get("best_streak", 0)
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
            streak_emoji = "🔥" if stats.get("current_streak", 0) > 0 else ""
            st.markdown(f"""
            <div style='display: flex; justify-content: center; gap: 2rem; padding: 0.5rem 0;'>
                <span>📊 <strong>{stats['total']}</strong> questions</span>
                <span>✅ <strong>{pct:.0f}%</strong> correct</span>
                <span>{streak_emoji} <strong>{stats.get('current_streak', 0)}</strong> active streak</span>
                <span>🏆 <strong>{stats.get('best_streak', 0)}</strong> best streak</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")

        # Progress overview
        answered = get_answered_questions(supabase, st.session_state.player_id)
        total_qs = len(all_questions)
        tried = len(answered["all"])
        st.markdown(f"**Overall progress:** {tried}/{total_qs} questions tried")
        # Per-chapter breakdown table
        prog_rows = []
        for chapter in CHAPTERS:
            ch_qs = [q for q in all_questions if q["chapter"] == chapter]
            ch_total = len(ch_qs)
            ch_terms = {q["term"] for q in ch_qs}
            ch_tried = len(ch_terms & answered["all"])
            prog_rows.append({"Chapter": chapter, "Tried": f"{ch_tried}/{ch_total}", "Remaining": ch_total - ch_tried})
        st.table(prog_rows)
    else:
        # No DB – just show generic stats if any
        if st.session_state.player_id:
            # fallback if stats still available
            pass

    # Quick start - random mix
    st.markdown("### 🎲 Quick Start")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔀 10 Random Questions", use_container_width=True):
            sample = prioritize_questions(all_questions, st.session_state.player_id, 10)
            if len(sample) < 5:  # fallback if too few prioritized
                sample = random.sample(all_questions, min(10, len(all_questions)))
            start_quiz(sample, "10 Random Questions", "Mixed")
            st.rerun()
    with col2:
        if st.button("🔀 20 Random Questions", use_container_width=True):
            sample = prioritize_questions(all_questions, st.session_state.player_id, 20)
            if len(sample) < 5:
                sample = random.sample(all_questions, min(20, len(all_questions)))
            start_quiz(sample, "20 Random Questions", "Mixed")
            st.rerun()

    st.markdown("---")

    # Review by Chapter
    st.markdown("### 📖 Review by Chapter")
    chapter_cols = st.columns(2)
    for i, chapter in enumerate(CHAPTERS):
        ch_questions = [q for q in all_questions if q["chapter"] == chapter]
        ch_prioritized = prioritize_questions(ch_questions, st.session_state.player_id, len(ch_questions))
        with chapter_cols[i % 2]:
            if st.button(f"{chapter} ({len(ch_questions)})", key=f"ch_{i}", use_container_width=True):
                start_quiz(ch_prioritized, chapter, chapter)
                st.rerun()

    st.markdown("---")

    # Review by Category
    st.markdown("### 📝 Review by Category")
    cat_cols = st.columns(3)
    for i, cat in enumerate(CATEGORIES):
        cat_path = os.path.join(SCRIPT_DIR, cat["file"])
        if os.path.exists(cat_path):
            with open(cat_path, "r", encoding="utf-8") as f:
                cat_qs = json.load(f)
        else:
            cat_qs = []
        with cat_cols[i]:
            if st.button(f"{cat['icon']} {cat['name']} ({len(cat_qs)})", key=f"cat_{i}", use_container_width=True):
                cat_prioritized = prioritize_questions(cat_qs, st.session_state.player_id, len(cat_qs))
                start_quiz(cat_prioritized, cat["name"], cat["name"])
                st.rerun()

    st.markdown("---")

    # Short Answer Practice
    st.markdown("### ✍️ Short Answer Practice")
    st.markdown("Practice writing short answers and get instant feedback on your writing!")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✍️ Start Short Answer Practice", use_container_width=True, type="primary"):
            st.session_state.sa_active = True
            st.rerun()
    with col2:
        st.caption("6 questions • Real-time AI feedback • 4-point scoring")

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
                current = player.get("current_streak", 0)
                best = player.get("best_streak", 0)
                streak_info = f"🔥 {best} best" if best > 0 else ""
                if current > 0:
                    streak_info = f"🔥 {current} active ({best} best)"
                st.markdown(
                    f"<span style='{highlight}'>{rank_emoji} <strong>{player['name']}</strong> — "
                    f"{streak_info} • ✅ {player['correct']}/{player['total']} ({pct:.0f}%)</span>",
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

    # Header with streak
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
    if st.session_state.current_streak >= 20:
        st.markdown("🌟 **LEGENDARY! 20+ streak!!** 🌟")
    if st.session_stats.current_streak >= 30:
        st.markdown("💥 **EPIC! 30+ streak!!**")
    if st.session_sstats.current_streak >= 50:
        st.markdown("💫 **GODLY! 50+ streak!!**")

    st.markdown("---")

    # Question
    st.markdown(f"### {q['question']}")
    if st.session_state.category_label and st.session_state.category_label not in ("Mixed", "Missed", q.get("chapter", "")):
        st.caption(f"📖 {q['chapter']} • {st.session_state.category_label}")
    else:
        st.caption(f"📖 {q['chapter']}")

    # Answer choices (already shuffled by shuffle_choices)
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
                    # Update player's persistent streak
                    update_player_streak(
                        supabase, st.session_state.player_id,
                        st.session_state.current_streak, st.session_state.best_streak
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
        st.markdown(f"<div style='text-align: center;'><p>🔥 Best streak this session: <strong>{st.session_state.best_streak}</strong> in a row!</p></div>", unsafe_allow_html=True)

    # Overall persistent streak
    supabase = get_supabase()
    if supabase and st.session_state.player_id:
        player = get_or_create_player(supabase, st.session_state.player_name)
        if player and player.get("current_streak", 0) > 0:
            st.markdown(f"<div style='text-align: center;'><p>🔥 Active streak across all sessions: <strong>{player['current_streak']}</strong></p></div>", unsafe_allow_html=True)

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


# ─── Short Answer ──────────────────────────────────────────────────────────────

@st.cache_data
def load_sa_questions():
    qpath = os.path.join(SCRIPT_DIR, SA_QUESTIONS_FILE)
    if os.path.exists(qpath):
        with open(qpath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def grade_short_answer(question: dict, student_answer: str) -> dict:
    """Send student answer to Ollama for grading."""
    prompt = f"""You are a kind but fair middle school history teacher grading a short answer question. You teach 6th graders, many of whom are ESL students learning in English.

Question: {question['question']}
Key points expected in a full answer: {chr(10).join('- ' + p for p in question['key_points'])}
Max points: {question['max_points']}

Student's answer: {student_answer}

Grade this answer using these standards:
- 1 point: Shows some knowledge of the topic, even if partially wrong or incomplete
- 2 points: Correct but lacks crucial support; or multiple correct facts without correct connections; or only answered one part of a multi-part question
- 3 points: Correct except for a single missing fact or minor misinterpretation; for multi-part questions, missing a minor part
- 4 points: Correctly answers the question with correct reason or example. Answers ALL parts of the question.

Important grading notes:
- Do NOT take points off for grammar unless it makes the answer impossible to understand
- Be lenient with ESL students — focus on content knowledge, not English perfection
- If a student shows they understand the concept but use wrong names/dates, give partial credit
- If a student is on the right track but incomplete, encourage them and tell them what to add

Respond in this exact JSON format:
{{"score": <number 1-4>, "feedback": "<2-3 sentences of encouraging feedback>", "what_was_good": "<what they got right>", "what_to_add": "<specific points they missed to get full credit>"}}"""

    try:
        import urllib.request
        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 512}
        }).encode()
        url = OLLAMA_URL.rstrip("/") + "/api/generate"
        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
        req = urllib.request.Request(url, data=payload, headers=headers)
        # Try the request with detailed error reporting
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode()
                if not body.strip():
                    return {"score": 0, "feedback": "Error: AI grader returned empty response. This usually means the grading server is temporarily down. Please try again in a minute.", "what_was_good": "", "what_to_add": ""}
                result = json.loads(body)
                # Check for Ollama error response
                if "error" in result:
                    return {"score": 0, "feedback": f"Error from AI: {result['error']}", "what_was_good": "", "what_to_add": ""}
                text = result.get("response", "").strip()
                st.session_state["debug_raw_response"] = text[:500] if text else "(empty)"
        except urllib.error.HTTPError as he:
            err_body = he.read().decode()[:200] if he.fp else "no details"
            return {"score": 0, "feedback": f"Error: AI grader returned HTTP {he.code}. {err_body}", "what_was_good": "", "what_to_add": ""}
        except urllib.error.URLError as ue:
            return {"score": 0, "feedback": f"Error: Cannot reach AI grader at {url}. Reason: {ue.reason}. The grading server may be offline or blocked.", "what_was_good": "", "what_to_add": ""}
        except Exception as net_err:
            return {"score": 0, "feedback": f"Error: Network issue — {type(net_err).__name__}: {net_err}. Try submitting again.", "what_was_good": "", "what_to_add": ""}
        # Parse JSON from response
        import re
        text = re.sub(r'^```json\\s*', '', text)
        text = re.sub(r'^```\\s*', '', text)
        text = re.sub(r'\\s*```$', '', text)
        brace_start = text.find('{')
        brace_end = text.rfind('}')
        if brace_start != -1 and brace_end != -1:
            return json.loads(text[brace_start:brace_end+1])
        return json.loads(text)
    except Exception as e:
        return {"score": 0, "feedback": f"Error grading: {e}", "what_was_good": "", "what_to_add": ""}


def page_short_answer():
    """Short answer practice page with LLM grading."""
    sa_questions = load_sa_questions()

    if not sa_questions:
        st.error("No short answer questions found!")
        return

    # Connectivity test for AI grader
    with st.expander("🔧 AI Grader Status"):
        if st.button("Test Connection"):
            import urllib.request
            url = OLLAMA_URL.rstrip("/") + "/api/tags"
            try:
                headers = {"Content-Type": "application/json"}

                if OLLAMA_API_KEY:
                    headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                    models = [m["name"] for m in data.get("models", [])]
                    st.success(f"✅ Connected! Available models: {', '.join(models) if models else 'none listed'}")
            except urllib.error.HTTPError as he:
                st.error(f"❌ HTTP {he.code}: {he.read().decode()[:200]}")
            except urllib.error.URLError as ue:
                st.error(f"❌ Cannot reach {url}\nReason: {ue.reason}")
            except Exception as e:
                st.error(f"❌ {type(e).__name__}: {e}")

    # Show last raw response for debugging
    if "debug_raw_response" in st.session_state:
        st.caption(f"Last AI response (first 500 chars): {st.session_state['debug_raw_response']}")

        # Initialize SA session state
    if "sa_index" not in st.session_state:
        # Mix real and practice questions, shuffle
        real = [q for q in sa_questions if q["source"] == "real"]
        practice = [q for q in sa_questions if q["source"] == "practice"]
        # Pick 2-3 real + 2-3 practice
        selected_real = random.sample(real, min(3, len(real)))
        selected_practice = random.sample(practice, min(3, len(practice)))
        selected = selected_real + selected_practice
        random.shuffle(selected)
        st.session_state.sa_questions = selected
        st.session_state.sa_index = 0
        st.session_state.sa_answers = {}
        st.session_state.sa_graded = {}
        st.session_state.sa_total_score = 0
        st.session_state.sa_max_score = sum(q["max_points"] for q in selected)

    questions = st.session_state.sa_questions
    idx = st.session_state.sa_index
    total = len(questions)

    if idx >= total:
        # Show results
        total_score = st.session_state.sa_total_score
        max_score = st.session_state.sa_max_score
        pct = (total_score / max_score * 100) if max_score > 0 else 0

        if pct >= 90:
            emoji, message = "🏆", "Outstanding! You're ready for the short answer section!"
        elif pct >= 75:
            emoji, message = "🎉", "Great job! Almost there — review the points you missed."
        elif pct >= 50:
            emoji, message = "💪", "Good effort! Review the feedback and try again."
        else:
            emoji, message = "📚", "Keep studying — you'll get there! Review your notes and try again."

        st.markdown(f"""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1>{emoji} Short Answer Complete!</h1>
            <h2>{total_score} / {max_score} points ({pct:.0f}%)</h2>
            <p style='font-size: 1.1rem; color: #888;'>{message}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📝 Your Answers & Feedback")
        for i, q in enumerate(questions):
            graded = st.session_state.sa_graded.get(q["id"], {})
            answer = st.session_state.sa_answers.get(q["id"], "")
            source_tag = "🔴 Real Test Question" if q["source"] == "real" else "🟡 Practice Question"
            score = graded.get("score", 0)
            max_pts = q["max_points"]

            score_color = "green" if score >= 3 else ("orange" if score >= 2 else "red")
            st.markdown(f"""
            **Q{i+1}.** {q["question"]}  
            <span style='color: gray; font-size: 0.85rem;'>{source_tag}</span>
            """, unsafe_allow_html=True)
            st.markdown(f"Your answer: *{answer}*")
            st.markdown(f"<span style='color: {score_color}; font-weight: bold;'>Score: {score}/{max_pts}</span>", unsafe_allow_html=True)
            if graded.get("what_was_good"):
                st.markdown(f"✅ **What you got right:** {graded['what_was_good']}")
            if graded.get("what_to_add"):
                st.markdown(f"📝 **To get full credit, add:** {graded['what_to_add']}")
            if graded.get("feedback"):
                st.markdown(f"💬 {graded['feedback']}")
            st.markdown("")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try Again (New Questions)", use_container_width=True):
                del st.session_state.sa_index
                st.rerun()
        with col2:
            if st.button("🏠 Back to Menu", use_container_width=True):
                st.session_state.sa_active = False
                del st.session_state.sa_index
                st.rerun()
        return

    # Current question
    q = questions[idx]
    source_tag = "🔴 Real Test Question" if q["source"] == "real" else "🟡 Practice Question"
    progress = idx / total

    st.progress(progress)
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <span><strong>Short Answer Practice</strong> • Q{idx+1}/{total}</span>
        <span>Score: {st.session_state.sa_total_score}/{st.session_state.sa_max_score}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Question
    st.markdown(f"### {q['question']}")
    st.markdown(f"<span style='color: gray; font-size: 0.85rem;'>{source_tag} • {q['chapter']} • {q['max_points']} points</span>", unsafe_allow_html=True)

    # Answer input
    answer_key = f"sa_answer_{q['id']}"
    submitted_key = f"sa_submitted_{q['id']}"

    if submitted_key not in st.session_state:
        st.session_state[submitted_key] = False

    if not st.session_state[submitted_key]:
        # Show input
        user_answer = st.text_area(
            "Write your answer in complete sentences. Answer ALL parts of the question.",
            key=answer_key,
            height=120,
            placeholder=f"Type your answer here... (1-3 sentences)"
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✅ Submit Answer", type="primary", use_container_width=True, disabled=not user_answer.strip()):
                if user_answer.strip():
                    st.session_state.sa_answers[q["id"]] = user_answer.strip()
                    st.session_state[submitted_key] = True

                    # Grade with LLM
                    with st.spinner("🤔 Grading your answer..."):
                        graded = grade_short_answer(q, user_answer.strip())
                    # Debug: show raw grading result if it errored
                    if graded.get("score", -1) == 0 and "Error" in graded.get("feedback", ""):
                        st.warning(f"Debug info: {graded}")
                    st.session_state.sa_graded[q["id"]] = graded
                    st.session_state.sa_total_score += graded.get("score", 0)

                    st.rerun()
    else:
        # Show feedback
        graded = st.session_state.sa_graded.get(q["id"], {})
        answer = st.session_state.sa_answers.get(q["id"], "")
        score = graded.get("score", 0)
        max_pts = q["max_points"]

        score_color = "green" if score >= 3 else ("orange" if score >= 2 else "red")

        st.markdown(f"Your answer: *{answer}*")
        st.markdown(f"<span style='color: {score_color}; font-weight: bold; font-size: 1.2rem;'>Score: {score}/{max_pts} points</span>", unsafe_allow_html=True)

        if graded.get("what_was_good"):
            st.success(f"✅ **What you got right:** {graded['what_was_good']}")
        if graded.get("what_to_add"):
            st.warning(f"📝 **To get full credit, add:** {graded['what_to_add']}")
        if graded.get("feedback"):
            st.info(f"💬 {graded['feedback']}")

        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("➡️ Next Question", type="primary", use_container_width=True):
                st.session_state.sa_index += 1
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
    elif st.session_state.sa_active:
        page_short_answer()
    elif st.session_state.quiz_active:
        page_quiz()
    else:
        page_menu()


if __name__ == "__main__":
    main()
