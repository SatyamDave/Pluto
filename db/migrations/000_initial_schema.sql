-- Initial Database Schema for Pluto AI Phone Assistant
-- This creates all tables from scratch

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    email VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    last_seen TIMESTAMPTZ
);

-- Create user_style_profiles table
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

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    preference_key VARCHAR NOT NULL,
    preference_value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, preference_key)
);

-- Create user_memory table
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

-- Create user_habit table
CREATE TABLE IF NOT EXISTS user_habit (
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

-- Create proactive_tasks table
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

-- Create external_contacts table
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

-- Create relationship_graph table
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
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create context_snapshots table
CREATE TABLE IF NOT EXISTS context_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    snapshot_time TIMESTAMPTZ DEFAULT now(),
    context_type VARCHAR NOT NULL,
    context_data JSONB NOT NULL,
    importance_score FLOAT DEFAULT 0.5
);

-- Create action_logs table
CREATE TABLE IF NOT EXISTS action_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    action_type VARCHAR NOT NULL,
    action_data JSONB NOT NULL,
    status VARCHAR NOT NULL,
    result JSONB,
    timestamp TIMESTAMPTZ DEFAULT now(),
    execution_time_ms INTEGER,
    error_message TEXT
);

-- Create contact_permissions table
CREATE TABLE IF NOT EXISTS contact_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    contact_id INTEGER REFERENCES external_contacts(id) NOT NULL,
    action_type VARCHAR NOT NULL,
    permission_level VARCHAR NOT NULL,
    auto_approve BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, contact_id, action_type)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_memory_user_id ON user_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_user_memory_timestamp ON user_memory(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_memory_type ON user_memory(type);
CREATE INDEX IF NOT EXISTS idx_user_habit_user_id ON user_habit(user_id);
CREATE INDEX IF NOT EXISTS idx_proactive_tasks_user_id ON proactive_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_proactive_tasks_scheduled_time ON proactive_tasks(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_external_contacts_user_id ON external_contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_action_logs_user_id ON action_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_action_logs_timestamp ON action_logs(timestamp);
