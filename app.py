#!/usr/bin/env python3
"""
Universal Review App
A flexible Streamlit app that generates quizzes based on a folder structure.
Structure: subjects/ [Subject Name] / [Chapter].json
"""

import json
import random
import os
import streamlit as st
from supabase import create_client, Client

# ─── Config ───────────────────────────────────────────────────────────────────

def _get_secret(key, default=""):
    try:
        return st.secrets[key]
    except (KeyError, AttributeError):
        return os.environ.get(key, default)

SUPABASE_URL = _get_secret("SUPABASE_URL", "")
SUPABASE_KEY = _get_secret("SUPABASE_KEY", "")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# We now look in a 'subjects' folder instead of hardcoded filenames
SUBJECTS_DIR = os.path.join(SCRIPT_DIR, "subjects")

OLLAMA_URL = _get_secret("OLLAMA_URL", "")
OLLAMA_MODEL = _get_secret("OLLAMA_MODEL", "")
OLLAMA_API_KEY = _get_secret("OLLAMA_API_KEY", "")

# ─── Dynamic Content Loading ──────────────────────────────────────────────────

def get_all_subjects():
    """Returns a list of folders inside the subjects directory."""
    if not os.path.exists(SUBJECTS_DIR):
        os.makedirs(SUBJECTS_DIR, exist_ok=True)
        return []
    # Return only directories
    return [d for d in os.listdir(SUBJECTS_DIR) if os.path.isdir(os.path.join(SUBJECTS_DIR, d))]

def get_chapters_for_subject(subject):
    """Returns a list of JSON files inside a subject folder."""
    subj_path = os.path.join(SUBJECTS_DIR, subject)
    if not os.path.exists(subj_path):
        return []
    # Return all .json files, removing the .json extension for display
    return [f[:-5] for f in os.listdir(subj_path) if f.endswith(".json")]

def load_questions_from_file(subject, chapter):
    """Loads a specific JSON file from subjects/subject/chapter.json"""
    path = os.path.join(SUBJECTS_DIR, subject, f"{chapter}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_all_questions_for_subject(subject):
    """Loads all JSON files within a subject folder."""
    questions = []
    subj_path = os.path.join(SUBJECTS_DIR, subject)
    for f in os.listdir(subj_path):
        if f.endswith(".json"):
            with open(os.path.join(subj_path, f), "r", encoding="utf-8") as file:
                questions.extend(json.load(file))
    return questions

# ─── Core Logic (Shuffling & DB) ────────────────────────────────────────────────

def shuffle_choices(question: dict) -> dict:
    choices = question["choices"][:]
    correct_text = choices[question["answer"]]
    random.shuffle(choices)
    new_answer = choices.index(correct_text)
    return {**question, "choices": choices, "answer": new_answer}

def get_supabase() -> Client:
    if not SUPABASE_KEY: return None
    try: return create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return None

def get_or_create_player(supabase, name):
    if not supabase or not name.strip(): return None
    try:
        result = supabase.table("players").select("*").eq("name", name.strip()[:50]).execute()
        if result.data: return result.data[0]
        result = supabase.table("players").insert({"name": name.strip()[:50]}).execute()
        return result.data[0] if result.data else None
    except: return None

def record_answer(supabase, player_id, term, subject, category, correct, streak):
    if not supabase: return
    try:
        supabase.table("scores").insert({
            "player_id": player_id, "question_term": term, 
            "subject": subject, "category": category, 
            "correct": correct, "streak": streak
        }).execute()
    except: pass

def update_player_streak(supabase, player_id, current_streak, best_streak):
    if not supabase: return
    try:
        supabase.table("players").update({"current_streak": current_streak, "best_streak": best_streak}).eq("id", player_id).execute()
    except: pass

# ─── Session State ────────────────────────────────────────────────────────────

def init_session_state():
    defaults = {
        "player_name": "", "player_id": None, "current_questions": [],
        "current_index": 0, "current_streak": 0, "best_streak": 0,
        "session_correct": 0, "session_total": 0, "session_missed": [],
        "quiz_active": False, "quiz_title": "", "category_label": "",
        "answered_current": False, "selected_answer": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state: st.session_state[key] = val

# ─── UI Pages ──────────────────────────────────────────────────────────────────

def page_login():
    st.markdown("<div style='text-align: center;'><h1>📚 Universal Review App</h1><p>Customizable study sets for any subject</p></div>", unsafe_allow_html=True)
    st.markdown("---")
    name = st.text_input("Enter your name to track progress:", placeholder="Your name...")
    if st.button("🚀 Start Learning", type="primary", use_container_width=True, disabled=not name.strip()):
        supabase = get_supabase()
        if supabase:
            player = get_or_create_player(supabase, name)
            if player:
                st.session_state.player_name = name.strip()
                st.session_state.player_id = player["id"]
                st.session_state.current_streak = player.get("current_streak", 0)
                st.session_state.best_streak = player.get("best_streak", 0)
            else:
                st.session_state.player_name = name.strip()
                st.session_state.player_id = None
        else:
            st.session_state.player_name = name.strip()
            st.session_state.player_id = None
        st.rerun()

def page_menu():
    st.markdown(f"<div style='text-align: center;'><h1>Welcome, {st.session_state.player_name}!</h1></div>", unsafe_allow_html=True)
    
    subjects = get_all_subjects()
    if not subjects:
        st.info("No subjects found. Create a folder in the `subjects/` directory to start!")
        return

    st.markdown("### 📂 Choose a Subject")
    for subject in subjects:
        with st.expander(f"📘 {subject}"):
            chapters = get_chapters_for_subject(subject)
            if not chapters:
                st.write("No chapters found in this subject.")
                continue
            
            # Quiz this subject's full content
            if st.button(f"🎲 Random Mix: {subject}", key=f"mix_{subject}"):
                all_qs = load_all_questions_for_subject(subject)
                start_quiz(all_qs, f"{subject} (Mixed)", "General")
                st.rerun()
            
            st.markdown("**Select a Chapter:**")
            for ch in chapters:
                if st.button(f"📖 {ch}", key=f"ch_{subject}_{ch}"):
                    ch_qs = load_questions_from_file(subject, ch)
                    start_quiz(ch_qs, f"{subject} - {ch}", ch)
                    st.rerun()

    if st.button("🚪 Log Out", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

def start_quiz(questions, title, category):
    shuffled = [shuffle_choices(q) for q in questions]
    st.session_state.current_questions = shuffled
    st.session_state.current_index = 0
    st.session_state.session_correct = 0
    st.session_state.session_total = 0
    st.session_state.session_missed = []
    st.session_state.quiz_active = True
    st.session_state.quiz_title = title
    st.session_state.category_label = category
    st.session_state.answered_current = False
    st.session_state.selected_answer = None

def page_quiz():
    questions = st.session_state.current_questions
    idx = st.session_state.current_index
    if idx >= len(questions):
        # Results page
        correct = st.session_state.session_correct
        total = st.session_state.session_total
        pct = (correct/total*100) if total else 0
        st.markdown(f"## 🎉 Quiz Complete! {pct:.0f}% ({correct}/{total})")
        if st.button("Back to Menu", use_container_width=True):
            st.session_state.quiz_active = False
            st.rerun()
        return

    q = questions[idx]
    st.progress(idx / len(questions))
    st.markdown(f"### {q['question']}")
    
    labels = ["A", "B", "C", "D"]
    if not st.session_state.answered_current:
        for i, choice in enumerate(q["choices"]):
            if st.button(f"{labels[i]}) {choice}", key=f"opt_{i}", use_container_width=True):
                st.session_state.selected_answer = i
                st.session_state.answered_current = True
                correct = (i == q["answer"])
                st.session_state.session_total += 1
                if correct:
                    st.session_state.session_correct += 1
                    st.session_state.current_streak += 1
                    st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.current_streak)
                else:
                    st.session_state.current_streak = 0
                    st.session_state.session_missed.append(q)
                
                # DB record
                supabase = get_supabase()
                if supabase and st.session_state.player_id:
                    record_answer(supabase, st.session_state.player_id, q['term'], st.session_state.quiz_title, st.session_state.category_label, correct, st.session_state.current_streak)
                    update_player_streak(supabase, st.session_state.player_id, st.session_state.current_streak, st.session_state.best_streak)
                st.rerun()
    else:
        # Show answer
        sel = st.session_state.selected_answer
        correct = (sel == q["answer"])
        for i, choice in enumerate(q["choices"]):
            if i == q["answer"]: st.markdown(f"✅ **{labels[i]}) {choice}**")
            elif i == sel and not correct: st.markdown(f"❌ ~~{labels[i]}) {choice}~~")
            else: st.markdown(f"{labels[i]}) {choice}")
        
        if correct: st.success("Correct!")
        else: st.error(f"Incorrect. Answer is {labels[q['answer']]}")
        
        if st.button("➡️ Next Question", use_container_width=True):
            st.session_state.current_index += 1
            st.session_state.answered_current = False
            st.rerun()

def main():
    st.set_page_config(page_title="Universal Review App", page_icon="📚")
    init_session_state()
    if not st.session_state.player_name: page_login()
    elif st.session_state.quiz_active: page_quiz()
    else: page_menu()

if __name__ == "__main__":
    main()
