-- =========================
-- Simplified Question Bank Database Schema
-- =========================

-- Drop existing tables if they exist (in dependency order)
DROP TABLE IF EXISTS user_answers CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS correct_answers CASCADE;
DROP TABLE IF EXISTS choices CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS topics CASCADE;

-- Drop existing types and extensions
DROP TYPE IF EXISTS question_type CASCADE;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS ltree;

-- Enable RLS globally
ALTER DATABASE postgres SET row_security = on;

-- =========================
-- ENUMS AND TYPES
-- =========================

CREATE TYPE question_type AS ENUM (
  'multiple_choice',
  'single_choice', 
  'true_false',
  'short_answer',
  'fill_in_blank',
  'essay',
  'matching',
  'ordering'
);

CREATE OR REPLACE FUNCTION generate_slug(topic_name TEXT) 
RETURNS TEXT AS $$
BEGIN
  RETURN regexp_replace(lower(trim(topic_name)), '\s+', '-', 'g');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =========================
-- CORE TABLES
-- =========================

-- Topics with hierarchical structure (no metadata)
CREATE TABLE topics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT GENERATED ALWAYS AS (generate_slug(name)) STORED,
  description TEXT,
  parent_id UUID REFERENCES topics(id) ON DELETE CASCADE,
  path LTREE,
  sort_order INTEGER DEFAULT 0,
  created_by UUID REFERENCES auth.users(id) DEFAULT auth.uid(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(slug)
);

-- Questions (no metadata)
CREATE TABLE questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
  question_text TEXT NOT NULL,
  question_type question_type NOT NULL DEFAULT 'multiple_choice',
  explanation TEXT,
  points INTEGER DEFAULT 1 CHECK (points > 0),
  difficulty_level INTEGER DEFAULT 1 CHECK (difficulty_level BETWEEN 1 AND 5),
  created_by UUID REFERENCES auth.users(id) DEFAULT auth.uid(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Answer choices for multiple choice, true/false, matching questions (no metadata)
CREATE TABLE choices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
  choice_text TEXT NOT NULL,
  is_correct BOOLEAN DEFAULT false,
  sort_order INTEGER DEFAULT 0
);

-- Correct answers for short answer, fill-in-blank, essay questions (no metadata)
CREATE TABLE correct_answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
  answer_text TEXT NOT NULL,
  is_case_sensitive BOOLEAN DEFAULT false,
  is_exact_match BOOLEAN DEFAULT true,
  points INTEGER DEFAULT 1,
  sort_order INTEGER DEFAULT 0
);

-- User profiles extending Supabase auth
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT,
  full_name TEXT,
  avatar_url TEXT,
  role TEXT DEFAULT 'student' CHECK (role IN ('admin', 'teacher', 'student')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User learning sessions
CREATE TABLE user_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) DEFAULT auth.uid(),
  topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
  session_name TEXT,
  total_questions INTEGER DEFAULT 0,
  completed_questions INTEGER DEFAULT 0,
  total_score INTEGER DEFAULT 0,
  max_possible_score INTEGER DEFAULT 0,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- User answers and responses
CREATE TABLE user_answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES user_sessions(id) ON DELETE CASCADE,
  question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
  choice_id UUID REFERENCES choices(id) ON DELETE SET NULL,
  answer_text TEXT,
  is_correct BOOLEAN,
  points_earned INTEGER DEFAULT 0,
  time_spent_seconds INTEGER,
  answered_at TIMESTAMPTZ DEFAULT NOW()
);

-- =========================
-- INDEXES FOR PERFORMANCE
-- =========================

-- Topics indexes
CREATE INDEX idx_topics_path ON topics USING GIST (path);
CREATE INDEX idx_topics_parent ON topics (parent_id);
CREATE INDEX idx_topics_created_by ON topics (created_by);

-- Questions indexes
CREATE INDEX idx_questions_topic ON questions(topic_id);
CREATE INDEX idx_questions_type ON questions(question_type);
CREATE INDEX idx_questions_difficulty ON questions(difficulty_level);
CREATE INDEX idx_questions_created_by ON questions(created_by);

-- Choices and answers indexes
CREATE INDEX idx_choices_question ON choices(question_id, sort_order);
CREATE INDEX idx_correct_answers_question ON correct_answers(question_id, sort_order);

-- User data indexes
CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_topic ON user_sessions(topic_id);
CREATE INDEX idx_user_answers_session ON user_answers(session_id);
CREATE INDEX idx_user_answers_question ON user_answers(question_id);

-- =========================
-- TRIGGERS AND FUNCTIONS
-- =========================

-- Auto-maintain ltree path for hierarchical topics
CREATE OR REPLACE FUNCTION maintain_topic_path() 
RETURNS TRIGGER AS $$
DECLARE
  parent_path LTREE;
BEGIN
  IF NEW.parent_id IS NULL THEN
    NEW.path := text2ltree(generate_slug(NEW.name));
  ELSE
    SELECT path INTO parent_path FROM topics WHERE id = NEW.parent_id;
    IF parent_path IS NULL THEN
      RAISE EXCEPTION 'Parent topic not found';
    END IF;
    NEW.path := parent_path || text2ltree(generate_slug(NEW.name));
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER topic_path_trigger
  BEFORE INSERT OR UPDATE OF parent_id, name ON topics
  FOR EACH ROW EXECUTE FUNCTION maintain_topic_path();

-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER topics_updated_at BEFORE UPDATE ON topics
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER questions_updated_at BEFORE UPDATE ON questions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER user_profiles_updated_at BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-create user profile on signup
CREATE OR REPLACE FUNCTION handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO user_profiles (id, email, full_name)
  VALUES (NEW.id, NEW.email, COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Auto-update session statistics
CREATE OR REPLACE FUNCTION update_session_stats()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE user_sessions 
  SET 
    completed_questions = (
      SELECT COUNT(*) FROM user_answers 
      WHERE session_id = NEW.session_id
    ),
    total_score = (
      SELECT COALESCE(SUM(points_earned), 0) FROM user_answers 
      WHERE session_id = NEW.session_id
    ),
    completed_at = CASE 
      WHEN (SELECT COUNT(*) FROM user_answers WHERE session_id = NEW.session_id) >= 
           (SELECT total_questions FROM user_sessions WHERE id = NEW.session_id)
      THEN NOW() 
      ELSE completed_at 
    END
  WHERE id = NEW.session_id;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_session_stats_trigger
  AFTER INSERT OR UPDATE ON user_answers
  FOR EACH ROW EXECUTE FUNCTION update_session_stats();

-- =========================
-- HELPER FUNCTIONS
-- =========================

-- Get all leaf topics (topics with no children)
CREATE OR REPLACE FUNCTION get_leaf_topics()
RETURNS TABLE (
    id UUID,
    name TEXT,
    description TEXT,
    path LTREE,
    parent_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT t.id, t.name, t.description, t.path, t.parent_id
    FROM topics t
    WHERE NOT EXISTS (
        SELECT 1 FROM topics child 
        WHERE child.parent_id = t.id
    )
    AND t.parent_id IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Count questions for a topic (including subtopics)
CREATE OR REPLACE FUNCTION count_topic_questions(topic_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
    question_count INTEGER;
    topic_path LTREE;
BEGIN
    -- Get the path of the topic
    SELECT path INTO topic_path FROM topics WHERE id = topic_uuid;
    
    -- Count questions in this topic and all subtopics
    SELECT COUNT(*) INTO question_count
    FROM questions q
    JOIN topics t ON q.topic_id = t.id
    WHERE t.path <@ topic_path OR t.id = topic_uuid;
    
    RETURN question_count;
END;
$$ LANGUAGE plpgsql;

-- Get course statistics
CREATE OR REPLACE FUNCTION get_course_stats(main_topic_id UUID)
RETURNS TABLE (
    total_topics INTEGER,
    total_questions INTEGER,
    total_leaf_topics INTEGER
) AS $$
DECLARE
    topic_path LTREE;
BEGIN
    SELECT path INTO topic_path FROM topics WHERE id = main_topic_id;
    
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INTEGER FROM topics WHERE path <@ topic_path) as total_topics,
        (SELECT COUNT(*)::INTEGER FROM questions q 
         JOIN topics t ON q.topic_id = t.id 
         WHERE t.path <@ topic_path) as total_questions,
        (SELECT COUNT(*)::INTEGER FROM topics t 
         WHERE t.path <@ topic_path 
         AND NOT EXISTS (SELECT 1 FROM topics child WHERE child.parent_id = t.id)) as total_leaf_topics;
END;
$$ LANGUAGE plpgsql;

-- =========================
-- ROW LEVEL SECURITY POLICIES
-- =========================

-- Enable RLS on all tables
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE choices ENABLE ROW LEVEL SECURITY;
ALTER TABLE correct_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Topics policies - Public read, owner write
CREATE POLICY "Topics are viewable by everyone" ON topics FOR SELECT USING (true);
CREATE POLICY "Users can create topics" ON topics FOR INSERT WITH CHECK (auth.uid() = created_by);
CREATE POLICY "Users can update their own topics" ON topics FOR UPDATE USING (auth.uid() = created_by);
CREATE POLICY "Users can delete their own topics" ON topics FOR DELETE USING (auth.uid() = created_by);

-- Questions policies - Public read, owner write
CREATE POLICY "Questions are viewable by everyone" ON questions FOR SELECT USING (true);
CREATE POLICY "Users can create questions" ON questions FOR INSERT WITH CHECK (auth.uid() = created_by);
CREATE POLICY "Users can update their own questions" ON questions FOR UPDATE USING (auth.uid() = created_by);
CREATE POLICY "Users can delete their own questions" ON questions FOR DELETE USING (auth.uid() = created_by);

-- Choices policies - Public read, question owner write
CREATE POLICY "Choices are viewable by everyone" ON choices FOR SELECT USING (true);
CREATE POLICY "Users can manage choices for their questions" ON choices FOR ALL USING (
    EXISTS (SELECT 1 FROM questions WHERE questions.id = choices.question_id AND questions.created_by = auth.uid())
);

-- Correct answers policies - Public read, question owner write
CREATE POLICY "Correct answers are viewable by everyone" ON correct_answers FOR SELECT USING (true);
CREATE POLICY "Users can manage correct answers for their questions" ON correct_answers FOR ALL USING (
    EXISTS (SELECT 1 FROM questions WHERE questions.id = correct_answers.question_id AND questions.created_by = auth.uid())
);

-- User sessions policies - Private to user
CREATE POLICY "Users can manage their own sessions" ON user_sessions FOR ALL USING (auth.uid() = user_id);

-- User answers policies - Private to session owner
CREATE POLICY "Users can manage their own answers" ON user_answers FOR ALL USING (
    EXISTS (SELECT 1 FROM user_sessions WHERE user_sessions.id = user_answers.session_id AND user_sessions.user_id = auth.uid())
);

-- User profiles policies
CREATE POLICY "Profiles are viewable by everyone" ON user_profiles FOR SELECT USING (true);
CREATE POLICY "Users can update their own profile" ON user_profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert their own profile" ON user_profiles FOR INSERT WITH CHECK (auth.uid() = id);