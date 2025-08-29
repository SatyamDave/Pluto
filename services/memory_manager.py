#!/usr/bin/env python3
"""
Pluto Memory Manager
Handles long-term memory with Postgres and fast recall with Redis
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import redis.asyncio as redis

from db.database import get_db
from db.models import UserMemory, UserHabit, ProactiveTask, ExternalContact, UserPreference, UserStyleProfile, RelationshipGraph, ContextSnapshot
from config import settings
from utils.logging_config import get_logger
from utils.constants import MAX_MEMORY_RECALL, MAX_CONTEXT_ITEMS, CACHE_TTL

# Helper function for Python 3.9 compatibility
async def get_db_session():
    """Get database session with Python 3.9 compatibility"""
    return await get_db().__anext__()

logger = get_logger(__name__)

class MemoryManager:
    """Pluto's memory manager - never forgets anything"""
    
    def __init__(self):
        self.redis_client = None
        self.openai_client = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize Redis and OpenAI clients"""
        try:
            # Redis for fast context recall
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            logger.info("Redis client initialized")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.redis_client = None
        
        try:
            # OpenAI for embeddings
            if settings.OPENAI_API_KEY:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized for embeddings")
        except Exception as e:
            logger.warning(f"OpenAI not available for embeddings: {e}")
            self.openai_client = None
    
    async def store_memory(
        self, 
        user_id: int, 
        memory_type: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: float = 0.5,
        related_memories: Optional[List[int]] = None,
        schedule_reminder: bool = True
    ) -> int:
        """
        Store a new memory in Postgres with embedding and relationships
        
        Args:
            user_id: User identifier
            memory_type: Type of memory (sms, email, calendar, etc.)
            content: Memory content
            metadata: Additional context data
            importance_score: Importance score (0.0 to 1.0)
            related_memories: List of related memory IDs
            
        Returns:
            Memory ID
        """
        try:
            # Generate embedding for semantic search
            embedding = None
            if self.openai_client:
                embedding = await self._generate_embedding(content)
            
            # Store in Postgres
            db = await get_db_session()
            memory = UserMemory(
                user_id=user_id,
                type=memory_type,
                content=content,
                embedding=json.dumps(embedding) if embedding else None,
                context_data=metadata or {},
                related_memories=related_memories or [],
                importance_score=importance_score
            )
            db.add(memory)
            await db.commit()
            await db.refresh(memory)
            
            # Store recent context in Redis (last 24h)
            await self._store_recent_context(user_id, memory_type, content, memory.id)
            
            # Update relationship graph if related memories exist
            if related_memories:
                await self._update_relationship_graph(user_id, memory.id, related_memories)
            
            # Update importance scores based on relationships
            await self._update_importance_scores(user_id, memory.id)
            
            # Schedule smart reminder if requested and it's a reminder-type memory
            if schedule_reminder and memory_type in ["reminder", "todo", "note", "voice_note"]:
                await self._schedule_smart_reminder(user_id, memory.id, content, importance_score)
            
            logger.info(f"Stored memory for user {user_id}: {memory_type} (ID: {memory.id})")
            return memory.id
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            raise
    
    async def recall_memory(
        self, 
        user_id: int, 
        query: str = None, 
        memory_type: str = None, 
        limit: int = 10,
        hours_back: int = 24,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Recall memories - semantic search if query provided, otherwise recent
        
        Args:
            user_id: User identifier
            query: Search query for semantic search
            memory_type: Filter by memory type
            limit: Maximum number of memories to return
            hours_back: Hours to look back
            min_importance: Minimum importance score
            
        Returns:
            List of memory dictionaries
        """
        try:
            db = await get_db_session()
            
            if query and self.openai_client:
                # Semantic search using embeddings
                return await self._semantic_search(user_id, query, limit, min_importance)
            else:
                # Traditional search by type and time
                query_filter = and_(
                    UserMemory.user_id == user_id,
                    UserMemory.is_active == True,
                    UserMemory.importance_score >= min_importance
                )
                
                if memory_type:
                    query_filter = and_(query_filter, UserMemory.type == memory_type)
                
                if hours_back > 0:
                    cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
                    query_filter = and_(query_filter, UserMemory.timestamp >= cutoff_time)
                
                memories = db.query(UserMemory).filter(query_filter).order_by(
                    desc(UserMemory.importance_score),
                    desc(UserMemory.timestamp)
                ).limit(limit).all()
                
                return [self._memory_to_dict(memory) for memory in memories]
                
        except Exception as e:
            logger.error(f"Error recalling memory: {e}")
            return []
    
    async def _semantic_search(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 10,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        try:
            # Generate embedding for query
            query_embedding = await self._generate_embedding(query)
            if not query_embedding:
                return []
            
            # Get all user memories with embeddings
            db = await get_db_session()
            memories = db.query(UserMemory).filter(
                and_(
                    UserMemory.user_id == user_id,
                    UserMemory.is_active == True,
                    UserMemory.embedding.isnot(None),
                    UserMemory.importance_score >= min_importance
                )
            ).limit(MAX_MEMORY_RECALL).all()
            
            if not memories:
                return []
            
            # Calculate cosine similarity
            similarities = []
            for memory in memories:
                try:
                    memory_embedding = json.loads(memory.embedding)
                    similarity = self._cosine_similarity(query_embedding, memory_embedding)
                    similarities.append((similarity, memory))
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            top_memories = similarities[:limit]
            
            return [self._memory_to_dict(memory) for _, memory in top_memories]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    async def get_related_memories(
        self, 
        user_id: str, 
        memory_id: int, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get memories related to a specific memory"""
        try:
            db = await get_db_session()
            
            # Get the target memory
            target_memory = db.query(UserMemory).filter(
                and_(
                    UserMemory.id == memory_id,
                    UserMemory.user_id == user_id
                )
            ).first()
            
            if not target_memory or not target_memory.related_memories:
                return []
            
            # Get related memories
            related_ids = target_memory.related_memories
            related_memories = db.query(UserMemory).filter(
                and_(
                    UserMemory.id.in_(related_ids),
                    UserMemory.is_active == True
                )
            ).limit(limit).all()
            
            return [self._memory_to_dict(memory) for memory in related_memories]
            
        except Exception as e:
            logger.error(f"Error getting related memories: {e}")
            return []
    
    async def get_memory_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get a comprehensive summary of user's memory"""
        try:
            db = await get_db_session()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get memory counts by type
            memory_counts = db.query(
                UserMemory.type,
                func.count(UserMemory.id).label('count'),
                func.avg(UserMemory.importance_score).label('avg_importance')
            ).filter(
                and_(
                    UserMemory.user_id == user_id,
                    UserMemory.timestamp >= cutoff_date,
                    UserMemory.is_active == True
                )
            ).group_by(UserMemory.type).all()
            
            # Get top memories by importance
            top_memories = db.query(UserMemory).filter(
                and_(
                    UserMemory.user_id == user_id,
                    UserMemory.timestamp >= cutoff_date,
                    UserMemory.is_active == True
                )
            ).order_by(desc(UserMemory.importance_score)).limit(10).all()
            
            # Get relationship count
            relationship_count = db.query(func.count(RelationshipGraph.id)).filter(
                RelationshipGraph.user_id == user_id
            ).scalar() or 0
            
            return {
                "period_days": days,
                "total_memories": sum(count.count for count in memory_counts),
                "memory_by_type": {count.type: {"count": count.count, "avg_importance": float(count.avg_importance or 0)} for count in memory_counts},
                "top_memories": [self._memory_to_dict(memory) for memory in top_memories],
                "relationship_count": relationship_count,
                "summary_generated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting memory summary: {e}")
            return {"error": str(e)}
    
    async def get_recent_context(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent context for user (last 24 hours)"""
        try:
            # Try Redis first for speed
            if self.redis_client:
                redis_key = f"recent_context:{user_id}"
                recent_data = await self.redis_client.lrange(redis_key, 0, limit - 1)
                
                if recent_data:
                    return [json.loads(data) for data in recent_data]
            
            # Fallback to database
            return await self.recall_memory(user_id, limit=limit, hours_back=24)
            
        except Exception as e:
            logger.error(f"Error getting recent context: {e}")
            return []
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences and style profile"""
        try:
            db = await get_db_session()
            
            # Get style profile
            style_profile = db.query(UserStyleProfile).filter(
                UserStyleProfile.user_id == user_id
            ).first()
            
            # Get preferences
            preferences = db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).all()
            
            # Get habits
            habits = db.query(UserHabit).filter(
                and_(
                    UserHabit.user_id == user_id,
                    UserHabit.is_active == True
                )
            ).all()
            
            result = {
                "style_profile": self._style_profile_to_dict(style_profile) if style_profile else {},
                "preferences": {pref.preference_key: pref.preference_value for pref in preferences},
                "habits": [self._habit_to_dict(habit) for habit in habits],
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}
    
    async def set_user_preference(self, user_id: str, key: str, value: Any) -> bool:
        """Set a user preference"""
        try:
            db = await get_db_session()
            
            # Check if preference exists
            existing = db.query(UserPreference).filter(
                and_(
                    UserPreference.user_id == user_id,
                    UserPreference.preference_key == key
                )
            ).first()
            
            if existing:
                existing.preference_value = value
                existing.updated_at = datetime.utcnow()
            else:
                new_pref = UserPreference(
                    user_id=user_id,
                    preference_key=key,
                    preference_value=value
                )
                db.add(new_pref)
            
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error setting user preference: {e}")
            return False
    
    async def update_style_profile(
        self, 
        user_id: str, 
        style_data: Dict[str, Any]
    ) -> bool:
        """Update user's style profile"""
        try:
            db = await get_db_session()
            
            # Get or create style profile
            profile = db.query(UserStyleProfile).filter(
                UserStyleProfile.user_id == user_id
            ).first()
            
            if profile:
                # Update existing profile
                for key, value in style_data.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                profile.updated_at = datetime.utcnow()
            else:
                # Create new profile
                profile = UserStyleProfile(
                    user_id=user_id,
                    **style_data
                )
                db.add(profile)
            
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating style profile: {e}")
            return False
    
    async def forget_memory(self, user_id: str, memory_id: int) -> bool:
        """Forget a specific memory (soft delete)"""
        try:
            db = await get_db_session()
            
            memory = db.query(UserMemory).filter(
                and_(
                    UserMemory.id == memory_id,
                    UserMemory.user_id == user_id
                )
            ).first()
            
            if memory:
                memory.is_active = False
                await db.commit()
                
                # Remove from Redis cache
                if self.redis_client:
                    redis_key = f"recent_context:{user_id}"
                    await self.redis_client.lrem(redis_key, 0, json.dumps(self._memory_to_dict(memory)))
                
                logger.info(f"Memory {memory_id} forgotten for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error forgetting memory: {e}")
            return False
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using OpenAI"""
        try:
            if not self.openai_client:
                return None
            
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def _store_recent_context(
        self, 
        user_id: str, 
        memory_type: str, 
        content: str, 
        memory_id: int
    ):
        """Store recent context in Redis for fast access"""
        try:
            if not self.redis_client:
                return
            
            redis_key = f"recent_context:{user_id}"
            context_data = {
                "id": memory_id,
                "type": memory_type,
                "content": content[:200],  # Truncate for Redis
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add to list (newest first)
            await self.redis_client.lpush(redis_key, json.dumps(context_data))
            
            # Keep only last MAX_CONTEXT_ITEMS
            await self.redis_client.ltrim(redis_key, 0, MAX_CONTEXT_ITEMS - 1)
            
            # Set expiration
            await self.redis_client.expire(redis_key, CACHE_TTL)
            
        except Exception as e:
            logger.error(f"Error storing recent context in Redis: {e}")
    
    async def _update_relationship_graph(
        self, 
        user_id: str, 
        memory_id: int, 
        related_memory_ids: List[int]
    ):
        """Update relationship graph when new memories are added"""
        try:
            db = await get_db_session()
            
            for related_id in related_memory_ids:
                # Create bidirectional relationship
                relationship = RelationshipGraph(
                    user_id=user_id,
                    entity1_type="memory",
                    entity1_id=str(memory_id),
                    entity2_type="memory",
                    entity2_id=str(related_id),
                    relationship_type="related_to",
                    strength=0.8,
                    context={"source": "memory_creation"}
                )
                db.add(relationship)
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error updating relationship graph: {e}")
    
    async def _schedule_smart_reminder(self, user_id: int, memory_id: int, content: str, importance_score: float):
        """
        Schedule a smart reminder based on urgency analysis and user context
        
        Args:
            user_id: User identifier
            memory_id: Memory ID to remind about
            content: Memory content for analysis
            importance_score: Importance score for timing
        """
        try:
            # Analyze urgency and context
            urgency_level = await self._analyze_urgency(content, importance_score)
            reminder_hours = await self._calculate_reminder_timing(urgency_level, content)
            
            # Schedule the reminder
            from services.proactive_agent import proactive_agent
            await proactive_agent.schedule_memory_reminder(
                user_id=user_id,
                memory_id=memory_id,
                content=content,
                hours_from_now=reminder_hours,
                urgency_level=urgency_level
            )
            
            logger.info(f"Scheduled smart reminder for user {user_id}, memory {memory_id} in {reminder_hours} hours")
            
        except Exception as e:
            logger.error(f"Error scheduling smart reminder: {e}")

    async def _analyze_urgency(self, content: str, importance_score: float) -> str:
        """
        Analyze the urgency level of a memory based on content and importance
        
        Returns:
            urgency_level: "critical", "high", "medium", "low"
        """
        try:
            # Keywords that indicate urgency
            critical_keywords = ["urgent", "emergency", "asap", "immediately", "now", "critical", "deadline", "due today"]
            high_keywords = ["important", "soon", "today", "this afternoon", "this evening", "priority"]
            medium_keywords = ["tomorrow", "this week", "soon", "when you can", "sometime"]
            
            content_lower = content.lower()
            
            # Check for critical urgency
            if any(keyword in content_lower for keyword in critical_keywords):
                return "critical"
            
            # Check for high urgency
            if any(keyword in content_lower for keyword in high_keywords):
                return "high"
            
            # Check for medium urgency
            if any(keyword in content_lower for keyword in medium_keywords):
                return "medium"
            
            # Default based on importance score
            if importance_score >= 0.8:
                return "high"
            elif importance_score >= 0.5:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"Error analyzing urgency: {e}")
            return "medium"

    async def _calculate_reminder_timing(self, urgency_level: str, content: str) -> int:
        """
        Calculate when to send the reminder based on urgency level
        
        Returns:
            hours_from_now: When to send the reminder
        """
        try:
            # Base timing by urgency level
            base_timing = {
                "critical": 1,    # 1 hour
                "high": 3,        # 3 hours  
                "medium": 6,      # 6 hours
                "low": 12         # 12 hours
            }
            
            hours = base_timing.get(urgency_level, 6)
            
            # Adjust based on time-sensitive keywords
            content_lower = content.lower()
            
            # Time-specific adjustments
            if "morning" in content_lower or "breakfast" in content_lower:
                hours = max(1, hours - 2)  # Earlier for morning tasks
            elif "evening" in content_lower or "dinner" in content_lower:
                hours = min(24, hours + 2)  # Later for evening tasks
            elif "tomorrow" in content_lower:
                hours = 24  # Tomorrow = 24 hours
            elif "next week" in content_lower:
                hours = 168  # Next week = 7 days
            elif "this afternoon" in content_lower:
                hours = 4   # This afternoon = 4 hours
            elif "tonight" in content_lower:
                hours = 8   # Tonight = 8 hours
            
            return hours
            
        except Exception as e:
            logger.error(f"Error calculating reminder timing: {e}")
            return 6  # Default to 6 hours

    async def _update_importance_scores(self, user_id: str, memory_id: int):
        """Update importance scores based on relationships"""
        try:
            db = await get_db_session()
            
            # Get relationships for this memory
            relationships = db.query(RelationshipGraph).filter(
                or_(
                    and_(
                        RelationshipGraph.user_id == user_id,
                        RelationshipGraph.entity1_id == str(memory_id)
                    ),
                    and_(
                        RelationshipGraph.user_id == user_id,
                        RelationshipGraph.entity2_id == str(memory_id)
                    )
                )
            ).all()
            
            if relationships:
                # Increase importance based on number of relationships
                importance_boost = min(0.3, len(relationships) * 0.1)
                
                memory = db.query(UserMemory).filter(
                    and_(
                        UserMemory.id == memory_id,
                        UserMemory.user_id == user_id
                    )
                ).first()
                
                if memory:
                    memory.importance_score = min(1.0, memory.importance_score + importance_boost)
                    await db.commit()
            
        except Exception as e:
            logger.error(f"Error updating importance scores: {e}")
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            if len(vec1) != len(vec2):
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _memory_to_dict(self, memory: UserMemory) -> Dict[str, Any]:
        """Convert memory object to dictionary"""
        return {
            "id": memory.id,
            "user_id": memory.user_id,
            "timestamp": memory.timestamp.isoformat() if memory.timestamp else None,
            "type": memory.type,
            "content": memory.content,
            "context_data": memory.context_data or {},
            "related_memories": memory.related_memories or [],
            "importance_score": memory.importance_score,
            "is_active": memory.is_active
        }
    
    def _style_profile_to_dict(self, profile: UserStyleProfile) -> Dict[str, Any]:
        """Convert style profile to dictionary"""
        if not profile:
            return {}
        
        return {
            "emoji_usage": profile.emoji_usage,
            "formality_level": profile.formality_level,
            "avg_message_length": profile.avg_message_length,
            "signature_phrases": profile.signature_phrases or [],
            "tone_preferences": profile.tone_preferences or {},
            "communication_style": profile.communication_style
        }
    
    def _habit_to_dict(self, habit: UserHabit) -> Dict[str, Any]:
        """Convert habit to dictionary"""
        return {
            "id": habit.id,
            "pattern_type": habit.pattern_type,
            "pattern_data": habit.pattern_data,
            "confidence": habit.confidence,
            "last_observed": habit.last_observed.isoformat() if habit.last_observed else None,
            "observation_count": habit.observation_count,
            "next_predicted": habit.next_predicted.isoformat() if habit.next_predicted else None,
            "proactive_suggestions": habit.proactive_suggestions or []
        }
    
    def _get_current_timestamp(self) -> datetime:
        """Get current timestamp in UTC"""
        return datetime.utcnow()


# Global memory manager instance
memory_manager = MemoryManager()
