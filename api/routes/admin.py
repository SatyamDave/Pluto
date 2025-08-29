"""
Admin routes for Pluto AI Phone Assistant
Provides debugging and visibility into user context, memory, and system state
"""

import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User, UserMemory, UserHabit, UserPreference, ProactiveTask
from services.memory_manager import memory_manager
from services.habit_engine import habit_engine
from services.proactive_agent import proactive_agent
from services.user_manager import user_manager
from config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin_token(token: str = Query(..., description="Admin access token")) -> bool:
    """Verify admin access token"""
    if not settings.ADMIN_TOKEN:
        raise HTTPException(status_code=500, detail="Admin token not configured")
    
    if token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    return True


@router.get("/users/{user_id}/context", response_class=HTMLResponse)
async def get_user_context_html(
    user_id: str,
    token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Get user context in HTML format for debugging"""
    try:
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user memory summary
        memory_summary = await memory_manager.get_memory_summary(user_id)
        
        # Get user habits
        habits = await habit_engine.get_user_habits(user_id)
        
        # Get user preferences
        preferences = await memory_manager.get_user_preferences(user_id)
        
        # Get proactive tasks
        proactive_tasks = await proactive_agent.get_user_proactive_tasks(user_id)
        
        # Generate HTML response
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pluto Admin - User Context</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .section h3 {{ margin-top: 0; color: #333; }}
                .memory-item {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 3px; }}
                .habit-item {{ margin: 8px 0; padding: 8px; background: #e8f4fd; border-radius: 3px; }}
                .preference-item {{ margin: 8px 0; padding: 8px; background: #f0f8f0; border-radius: 3px; }}
                .task-item {{ margin: 8px 0; padding: 8px; background: #fff3cd; border-radius: 3px; }}
                .timestamp {{ color: #666; font-size: 0.9em; }}
                .error {{ color: #d32f2f; }}
                .success {{ color: #388e3c; }}
            </style>
        </head>
        <body>
            <h1>Pluto Admin - User Context</h1>
            <div class="section">
                <h3>User Information</h3>
                <p><strong>ID:</strong> {user.id}</p>
                <p><strong>Phone:</strong> {user.phone_number}</p>
                <p><strong>Status:</strong> {user.status}</p>
                <p><strong>Created:</strong> {user.created_at}</p>
                <p><strong>Last Active:</strong> {user.last_active}</p>
            </div>
            
            <div class="section">
                <h3>Memory Summary</h3>
                <div class="memory-item">
                    <strong>Total Memories:</strong> {memory_summary.get('total_count', 'N/A')}<br>
                    <strong>Recent Memories:</strong> {memory_summary.get('recent_count', 'N/A')}<br>
                    <strong>Memory Types:</strong> {', '.join(memory_summary.get('type_breakdown', {}).keys()) if memory_summary.get('type_breakdown') else 'N/A'}
                </div>
            </div>
            
            <div class="section">
                <h3>User Habits ({len(habits)} detected)</h3>
                {''.join([f'<div class="habit-item"><strong>{habit.get("pattern_type", "Unknown")}:</strong> {habit.get("description", "No description")} (Confidence: {habit.get("confidence", 0):.2f})</div>' for habit in habits])}
            </div>
            
            <div class="section">
                <h3>User Preferences ({len(preferences)} set)</h3>
                {''.join([f'<div class="preference-item"><strong>{key}:</strong> {value}</div>' for key, value in preferences.items()])}
            </div>
            
            <div class="section">
                <h3>Proactive Tasks ({len(proactive_tasks)} scheduled)</h3>
                {''.join([f'<div class="task-item"><strong>{task.get("task_type", "Unknown")}:</strong> {task.get("description", "No description")} - Next: {task.get("next_run", "Unknown")}</div>' for task in proactive_tasks])}
            </div>
            
            <div class="section">
                <h3>Quick Actions</h3>
                <button onclick="location.reload()">Refresh Data</button>
                <button onclick="window.print()">Print Report</button>
                <button onclick="window.history.back()">Go Back</button>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error - Pluto Admin</title></head>
        <body>
            <h1>Error Loading User Context</h1>
            <p class="error">{str(e)}</p>
            <button onclick="window.history.back()">Go Back</button>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)


@router.get("/users/{user_id}/context.json")
async def get_user_context_json(
    user_id: str,
    token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Get user context in JSON format for API consumption"""
    try:
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user memory summary
        memory_summary = await memory_manager.get_memory_summary(user_id)
        
        # Get user habits
        habits = await habit_engine.get_user_habits(user_id)
        
        # Get user preferences
        preferences = await memory_manager.get_user_preferences(user_id)
        
        # Get proactive tasks
        proactive_tasks = await proactive_agent.get_user_proactive_tasks(user_id)
        
        # Get recent memories
        recent_memories = await memory_manager.recall_memory(
            user_id=user_id,
            limit=20,
            hours_back=24
        )
        
        context_data = {
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "status": user.status,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_active": user.last_active.isoformat() if user.last_active else None
            },
            "memory": {
                "summary": memory_summary,
                "recent_memories": recent_memories
            },
            "habits": habits,
            "preferences": preferences,
            "proactive_tasks": proactive_tasks,
            "generated_at": memory_manager._get_current_timestamp().isoformat()
        }
        
        return JSONResponse(content=context_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading user context: {str(e)}")


@router.get("/users")
async def list_users(
    token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db),
    limit: int = Query(100, description="Maximum number of users to return"),
    offset: int = Query(0, description="Number of users to skip")
):
    """List all users with basic information"""
    try:
        users = db.query(User).offset(offset).limit(limit).all()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "phone_number": user.phone_number,
                "status": user.status,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_active": user.last_active.isoformat() if user.last_active else None
            })
        
        return {
            "users": user_list,
            "total": len(user_list),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")


@router.get("/system/status")
async def get_system_status(
    token: str = Depends(verify_admin_token)
):
    """Get overall system status and health"""
    try:
        # Get basic system information
        system_status = {
            "status": "operational",
            "timestamp": memory_manager._get_current_timestamp().isoformat(),
            "version": "1.0.0",
            "services": {
                "memory_manager": "operational",
                "habit_engine": "operational",
                "proactive_agent": "operational",
                "user_manager": "operational"
            }
        }
        
        # Check service health (simplified)
        try:
            await memory_manager.get_memory_summary("test")
            system_status["services"]["memory_manager"] = "operational"
        except:
            system_status["services"]["memory_manager"] = "degraded"
        
        try:
            await habit_engine.get_user_habits("test")
            system_status["services"]["habit_engine"] = "operational"
        except:
            system_status["services"]["habit_engine"] = "degraded"
        
        # Overall status
        if any(status == "degraded" for status in system_status["services"].values()):
            system_status["status"] = "degraded"
        
        return system_status
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": memory_manager._get_current_timestamp().isoformat()
        }


@router.delete("/users/{user_id}/memory/{memory_id}")
async def delete_user_memory(
    user_id: str,
    memory_id: int,
    token: str = Depends(verify_admin_token)
):
    """Delete a specific user memory (admin only)"""
    try:
        result = await memory_manager.forget_memory(user_id, memory_id)
        
        if result:
            return {"message": "Memory deleted successfully", "memory_id": memory_id}
        else:
            raise HTTPException(status_code=404, detail="Memory not found or already deleted")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting memory: {str(e)}")


@router.post("/users/{user_id}/reset")
async def reset_user_data(
    user_id: str,
    token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Reset all user data (admin only - use with caution)"""
    try:
        # This is a dangerous operation - should have additional confirmation
        # For now, just return a warning
        return {
            "warning": "This operation would delete all user data. Not implemented for safety.",
            "user_id": user_id,
            "message": "Use individual deletion endpoints instead"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting user data: {str(e)}")
