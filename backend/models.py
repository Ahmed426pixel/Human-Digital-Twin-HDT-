from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import bcrypt

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    profiles = relationship("HDTProfile", back_populates="user")
    sessions = relationship("Session", back_populates="user")
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class HDTProfile(Base):
    __tablename__ = 'hdt_profiles'
    
    profile_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    role_type = Column(String(50), nullable=False)  # software_engineer, office_worker, factory_worker
    display_name = Column(String(100))
    avatar_model_path = Column(String(255))
    capabilities = Column(JSON)
    preferences = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="profiles")
    sessions = relationship("Session", back_populates="profile")
    tasks = relationship("AITask", back_populates="profile")
    
    def to_dict(self):
        return {
            'profile_id': self.profile_id,
            'user_id': self.user_id,
            'role_type': self.role_type,
            'display_name': self.display_name,
            'avatar_model_path': self.avatar_model_path,
            'capabilities': self.capabilities,
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Session(Base):
    __tablename__ = 'sessions'
    
    session_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    profile_id = Column(Integer, ForeignKey('hdt_profiles.profile_id'), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.now)
    end_time = Column(DateTime)
    session_duration = Column(Integer)  # seconds
    total_tasks_completed = Column(Integer, default=0)
    avg_cognitive_load = Column(Float)
    avg_stress_level = Column(Float)
    session_notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    profile = relationship("HDTProfile", back_populates="sessions")
    physiological_data = relationship("PhysiologicalData", back_populates="session")
    work_activities = relationship("WorkActivity", back_populates="session")
    tasks = relationship("AITask", back_populates="session")
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'profile_id': self.profile_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'session_duration': self.session_duration,
            'total_tasks_completed': self.total_tasks_completed,
            'is_active': self.is_active
        }

class PhysiologicalData(Base):
    __tablename__ = 'physiological_data'
    
    data_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.session_id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    heart_rate = Column(Integer)
    hrv = Column(Float)
    skin_temperature = Column(Float)
    stress_level = Column(Float)
    cognitive_load = Column(Float)
    fatigue_score = Column(Float)
    posture_score = Column(Float)
    raw_sensor_data = Column(JSON)
    
    # Relationships
    session = relationship("Session", back_populates="physiological_data")
    
    def to_dict(self):
        return {
            'data_id': self.data_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'heart_rate': self.heart_rate,
            'stress_level': self.stress_level,
            'cognitive_load': self.cognitive_load,
            'fatigue_score': self.fatigue_score,
            'posture_score': self.posture_score
        }

class WorkActivity(Base):
    __tablename__ = 'work_activities'
    
    activity_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.session_id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    activity_type = Column(String(50))
    typing_speed = Column(Integer)
    mouse_movements = Column(Integer)
    application_name = Column(String(255))
    window_title = Column(String(255))
    screen_time_seconds = Column(Integer)
    focus_score = Column(Float)
    
    # Relationships
    session = relationship("Session", back_populates="work_activities")
    
    def to_dict(self):
        return {
            'activity_id': self.activity_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'activity_type': self.activity_type,
            'typing_speed': self.typing_speed,
            'focus_score': self.focus_score
        }

class AITask(Base):
    __tablename__ = 'ai_tasks'
    
    task_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.session_id'), nullable=False)
    profile_id = Column(Integer, ForeignKey('hdt_profiles.profile_id'), nullable=False)
    task_type = Column(String(100))
    command_text = Column(Text, nullable=False)
    task_status = Column(String(50), default='pending')
    priority = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time_seconds = Column(Integer)
    result_data = Column(JSON)
    error_message = Column(Text)
    tokens_used = Column(Integer)
    estimated_complexity = Column(String(50))
    
    # Relationships
    session = relationship("Session", back_populates="tasks")
    profile = relationship("HDTProfile", back_populates="tasks")
    interactions = relationship("AIInteraction", back_populates="task")
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'session_id': self.session_id,
            'task_type': self.task_type,
            'command_text': self.command_text,
            'task_status': self.task_status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result_data': self.result_data,
            'error_message': self.error_message
        }

class AIInteraction(Base):
    __tablename__ = 'ai_interactions'
    
    interaction_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.session_id'), nullable=False)
    task_id = Column(Integer, ForeignKey('ai_tasks.task_id'))
    timestamp = Column(DateTime, default=datetime.now)
    role = Column(String(20), nullable=False)  # user, assistant, system
    message_text = Column(Text, nullable=False)
    context_data = Column(JSON)
    tokens_used = Column(Integer)
    
    # Relationships
    task = relationship("AITask", back_populates="interactions")
    
    def to_dict(self):
        return {
            'interaction_id': self.interaction_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'role': self.role,
            'message_text': self.message_text
        }