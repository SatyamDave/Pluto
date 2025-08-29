-- Migration: Add timezone support for users
-- Date: 2024-01-XX
-- Description: Add timezone field to users table and create timezone preferences

-- Add timezone column to users table
ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC';

-- Create index on timezone for efficient queries
CREATE INDEX idx_users_timezone ON users(timezone);

-- Insert default timezone preferences for existing users
INSERT INTO user_preferences (user_id, preference_key, preference_value, updated_at)
SELECT 
    id as user_id,
    'timezone' as preference_key,
    'UTC' as preference_value,
    NOW() as updated_at
FROM users 
WHERE id NOT IN (
    SELECT user_id FROM user_preferences WHERE preference_key = 'timezone'
);

-- Add timezone validation constraint
ALTER TABLE users ADD CONSTRAINT chk_timezone_valid 
CHECK (timezone IN (
    'UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
    'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Asia/Tokyo', 'Asia/Shanghai',
    'Australia/Sydney', 'Pacific/Auckland'
));

-- Update existing users with common timezones based on phone number patterns
-- This is a placeholder for future implementation
-- UPDATE users SET timezone = 'America/New_York' WHERE phone_number LIKE '+1%' AND timezone = 'UTC';
