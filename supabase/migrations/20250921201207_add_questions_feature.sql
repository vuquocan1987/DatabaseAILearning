-- =========================
-- Minimal Working Question Bank
-- =========================

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS ltree;

-- Topics with tree structure
CREATE TABLE topics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT GENERATED ALWAYS AS (regexp_replace(lower(trim(name)), '\s+', '-', 'g')) STORED,
  parent_id UUID REFERENCES topics(id) ON DELETE CASCADE,
  path LTREE,
  description TEXT,
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(slug)
);

-- Index for efficient tree queries
CREATE INDEX idx_topics_path ON topics USING GIST (path);
CREATE INDEX idx_topics_parent ON topics (parent_id);

-- Auto-maintain ltree path
CREATE OR REPLACE FUNCTION maintain_topic_path() 
RETURNS TRIGGER AS $$
DECLARE
  parent_path LTREE;
BEGIN
  IF NEW.parent_id IS NULL THEN
    NEW.path := text2ltree(NEW.slug);
  ELSE
    SELECT path INTO parent_path FROM topics WHERE id = NEW.parent_id;
    IF parent_path IS NULL THEN
      RAISE EXCEPTION 'Parent topic not found';
    END IF;
    NEW.path := parent_path || text2ltree(NEW.slug);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER topic_path_trigger
  BEFORE INSERT OR UPDATE OF parent_id, name ON topics
  FOR EACH ROW EXECUTE FUNCTION maintain_topic_path();

-- Questions
CREATE TABLE questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id UUID REFERENCES topics(id),
  question_text TEXT NOT NULL,
  explanation TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Answer choices
CREATE TABLE choices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
  choice_text TEXT NOT NULL,
  is_correct BOOLEAN DEFAULT false,
  sort_order INTEGER DEFAULT 0
);

-- User attempts (simple tracking)
CREATE TABLE user_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT, -- Just use email or username for now
  topic_id UUID REFERENCES topics(id),
  started_at TIMESTAMPTZ DEFAULT NOW()
);

-- User answers
CREATE TABLE user_answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES user_sessions(id),
  question_id UUID REFERENCES questions(id),
  choice_id UUID REFERENCES choices(id),
  is_correct BOOLEAN,
  answered_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_questions_topic ON questions(topic_id);
CREATE INDEX idx_choices_question ON choices(question_id, sort_order);
CREATE INDEX idx_answers_session ON user_answers(session_id);
