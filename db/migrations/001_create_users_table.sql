-- Migration: Create users table and update existing tables
-- Run this after updating the models.py file

-- Add last_seen column to users table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'last_seen') THEN
        ALTER TABLE users ADD COLUMN last_seen TIMESTAMPTZ;
    END IF;
END $$;

-- Create user_style_profiles table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_style_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE NOT NULL,
    emoji_usage BOOLEAN DEFAULT TRUE,
    formality_level VARCHAR DEFAULT 'casual',
    avg_message_length VARCHAR DEFAULT 'medium',
    signature_phrases JSONB DEFAULT '[]',
    tone_preferences JSONB DEFAULT '{}',
    communication_style VARCHAR DEFAULT 'friendly',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create user_preferences table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    preference_key VARCHAR NOT NULL,
    preference_value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, preference_key)
);

-- Create user_memory table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_memory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now(),
    type VARCHAR NOT NULL,
    content TEXT NOT NULL,
    embedding TEXT, -- JSON string of embedding vector
    context_data JSONB, -- Additional context like confidence, entities, etc.
    related_memories JSONB, -- IDs of related memories
    importance_score FLOAT DEFAULT 0.5,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create user_habits table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_habits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    pattern_type VARCHAR NOT NULL,
    pattern_data JSONB NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    last_observed TIMESTAMPTZ DEFAULT now(),
    observation_count INTEGER DEFAULT 1,
    next_predicted TIMESTAMPTZ,
    proactive_suggestions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create proactive_tasks table if it doesn't exist
CREATE TABLE IF NOT EXISTS proactive_tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    task_type VARCHAR NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    priority INTEGER DEFAULT 5,
    task_data JSONB,
    status VARCHAR DEFAULT 'pending',
    last_run TIMESTAMPTZ,
    next_run TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create external_contacts table if it doesn't exist
CREATE TABLE IF NOT EXISTS external_contacts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    name VARCHAR NOT NULL,
    phone VARCHAR,
    email VARCHAR,
    relationship VARCHAR,
    permissions JSONB,
    last_interaction TIMESTAMPTZ,
    interaction_history JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create relationship_graph table if it doesn't exist
CREATE TABLE IF NOT EXISTS relationship_graph (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    entity1_type VARCHAR NOT NULL,
    entity1_id VARCHAR NOT NULL,
    entity2_type VARCHAR NOT NULL,
    entity2_id VARCHAR NOT NULL,
    relationship_type VARCHAR NOT NULL,
    strength FLOAT DEFAULT 1.0,
    context JSONB,
    last_updated TIMESTAMPTZ DEFAULT now()
);

-- Create context_snapshots table if it doesn't exist
CREATE TABLE IF NOT EXISTS context_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now(),
    context_type VARCHAR NOT NULL,
    context_data JSONB NOT NULL,
    summary TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_style_profiles_user_id ON user_style_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_memory_user_id ON user_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_user_memory_type ON user_memory(type);
CREATE INDEX IF NOT EXISTS idx_user_memory_timestamp ON user_memory(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_habits_user_id ON user_habits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_habits_pattern_type ON user_habits(pattern_type);
CREATE INDEX IF NOT EXISTS idx_proactive_tasks_user_id ON proactive_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_proactive_tasks_scheduled ON proactive_tasks(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_external_contacts_user_id ON external_contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_relationship_graph_user_id ON relationship_graph(user_id);
CREATE INDEX IF NOT EXISTS idx_context_snapshots_user_id ON context_snapshots(user_id);

-- Insert default preferences for existing users (if any)
INSERT INTO user_preferences (user_id, preference_key, preference_value)
SELECT 
    u.id,
    'auto_confirm_family',
    'true'::jsonb
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_preferences up 
    WHERE up.user_id = u.id AND up.preference_key = 'auto_confirm_family'
);

INSERT INTO user_preferences (user_id, preference_key, preference_value)
SELECT 
    u.id,
    'auto_confirm_work',
    'false'::jsonb
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_preferences up 
    WHERE up.user_id = u.id AND up.preference_key = 'auto_confirm_work'
);

INSERT INTO user_preferences (user_id, preference_key, preference_value)
SELECT 
    u.id,
    'morning_digest_enabled',
    'true'::jsonb
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_preferences up 
    WHERE up.user_id = u.id AND up.preference_key = 'morning_digest_enabled'
);

INSERT INTO user_preferences (user_id, preference_key, preference_value)
SELECT 
    u.id,
    'proactive_mode',
    'true'::jsonb
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_preferences up 
    WHERE up.user_id = u.id AND up.preference_key = 'proactive_mode'
);

INSERT INTO user_preferences (user_id, preference_key, preference_value)
SELECT 
    u.id,
    'wake_up_calls',
    'true'::jsonb
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_preferences up 
    WHERE up.user_id = u.id AND up.preference_key = 'wake_up_calls'
);

INSERT INTO user_preferences (user_id, preference_key, preference_value)
SELECT 
    u.id,
    'email_summaries',
    'true'::jsonb
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_preferences up 
    WHERE up.user_id = u.id AND up.preference_key = 'email_summaries'
);

INSERT INTO user_preferences (user_id, preference_key, preference_value)
SELECT 
    u.id,
    'calendar_alerts',
    'true'::jsonb
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_preferences up 
    WHERE up.user_id = u.id AND up.preference_key = 'calendar_alerts'
);

-- Create default style profiles for existing users
INSERT INTO user_style_profiles (user_id, emoji_usage, formality_level, avg_message_length, signature_phrases, tone_preferences, communication_style)
SELECT 
    u.id,
    TRUE,
    'casual',
    'medium',
    '[]'::jsonb,
    '{"humor": 0.5, "formality": 0.3}'::jsonb,
    'friendly'
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_style_profiles usp WHERE usp.user_id = u.id
);
