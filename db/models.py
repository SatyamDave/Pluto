"""
Database models for Jarvis Phone AI Assistant
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    reminders = relationship("Reminder", back_populates="user")
    notes = relationship("Note", back_populates="user")
    calendar_events = relationship("CalendarEvent", back_populates="user")
    
    def __repr__(self):
        return f"<User(phone_number='{self.phone_number}', name='{self.name}')>"


class Reminder(Base):
    """Reminder model"""
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    reminder_time = Column(DateTime(timezone=True), nullable=False)
    is_completed = Column(Boolean, default=False)
    reminder_type = Column(String(50), default="sms")  # sms, call, both
    status = Column(String(50), default="pending")  # pending, sent, confirmed, failed
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reminders")
    
    def __repr__(self):
        return f"<Reminder(title='{self.title}', time='{self.reminder_time}')>"


class Note(Base):
    """Note/To-do model"""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    note_type = Column(String(50), default="note")  # note, todo, list
    is_completed = Column(Boolean, default=False)
    priority = Column(String(20), default="medium")  # low, medium, high
    tags = Column(JSON, default=list)  # Store as JSON array
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notes")
    
    def __repr__(self):
        return f"<Note(title='{self.title}', type='{self.note_type}')>"


class CalendarEvent(Base):
    """Calendar event model"""
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(String(255), nullable=False)  # External calendar event ID
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(255), nullable=True)
    attendees = Column(JSON, default=list)  # Store as JSON array
    calendar_source = Column(String(50), default="google")  # google, outlook, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="calendar_events")
    
    def __repr__(self):
        return f"<CalendarEvent(title='{self.title}', start='{self.start_time}')>"


class EmailMessage(Base):
    """Email message model"""
    __tablename__ = "email_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(String(255), nullable=False)  # External email message ID
    subject = Column(String(500), nullable=True)
    sender = Column(String(255), nullable=False)
    recipients = Column(JSON, default=list)  # Store as JSON array
    content = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    is_important = Column(Boolean, default=False)
    email_source = Column(String(50), default="gmail")  # gmail, outlook, etc.
    received_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<EmailMessage(subject='{self.subject}', sender='{self.sender}')>"


class Conversation(Base):
    """Conversation history model"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), nullable=False)
    message_type = Column(String(20), nullable=False)  # sms, voice
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True)
    action_taken = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Conversation(session='{self.session_id}', intent='{self.intent}')>"


class UserMemory(Base):
    """User memory table for Pluto's long-term memory"""
    __tablename__ = "user_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(String, index=True, nullable=False)  # reminder, schedule, habit, contact, sms, call, email
    content = Column(Text, nullable=False)
    embedding = Column(Text)  # JSON string of embedding vector
    context_data = Column(JSON)  # Additional context like confidence, entities, etc.
    related_memories = Column(JSON)  # IDs of related memories
    importance_score = Column(Float, default=0.5)  # 0.0 to 1.0, higher = more important
    is_active = Column(Boolean, default=True)  # For soft deletion
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_user_memory_user_type', 'user_id', 'type'),
        Index('idx_user_memory_timestamp', 'timestamp'),
        Index('idx_user_memory_importance', 'importance_score'),
    )


class UserStyleProfile(Base):
    """User's personal style and personality preferences"""
    __tablename__ = "user_style_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    emoji_usage = Column(Boolean, default=True)
    formality_level = Column(String, default='casual')  # casual, formal, mixed
    avg_message_length = Column(String, default='medium')  # short, medium, long
    signature_phrases = Column(JSON, default=list)  # ["on it", "yep", "got it"]
    tone_preferences = Column(JSON, default=dict)  # {"humor": 0.7, "formality": 0.3}
    communication_style = Column(String, default='friendly')  # friendly, direct, professional
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<UserStyleProfile(user_id='{self.user_id}', style='{self.formality_level}')>"


class UserHabit(Base):
    """User habit patterns for proactive behavior"""
    __tablename__ = "user_habit"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    pattern_type = Column(String, nullable=False)  # time_based, frequency_based, context_based
    pattern_data = Column(JSON, nullable=False)  # Pattern details (time, frequency, context)
    confidence = Column(Float, default=0.0)  # How confident we are in this habit
    last_observed = Column(DateTime(timezone=True), server_default=func.now())
    observation_count = Column(Integer, default=1)
    next_predicted = Column(DateTime(timezone=True))  # When this habit is likely to occur next
    proactive_suggestions = Column(JSON)  # What Pluto should suggest
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_user_habits_user_pattern', 'user_id', 'pattern_type'),
        Index('idx_user_habits_confidence', 'confidence'),
        Index('idx_user_habits_next_predicted', 'next_predicted'),
    )


class ProactiveTask(Base):
    """Scheduled proactive tasks for Pluto"""
    __tablename__ = "proactive_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    task_type = Column(String, nullable=False)  # morning_digest, inbox_check, habit_reminder, calendar_alert
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    priority = Column(Integer, default=5)  # 1-10, higher = more urgent
    task_data = Column(JSON)  # Task-specific data
    status = Column(String, default='pending')  # pending, running, completed, failed
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_proactive_tasks_user_status', 'user_id', 'status'),
        Index('idx_proactive_tasks_scheduled', 'scheduled_time'),
        Index('idx_proactive_tasks_priority', 'priority'),
    )


class ExternalContact(Base):
    """External contacts that Pluto can interact with"""
    __tablename__ = "external_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    relationship = Column(String)  # boss, friend, family, service_provider
    permissions = Column(JSON)  # What Pluto can do (call, text, email)
    last_interaction = Column(DateTime(timezone=True))
    interaction_history = Column(JSON)  # History of interactions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_external_contacts_user', 'user_id'),
        Index('idx_external_contacts_phone', 'phone'),
        Index('idx_external_contacts_email', 'email'),
        Index('idx_external_contacts_relationship', 'relationship'),
    )


class UserPreference(Base):
    """User preferences and settings for Pluto"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    preference_key = Column(String, nullable=False)
    preference_value = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'preference_key', name='uq_user_preference'),
    )


class RelationshipGraph(Base):
    """Graph of relationships between entities in user's life"""
    __tablename__ = "relationship_graph"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    entity1_type = Column(String, nullable=False)  # person, event, place, topic
    entity1_id = Column(String, nullable=False)  # ID or name of first entity
    entity2_type = Column(String, nullable=False)  # person, event, place, topic
    entity2_id = Column(String, nullable=False)  # ID or name of second entity
    relationship_type = Column(String, nullable=False)  # works_with, attends, located_at, related_to
    strength = Column(Float, default=1.0)  # Relationship strength (0.0 to 1.0)
    context = Column(JSON)  # Additional context about the relationship
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_relationship_graph_user', 'user_id'),
        Index('idx_relationship_graph_entity1', 'entity1_type', 'entity1_id'),
        Index('idx_relationship_graph_entity2', 'entity2_type', 'entity2_id'),
        Index('idx_relationship_graph_type', 'relationship_type'),
    )


class ContextSnapshot(Base):
    """Snapshots of user's context at specific points in time"""
    __tablename__ = "context_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    context_type = Column(String, nullable=False)  # daily, weekly, event_based
    context_data = Column(JSON, nullable=False)  # Full context snapshot
    summary = Column(Text)  # Human-readable summary
    is_active = Column(Boolean, default=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_context_snapshots_user', 'user_id'),
        Index('idx_context_snapshots_timestamp', 'timestamp'),
        Index('idx_context_snapshots_type', 'context_type'),
    )


class ActionLog(Base):
    """Log of all actions taken by Pluto on behalf of users"""
    __tablename__ = "action_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)  # String to match action_layer usage
    action_type = Column(String, nullable=False)  # send_email, send_sms, place_call, etc.
    action_data = Column(JSON, nullable=True)  # Data needed for the action
    contact_info = Column(JSON, nullable=True)  # Information about external contact
    status = Column(String, default="pending")  # pending, confirmed, executed, cancelled, failed
    result = Column(JSON, nullable=True)  # Result of the action execution
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # When action expires if not confirmed
    
    # Indexes
    __table_args__ = (
        Index('idx_action_logs_user', 'user_id'),
        Index('idx_action_logs_type', 'action_type'),
        Index('idx_action_logs_status', 'status'),
        Index('idx_action_logs_created', 'created_at'),
        Index('idx_action_logs_expires', 'expires_at'),
    )


class ContactPermission(Base):
    """Permissions for external contacts and actions"""
    __tablename__ = "contact_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("external_contacts.id"), nullable=False, index=True)
    action_type = Column(String, nullable=False)  # send_email, send_sms, place_call, etc.
    permission_level = Column(String, nullable=False)  # always_ask, auto_approve, never_allow
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('contact_id', 'action_type', name='uq_contact_permission'),
        Index('idx_contact_permissions_contact', 'contact_id'),
        Index('idx_contact_permissions_action', 'action_type'),
        Index('idx_contact_permissions_level', 'permission_level'),
    )
