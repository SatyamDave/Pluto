"""
Notes service for Jarvis Phone AI Assistant
Manages user notes, todos, and lists
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from db.database import get_db
from db.models import Note, User

logger = logging.getLogger(__name__)


class NotesService:
    """Service for managing user notes and todos"""
    
    def __init__(self):
        """Initialize the notes service"""
        self.logger = logger
        self.logger.info("Notes service initialized")
    
    async def create_note(
        self,
        user_id: int,
        title: str,
        content: Optional[str] = None,
        note_type: str = "note",
        priority: str = "medium",
        tags: Optional[List[str]] = None
    ) -> Note:
        """Create a new note or todo"""
        try:
            db = await get_db()
            
            # Create note record
            note = Note(
                user_id=user_id,
                title=title,
                content=content,
                note_type=note_type,
                priority=priority,
                tags=tags or [],
                is_completed=False
            )
            
            db.add(note)
            await db.commit()
            await db.refresh(note)
            
            logger.info(f"Created {note_type} '{title}' for user {user_id}")
            return note
            
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            raise
    
    async def get_user_notes(
        self, 
        user_id: int, 
        note_type: Optional[str] = None,
        include_completed: bool = False,
        limit: int = 50
    ) -> List[Note]:
        """Get notes for a user with optional filtering"""
        try:
            db = await get_db()
            
            query = select(Note).where(Note.user_id == user_id)
            
            if note_type:
                query = query.where(Note.note_type == note_type)
            
            if not include_completed:
                query = query.where(Note.is_completed == False)
            
            query = query.order_by(Note.created_at.desc()).limit(limit)
            
            result = await db.execute(query)
            notes = result.scalars().all()
            
            return notes
            
        except Exception as e:
            logger.error(f"Error getting user notes: {e}")
            raise
    
    async def search_notes(
        self, 
        user_id: int, 
        search_term: str,
        note_type: Optional[str] = None
    ) -> List[Note]:
        """Search notes by title or content"""
        try:
            db = await get_db()
            
            query = select(Note).where(
                and_(
                    Note.user_id == user_id,
                    or_(
                        Note.title.ilike(f"%{search_term}%"),
                        Note.content.ilike(f"%{search_term}%")
                    )
                )
            )
            
            if note_type:
                query = query.where(Note.note_type == note_type)
            
            query = query.order_by(Note.created_at.desc())
            
            result = await db.execute(query)
            notes = result.scalars().all()
            
            logger.info(f"Found {len(notes)} notes matching '{search_term}' for user {user_id}")
            return notes
            
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            raise
    
    async def get_notes_by_tag(self, user_id: int, tag: str) -> List[Note]:
        """Get notes by specific tag"""
        try:
            db = await get_db()
            
            # Note: This is a simplified search. In production with PostgreSQL,
            # you'd want to use proper JSON operators for better performance
            query = select(Note).where(
                and_(
                    Note.user_id == user_id,
                    Note.tags.contains([tag])
                )
            )
            
            result = await db.execute(query)
            notes = result.scalars().all()
            
            return notes
            
        except Exception as e:
            logger.error(f"Error getting notes by tag: {e}")
            raise
    
    async def update_note(
        self, 
        note_id: int, 
        user_id: int,
        **kwargs
    ) -> Optional[Note]:
        """Update a note"""
        try:
            db = await get_db()
            
            query = select(Note).where(
                and_(
                    Note.id == note_id,
                    Note.user_id == user_id
                )
            )
            
            result = await db.execute(query)
            note = result.scalar_one_or_none()
            
            if note:
                for key, value in kwargs.items():
                    if hasattr(note, key):
                        setattr(note, key, value)
                
                note.updated_at = datetime.utcnow()
                await db.commit()
                await db.refresh(note)
                
                logger.info(f"Updated note {note_id} for user {user_id}")
                return note
            else:
                logger.warning(f"Note {note_id} not found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating note: {e}")
            raise
    
    async def mark_note_completed(self, note_id: int, user_id: int) -> bool:
        """Mark a note as completed"""
        try:
            db = await get_db()
            
            query = select(Note).where(
                and_(
                    Note.id == note_id,
                    Note.user_id == user_id
                )
            )
            
            result = await db.execute(query)
            note = result.scalar_one_or_none()
            
            if note:
                note.is_completed = True
                note.updated_at = datetime.utcnow()
                await db.commit()
                
                logger.info(f"Marked note {note_id} as completed for user {user_id}")
                return True
            else:
                logger.warning(f"Note {note_id} not found for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error marking note completed: {e}")
            raise
    
    async def delete_note(self, note_id: int, user_id: int) -> bool:
        """Delete a note"""
        try:
            db = await get_db()
            
            query = select(Note).where(
                and_(
                    Note.id == note_id,
                    Note.user_id == user_id
                )
            )
            
            result = await db.execute(query)
            note = result.scalar_one_or_none()
            
            if note:
                await db.delete(note)
                await db.commit()
                
                logger.info(f"Deleted note {note_id} for user {user_id}")
                return True
            else:
                logger.warning(f"Note {note_id} not found for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting note: {e}")
            raise
    
    async def get_notes_analytics(self, user_id: int) -> Dict[str, Any]:
        """Get analytics about user's notes"""
        try:
            db = await get_db()
            
            # Get note counts by type
            type_query = """
                SELECT note_type, COUNT(*) as count
                FROM notes 
                WHERE user_id = :user_id
                GROUP BY note_type
            """
            
            result = await db.execute(type_query, {"user_id": user_id})
            type_counts = {row.note_type: row.count for row in result.fetchall()}
            
            # Get completion rates
            completion_query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN is_completed = true THEN 1 END) as completed
                FROM notes 
                WHERE user_id = :user_id
            """
            
            result = await db.execute(completion_query, {"user_id": user_id})
            completion_stats = result.fetchone()
            
            # Get priority distribution
            priority_query = """
                SELECT priority, COUNT(*) as count
                FROM notes 
                WHERE user_id = :user_id
                GROUP BY priority
            """
            
            result = await db.execute(priority_query, {"user_id": user_id})
            priority_counts = {row.priority: row.count for row in result.fetchall()}
            
            # Get recent activity
            recent_query = """
                SELECT COUNT(*) as count
                FROM notes 
                WHERE user_id = :user_id 
                AND created_at >= NOW() - INTERVAL '7 days'
            """
            
            result = await db.execute(recent_query, {"user_id": user_id})
            recent_count = result.fetchone().count
            
            return {
                "total_notes": completion_stats.total,
                "completed_notes": completion_stats.completed,
                "completion_rate": (completion_stats.completed / completion_stats.total * 100) if completion_stats.total > 0 else 0,
                "notes_by_type": type_counts,
                "notes_by_priority": priority_counts,
                "recent_notes": recent_count,
                "total_tags": await self._get_total_tags_count(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting notes analytics: {e}")
            return {"error": str(e)}
    
    async def _get_total_tags_count(self, user_id: int) -> int:
        """Get total number of unique tags used by user"""
        try:
            db = await get_db()
            
            # This is a simplified approach. In production with PostgreSQL,
            # you'd want to use proper JSON aggregation functions
            query = "SELECT tags FROM notes WHERE user_id = :user_id AND tags IS NOT NULL"
            result = await db.execute(query, {"user_id": user_id})
            
            all_tags = set()
            for row in result.fetchall():
                if row.tags:
                    all_tags.update(row.tags)
            
            return len(all_tags)
            
        except Exception as e:
            logger.error(f"Error getting tags count: {e}")
            return 0
    
    async def create_shopping_list(self, user_id: int, items: List[str]) -> Note:
        """Create a shopping list from items"""
        try:
            # Create a list note with items as content
            content = "\n".join([f"• {item}" for item in items])
            
            note = await self.create_note(
                user_id=user_id,
                title="Shopping List",
                content=content,
                note_type="list",
                priority="medium",
                tags=["shopping", "list"]
            )
            
            logger.info(f"Created shopping list with {len(items)} items for user {user_id}")
            return note
            
        except Exception as e:
            logger.error(f"Error creating shopping list: {e}")
            raise
    
    async def add_item_to_list(self, note_id: int, user_id: int, item: str) -> bool:
        """Add an item to an existing list"""
        try:
            db = await get_db()
            
            query = select(Note).where(
                and_(
                    Note.id == note_id,
                    Note.user_id == user_id,
                    Note.note_type == "list"
                )
            )
            
            result = await db.execute(query)
            note = result.scalar_one_or_none()
            
            if note:
                # Add new item to content
                current_content = note.content or ""
                new_content = current_content + f"\n• {item}"
                
                note.content = new_content
                note.updated_at = datetime.utcnow()
                
                await db.commit()
                
                logger.info(f"Added item '{item}' to list {note_id}")
                return True
            else:
                logger.warning(f"List {note_id} not found for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding item to list: {e}")
            raise
