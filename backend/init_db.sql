-- Industry-Level Human Digital Twin Database
-- PostgreSQL Initialization Script

-- Create database (run this as postgres superuser)
-- CREATE DATABASE hdt_database;

-- Connect to the database
-- \c hdt_database;

-- Enable UUID extension (optional, for future use)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

CREATE INDEX IF NOT EXISTS idx_hdt_profiles_user ON hdt_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_hdt_profiles_role ON hdt_profiles(role_type);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time DESC);

CREATE INDEX IF NOT EXISTS idx_physio_session ON physiological_data(session_id);
CREATE INDEX IF NOT EXISTS idx_physio_timestamp ON physiological_data(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_work_activities_session ON work_activities(session_id);
CREATE INDEX IF NOT EXISTS idx_work_activities_timestamp ON work_activities(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_ai_tasks_session ON ai_tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_tasks_status ON ai_tasks(task_status);
CREATE INDEX IF NOT EXISTS idx_ai_tasks_created ON ai_tasks(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_interactions_session ON ai_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_interactions_task ON ai_interactions(task_id);
CREATE INDEX IF NOT EXISTS idx_ai_interactions_timestamp ON ai_interactions(timestamp DESC);

-- Insert default configuration values
-- Note: These will be created by SQLAlchemy models, but you can insert manually if needed

-- Create a view for session analytics
CREATE OR REPLACE VIEW session_analytics AS
SELECT 
    s.session_id,
    s.user_id,
    s.start_time,
    s.end_time,
    s.session_duration,
    COUNT(DISTINCT at.task_id) as total_tasks,
    COUNT(DISTINCT CASE WHEN at.task_status = 'completed' THEN at.task_id END) as completed_tasks,
    AVG(pd.stress_level) as avg_stress,
    AVG(pd.cognitive_load) as avg_cognitive_load,
    AVG(wa.focus_score) as avg_focus
FROM sessions s
LEFT JOIN ai_tasks at ON s.session_id = at.session_id
LEFT JOIN physiological_data pd ON s.session_id = pd.session_id
LEFT JOIN work_activities wa ON s.session_id = wa.session_id
GROUP BY s.session_id;

-- Create a function to clean old data (optional)
CREATE OR REPLACE FUNCTION cleanup_old_data(retention_days INTEGER DEFAULT 90)
RETURNS TABLE(deleted_physio BIGINT, deleted_activities BIGINT, deleted_interactions BIGINT) AS $$
DECLARE
    cutoff_date TIMESTAMP;
    physio_count BIGINT;
    activity_count BIGINT;
    interaction_count BIGINT;
BEGIN
    cutoff_date := NOW() - (retention_days || ' days')::INTERVAL;
    
    DELETE FROM physiological_data WHERE timestamp < cutoff_date;
    GET DIAGNOSTICS physio_count = ROW_COUNT;
    
    DELETE FROM work_activities WHERE timestamp < cutoff_date;
    GET DIAGNOSTICS activity_count = ROW_COUNT;
    
    DELETE FROM ai_interactions WHERE timestamp < cutoff_date;
    GET DIAGNOSTICS interaction_count = ROW_COUNT;
    
    RETURN QUERY SELECT physio_count, activity_count, interaction_count;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;