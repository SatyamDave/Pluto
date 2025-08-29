"""
Notes API routes for Jarvis Phone AI Assistant
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from notes.notes_service import NotesService

logger = logging.getLogger(__name__)
router = APIRouter()


class NoteCreate(BaseModel):
    """Create note request model"""
    title: str
    content: Optional[str] = None
    note_type: str = "note"
    priority: str = "medium"
    tags: Optional[List[str]] = None


class NoteUpdate(BaseModel):
    """Update note request model"""
    title: Optional[str] = None
    content: Optional[str] = None
    note_type: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteResponse(BaseModel):
    """Note response model"""
    id: int
    title: str
    content: Optional[str]
    note_type: str
    is_completed: bool
    priority: str
    tags: List[str]
    created_at: str
    updated_at: str


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Create a new note"""
    try:
        service = NotesService()
        note = await service.create_note(
            user_id=user_id,
            title=note_data.title,
            content=note_data.content,
            note_type=note_data.note_type,
            priority=note_data.priority,
            tags=note_data.tags
        )
        
        return NoteResponse(
            id=note.id,
            title=note.title,
            content=note.content,
            note_type=note.note_type,
            is_completed=note.is_completed,
            priority=note.priority,
            tags=note.tags,
            created_at=note.created_at.isoformat(),
            updated_at=note.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail="Failed to create note")


@router.get("/{user_id}", response_model=List[NoteResponse])
async def get_user_notes(
    user_id: int,
    note_type: Optional[str] = None,
    include_completed: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get notes for a user"""
    try:
        service = NotesService()
        notes = await service.get_user_notes(
            user_id=user_id,
            note_type=note_type,
            include_completed=include_completed,
            limit=limit
        )
        
        return [
            NoteResponse(
                id=note.id,
                title=note.title,
                content=note.content,
                note_type=note.note_type,
                is_completed=note.is_completed,
                priority=note.priority,
                tags=note.tags,
                created_at=note.created_at.isoformat(),
                updated_at=note.updated_at.isoformat()
            )
            for note in notes
        ]
        
    except Exception as e:
        logger.error(f"Error getting notes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notes")


@router.get("/{user_id}/search")
async def search_notes(
    user_id: int,
    q: str,
    note_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Search notes by title or content"""
    try:
        service = NotesService()
        notes = await service.search_notes(
            user_id=user_id,
            search_term=q,
            note_type=note_type
        )
        
        return {
            "user_id": user_id,
            "search_term": q,
            "results_count": len(notes),
            "notes": [
                {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "note_type": note.note_type,
                    "is_completed": note.is_completed,
                    "priority": note.priority,
                    "tags": note.tags,
                    "created_at": note.created_at.isoformat()
                }
                for note in notes
            ]
        }
        
    except Exception as e:
        logger.error(f"Error searching notes: {e}")
        raise HTTPException(status_code=500, detail="Failed to search notes")


@router.get("/{user_id}/tag/{tag}")
async def get_notes_by_tag(
    user_id: int,
    tag: str,
    db: AsyncSession = Depends(get_db)
):
    """Get notes by specific tag"""
    try:
        service = NotesService()
        notes = await service.get_notes_by_tag(user_id, tag)
        
        return {
            "user_id": user_id,
            "tag": tag,
            "notes_count": len(notes),
            "notes": [
                {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "note_type": note.note_type,
                    "is_completed": note.is_completed,
                    "priority": note.priority,
                    "tags": note.tags,
                    "created_at": note.created_at.isoformat()
                }
                for note in notes
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting notes by tag: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notes by tag")


@router.put("/{note_id}")
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Update a note"""
    try:
        service = NotesService()
        
        # Prepare update data
        update_data = {}
        if note_data.title is not None:
            update_data['title'] = note_data.title
        if note_data.content is not None:
            update_data['content'] = note_data.content
        if note_data.note_type is not None:
            update_data['note_type'] = note_data.note_type
        if note_data.priority is not None:
            update_data['priority'] = note_data.priority
        if note_data.tags is not None:
            update_data['tags'] = note_data.tags
        
        note = await service.update_note(
            note_id=note_id,
            user_id=user_id,
            **update_data
        )
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {"message": "Note updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating note: {e}")
        raise HTTPException(status_code=500, detail="Failed to update note")


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Delete a note"""
    try:
        service = NotesService()
        success = await service.delete_note(note_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {"message": "Note deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete note")


@router.post("/{note_id}/complete")
async def mark_note_completed(
    note_id: int,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Mark a note as completed"""
    try:
        service = NotesService()
        success = await service.mark_note_completed(note_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {"message": "Note marked as completed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking note completed: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark note completed")


@router.post("/{user_id}/shopping-list")
async def create_shopping_list(
    user_id: int,
    items: List[str],
    db: AsyncSession = Depends(get_db)
):
    """Create a shopping list"""
    try:
        service = NotesService()
        note = await service.create_shopping_list(user_id, items)
        
        return {
            "message": "Shopping list created successfully",
            "note_id": note.id,
            "items_count": len(items)
        }
        
    except Exception as e:
        logger.error(f"Error creating shopping list: {e}")
        raise HTTPException(status_code=500, detail="Failed to create shopping list")


@router.get("/{user_id}/analytics")
async def get_notes_analytics(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get notes analytics for a user"""
    try:
        service = NotesService()
        analytics = await service.get_notes_analytics(user_id)
        
        if "error" in analytics:
            raise HTTPException(status_code=400, detail=analytics["error"])
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notes analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notes analytics")
