-- Ancient Civilizations Review — Supabase Tables
-- Run this in the Supabase SQL Editor (Syntaxiom Edu project)
-- These tables are completely separate from the vocabulary app tables

-- Players table (no auth needed — just names)
CREATE TABLE IF NOT EXISTS ancient_civ_players (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    current_streak INTEGER NOT NULL DEFAULT 0,
    best_streak INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scores table (every answer is recorded)
CREATE TABLE IF NOT EXISTS ancient_civ_scores (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    player_id BIGINT NOT NULL REFERENCES ancient_civ_players(id) ON DELETE CASCADE,
    question_term TEXT NOT NULL,
    chapter TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    correct BOOLEAN NOT NULL,
    streak INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for leaderboard queries
CREATE INDEX IF NOT EXISTS idx_scores_player ON ancient_civ_scores(player_id);
CREATE INDEX IF NOT EXISTS idx_scores_streak ON ancient_civ_scores(streak DESC);
CREATE INDEX IF NOT EXISTS idx_scores_correct ON ancient_civ_scores(correct);
CREATE INDEX IF NOT EXISTS idx_scores_player_correct ON ancient_civ_scores(player_id, correct);

-- RLS policies (allow anonymous reads/writes — this is a public review app)
ALTER TABLE ancient_civ_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE ancient_civ_scores ENABLE ROW LEVEL SECURITY;

-- Anyone can read and write (this is intentionally public — no sensitive data)
CREATE POLICY "Anyone can read players" ON ancient_civ_players FOR SELECT USING (true);
CREATE POLICY "Anyone can insert players" ON ancient_civ_players FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can read scores" ON ancient_civ_scores FOR SELECT USING (true);
CREATE POLICY "Anyone can insert scores" ON ancient_civ_scores FOR INSERT WITH CHECK (true);

-- GRANT table-level permissions to anon role (required even with RLS policies)
GRANT SELECT, INSERT, UPDATE ON TABLE ancient_civ_players TO anon;
GRANT SELECT, INSERT ON TABLE ancient_civ_scores TO anon;
GRANT SELECT ON TABLE ancient_civ_leaderboard TO anon;

-- Leaderboard view (pre-aggregated)
CREATE OR REPLACE VIEW ancient_civ_leaderboard AS
SELECT
    p.id AS player_id,
    p.name,
    COUNT(*) AS total_answers,
    COUNT(*) FILTER (WHERE s.correct) AS total_correct,
    ROUND(COUNT(*) FILTER (WHERE s.correct)::DECIMAL / NULLIF(COUNT(*), 0) * 100, 1) AS accuracy,
    MAX(s.streak) AS best_streak
FROM ancient_civ_players p
JOIN ancient_civ_scores s ON s.player_id = p.id
GROUP BY p.id, p.name
ORDER BY best_streak DESC, total_correct DESC;