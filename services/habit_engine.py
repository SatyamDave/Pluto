#!/usr/bin/env python3
"""
Pluto Habit Learning Engine
Detects user patterns and suggests proactive actions with enhanced memory integration
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from collections import defaultdict

from db.database import get_db
from db.models import UserMemory, UserHabit, ProactiveTask
from services.memory_manager import memory_manager
from utils.logging_config import get_logger
from utils.constants import HABIT_CONFIDENCE_THRESHOLD

logger = get_logger(__name__)

class HabitEngine:
    """Pluto's habit learning engine - learns patterns and suggests proactive actions"""
    
    def __init__(self):
        self.pattern_detectors = {
            "time_based": self._detect_time_patterns,
            "frequency_based": self._detect_frequency_patterns,
            "context_based": self._detect_context_patterns,
            "sequence_based": self._detect_sequence_patterns
        }
        
        self.habit_categories = {
            "communication": ["sms", "email", "call"],
            "productivity": ["reminder", "calendar", "note"],
            "lifestyle": ["wake_up", "exercise", "meal", "sleep"],
            "work": ["meeting", "task", "deadline", "break"]
        }
    
    async def analyze_user_habits(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Analyze user's memory to detect habits
        
        Args:
            user_id: User identifier
            
        Returns:
            List of detected habits
        """
        try:
            # Get recent memories (last 30 days)
            memories = await memory_manager.recall_memory(
                user_id=user_id,
                hours_back=24 * 30,
                limit=1000
            )
            
            if not memories:
                return []
            
            # Detect different types of patterns
            habits = []
            
            # Time-based patterns
            time_habits = await self._detect_time_patterns(user_id, memories)
            habits.extend(time_habits)
            
            # Frequency-based patterns
            freq_habits = await self._detect_frequency_patterns(user_id, memories)
            habits.extend(freq_habits)
            
            # Context-based patterns
            context_habits = await self._detect_context_patterns(user_id, memories)
            habits.extend(context_habits)
            
            # Sequence-based patterns
            sequence_habits = await self._detect_sequence_patterns(user_id, memories)
            habits.extend(sequence_habits)
            
            # Store detected habits
            await self._store_habits(user_id, habits)
            
            # Update habit predictions
            await self._update_habit_predictions(user_id, habits)
            
            return habits
            
        except Exception as e:
            logger.error(f"Error analyzing user habits: {e}")
            return []
    
    async def get_user_habits(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's current habits"""
        try:
            db = await anext(get_db())
            
            habits = db.query(UserHabit).filter(
                and_(
                    UserHabit.user_id == user_id,
                    UserHabit.is_active == True
                )
            ).order_by(desc(UserHabit.confidence)).all()
            
            return [self._habit_to_dict(habit) for habit in habits]
            
        except Exception as e:
            logger.error(f"Error getting user habits: {e}")
            return []
    
    async def suggest_proactive_actions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get proactive suggestions based on user habits
        
        Args:
            user_id: User identifier
            
        Returns:
            List of proactive action suggestions
        """
        try:
            habits = await self.get_user_habits(user_id)
            suggestions = []
            
            current_time = datetime.utcnow()
            
            for habit in habits:
                # Check if habit is due soon
                if habit.get('next_predicted'):
                    next_time = datetime.fromisoformat(habit['next_predicted'])
                    time_until = (next_time - current_time).total_seconds() / 3600  # hours
                    
                    if 0 <= time_until <= 4:  # Due within 4 hours
                        suggestion = await self._generate_habit_suggestion(habit, time_until)
                        if suggestion:
                            suggestions.append(suggestion)
                
                # Check for missed habits
                elif habit.get('last_observed'):
                    last_time = datetime.fromisoformat(habit['last_observed'])
                    hours_since = (current_time - last_time).total_seconds() / 3600
                    
                    # If habit is overdue by more than expected frequency
                    expected_frequency = habit.get('pattern_data', {}).get('frequency_hours', 24)
                    if hours_since > expected_frequency * 1.5:
                        suggestion = await self._generate_missed_habit_suggestion(habit, hours_since)
                        if suggestion:
                            suggestions.append(suggestion)
            
            # Sort by priority and confidence
            suggestions.sort(key=lambda x: (x.get('priority', 'medium'), x.get('confidence', 0)), reverse=True)
            
            return suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Error getting proactive suggestions: {e}")
            return []
    
    async def get_today_habits(self, user_id: str) -> List[Dict[str, Any]]:
        """Get habits that are due today"""
        try:
            habits = await self.get_user_habits(user_id)
            today_habits = []
            
            current_time = datetime.utcnow()
            today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            for habit in habits:
                if habit.get('next_predicted'):
                    next_time = datetime.fromisoformat(habit['next_predicted'])
                    if today_start <= next_time < today_end:
                        today_habits.append(habit)
            
            return today_habits
            
        except Exception as e:
            logger.error(f"Error getting today's habits: {e}")
            return []
    
    async def mark_habit_executed(self, user_id: str, habit_id: int) -> bool:
        """
        Mark a habit as executed
        
        Args:
            user_id: User identifier
            habit_id: Habit ID to mark as executed
            
        Returns:
            Success status
        """
        try:
            db = await anext(get_db())
            
            habit = db.query(UserHabit).filter(
                and_(
                    UserHabit.id == habit_id,
                    UserHabit.user_id == user_id
                )
            ).first()
            
            if habit:
                habit.last_observed = datetime.utcnow()
                habit.observation_count += 1
                
                # Update confidence based on more observations
                habit.confidence = min(0.95, habit.confidence + 0.05)
                
                # Predict next occurrence
                next_time = await self._predict_next_occurrence(habit)
                habit.next_predicted = next_time
                
                db.commit()
                
                # Store habit execution in memory
                await memory_manager.store_memory(
                    user_id=user_id,
                    memory_type="habit_executed",
                    content=f"Executed habit: {habit.pattern_data.get('action', 'habit')}",
                    metadata={
                        "habit_id": habit_id,
                        "pattern_type": habit.pattern_type,
                        "confidence": habit.confidence
                    },
                    importance_score=0.6
                )
                
                logger.info(f"Marked habit {habit_id} as executed for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking habit as executed: {e}")
            return False
    
    async def _detect_time_patterns(self, user_id: str, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect time-based patterns (e.g., wake up at 7AM on weekdays)"""
        try:
            time_patterns = defaultdict(list)
            
            # Group memories by type and extract time information
            for memory in memories:
                if memory.get("type") in ["reminder", "schedule", "habit", "sms"]:
                    content = memory.get("content", "").lower()
                    timestamp = memory.get("timestamp")
                    
                    # Extract time patterns
                    time_info = self._extract_time_from_content(content, timestamp)
                    if time_info:
                        key = f"{memory['type']}_{time_info['time_pattern']}"
                        time_patterns[key].append({
                            "content": memory["content"],
                            "timestamp": timestamp,
                            "time_info": time_info
                        })
            
            # Analyze patterns
            habits = []
            for pattern_key, occurrences in time_patterns.items():
                if len(occurrences) >= 3:  # Minimum 3 occurrences to consider a habit
                    pattern = self._analyze_time_pattern(occurrences)
                    if pattern:
                        habits.append({
                            "pattern_type": "time_based",
                            "pattern_data": pattern,
                            "confidence": min(0.9, len(occurrences) / 10.0),
                            "observations": len(occurrences)
                        })
            
            return habits
            
        except Exception as e:
            logger.error(f"Error detecting time patterns: {e}")
            return []
    
    async def _detect_frequency_patterns(self, user_id: str, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect frequency-based patterns (e.g., check email every 2 hours)"""
        try:
            frequency_patterns = defaultdict(list)
            
            # Group by memory type
            for memory in memories:
                memory_type = memory.get("type")
                if memory_type:
                    frequency_patterns[memory_type].append(memory.get("timestamp"))
            
            habits = []
            
            for memory_type, timestamps in frequency_patterns.items():
                if len(timestamps) >= 5:  # Need at least 5 occurrences
                    # Calculate time intervals
                    intervals = []
                    sorted_timestamps = sorted(timestamps)
                    
                    for i in range(1, len(sorted_timestamps)):
                        interval = (sorted_timestamps[i] - sorted_timestamps[i-1]).total_seconds() / 3600  # hours
                        intervals.append(interval)
                    
                    if intervals:
                        avg_interval = sum(intervals) / len(intervals)
                        consistency = self._calculate_consistency(intervals, avg_interval)
                        
                        if consistency > 0.6:  # Good consistency
                            habits.append({
                                "pattern_type": "frequency_based",
                                "pattern_data": {
                                    "memory_type": memory_type,
                                    "frequency_hours": round(avg_interval, 1),
                                    "consistency": consistency,
                                    "action": f"check {memory_type}"
                                },
                                "confidence": min(0.8, consistency),
                                "observations": len(timestamps)
                            })
            
            return habits
            
        except Exception as e:
            logger.error(f"Error detecting frequency patterns: {e}")
            return []
    
    async def _detect_context_patterns(self, user_id: str, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect context-based patterns (e.g., always set reminder after meeting)"""
        try:
            context_patterns = defaultdict(list)
            
            # Look for sequences of different memory types
            for i, memory in enumerate(memories):
                if i < len(memories) - 1:
                    current_type = memory.get("type")
                    next_type = memories[i + 1].get("type")
                    
                    if current_type and next_type and current_type != next_type:
                        pattern_key = f"{current_type}_then_{next_type}"
                        context_patterns[pattern_key].append({
                            "first": memory,
                            "second": memories[i + 1],
                            "time_gap": (memories[i + 1].get("timestamp") - memory.get("timestamp")).total_seconds() / 60  # minutes
                        })
            
            habits = []
            for pattern_key, occurrences in context_patterns.items():
                if len(occurrences) >= 3:  # Minimum 3 occurrences
                    avg_gap = sum(occ["time_gap"] for occ in occurrences) / len(occurrences)
                    
                    habits.append({
                        "pattern_type": "context_based",
                        "pattern_data": {
                            "trigger": pattern_key.split("_then_")[0],
                            "action": pattern_key.split("_then_")[1],
                            "avg_gap_minutes": round(avg_gap, 1),
                            "action": f"after {pattern_key.split('_then_')[0]}, do {pattern_key.split('_then_')[1]}"
                        },
                        "confidence": min(0.7, len(occurrences) / 8.0),
                        "observations": len(occurrences)
                    })
            
            return habits
            
        except Exception as e:
            logger.error(f"Error detecting context patterns: {e}")
            return []
    
    async def _detect_sequence_patterns(self, user_id: str, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect sequence patterns (e.g., morning routine: wake up -> check email -> set reminders)"""
        try:
            # Look for recurring sequences of 3+ actions
            sequence_patterns = defaultdict(list)
            
            # Check sequences of different lengths
            for seq_length in range(3, 6):  # 3 to 5 actions
                for i in range(len(memories) - seq_length + 1):
                    sequence = memories[i:i + seq_length]
                    sequence_types = [m.get("type") for m in sequence]
                    sequence_key = "_".join(sequence_types)
                    
                    sequence_patterns[sequence_key].append({
                        "sequence": sequence,
                        "start_time": sequence[0].get("timestamp"),
                        "end_time": sequence[-1].get("timestamp")
                    })
            
            habits = []
            for sequence_key, occurrences in sequence_patterns.items():
                if len(occurrences) >= 2:  # At least 2 occurrences
                    # Calculate average duration
                    durations = []
                    for occ in occurrences:
                        duration = (occ["end_time"] - occ["start_time"]).total_seconds() / 60  # minutes
                        durations.append(duration)
                    
                    avg_duration = sum(durations) / len(durations)
                    
                    habits.append({
                        "pattern_type": "sequence_based",
                        "pattern_data": {
                            "sequence": sequence_key.split("_"),
                            "avg_duration_minutes": round(avg_duration, 1),
                            "action": f"follow sequence: {' -> '.join(sequence_key.split('_'))}"
                        },
                        "confidence": min(0.6, len(occurrences) / 6.0),
                        "observations": len(occurrences)
                    })
            
            return habits
            
        except Exception as e:
            logger.error(f"Error detecting sequence patterns: {e}")
            return []
    
    def _extract_time_from_content(self, content: str, timestamp: datetime) -> Optional[Dict[str, Any]]:
        """Extract time information from content and timestamp"""
        try:
            content_lower = content.lower()
            
            # Look for specific times
            time_patterns = [
                r'(\d{1,2}):?(\d{2})\s*(am|pm)?',
                r'(\d{1,2})\s*(am|pm)',
                r'(\d{1,2})\s*o\'?clock'
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, content_lower)
                if match:
                    hour = int(match.group(1))
                    minute = int(match.group(2)) if match.group(2) else 0
                    
                    # Handle AM/PM
                    if 'pm' in content_lower and hour != 12:
                        hour += 12
                    elif 'am' in content_lower and hour == 12:
                        hour = 0
                    
                    # Create time object
                    time_obj = timestamp.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    return {
                        "time_pattern": f"{hour:02d}:{minute:02d}",
                        "hour": hour,
                        "minute": minute,
                        "time_obj": time_obj
                    }
            
            # Look for relative times
            if "morning" in content_lower:
                return {"time_pattern": "morning", "hour": 8, "minute": 0}
            elif "afternoon" in content_lower:
                return {"time_pattern": "afternoon", "hour": 14, "minute": 0}
            elif "evening" in content_lower:
                return {"time_pattern": "evening", "hour": 18, "minute": 0}
            elif "night" in content_lower:
                return {"time_pattern": "night", "hour": 22, "minute": 0}
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting time from content: {e}")
            return None
    
    def _analyze_time_pattern(self, occurrences: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze time pattern from occurrences"""
        try:
            if not occurrences:
                return None
            
            # Extract time information
            times = []
            for occ in occurrences:
                time_info = occ.get("time_info")
                if time_info and time_info.get("time_obj"):
                    times.append(time_info["time_obj"])
            
            if not times:
                return None
            
            # Calculate average time
            total_seconds = sum((t.hour * 3600 + t.minute * 60) for t in times)
            avg_seconds = total_seconds / len(times)
            avg_hour = avg_seconds // 3600
            avg_minute = (avg_seconds % 3600) // 60
            
            # Check for weekday patterns
            weekday_counts = defaultdict(int)
            for occ in occurrences:
                timestamp = occ.get("timestamp")
                if timestamp:
                    weekday_counts[timestamp.weekday()] += 1
            
            dominant_weekdays = [day for day, count in weekday_counts.items() if count >= len(occurrences) * 0.3]
            
            return {
                "action": f"activity at {avg_hour:02d}:{avg_minute:02d}",
                "avg_time": f"{avg_hour:02d}:{avg_minute:02d}",
                "weekdays": dominant_weekdays,
                "consistency": min(0.9, len(occurrences) / 10.0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing time pattern: {e}")
            return None
    
    def _calculate_consistency(self, intervals: List[float], avg_interval: float) -> float:
        """Calculate consistency of intervals"""
        try:
            if not intervals:
                return 0.0
            
            # Calculate standard deviation
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            std_dev = variance ** 0.5
            
            # Consistency is inverse of coefficient of variation
            if avg_interval > 0:
                cv = std_dev / avg_interval
                consistency = max(0.0, 1.0 - cv)
                return min(1.0, consistency)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating consistency: {e}")
            return 0.0
    
    async def _store_habits(self, user_id: str, habits: List[Dict[str, Any]]):
        """Store detected habits in database"""
        try:
            db = await anext(get_db())
            
            for habit_data in habits:
                # Check if habit already exists
                existing = db.query(UserHabit).filter(
                    and_(
                        UserHabit.user_id == user_id,
                        UserHabit.pattern_type == habit_data["pattern_type"]
                    )
                ).first()
                
                if existing:
                    # Update existing habit
                    existing.pattern_data = habit_data["pattern_data"]
                    existing.confidence = max(existing.confidence, habit_data["confidence"])
                    existing.observation_count = max(existing.observation_count, habit_data["observations"])
                    existing.last_observed = datetime.utcnow()
                else:
                    # Create new habit
                    new_habit = UserHabit(
                        user_id=user_id,
                        pattern_type=habit_data["pattern_type"],
                        pattern_data=habit_data["pattern_data"],
                        confidence=habit_data["confidence"],
                        observation_count=habit_data["observations"],
                        last_observed=datetime.utcnow()
                    )
                    db.add(new_habit)
            
            db.commit()
            logger.info(f"Stored {len(habits)} habits for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing habits: {e}")
    
    async def _update_habit_predictions(self, user_id: str, habits: List[Dict[str, Any]]):
        """Update predictions for when habits will occur next"""
        try:
            db = await anext(get_db())
            
            for habit_data in habits:
                # Find the habit in database
                habit = db.query(UserHabit).filter(
                    and_(
                        UserHabit.user_id == user_id,
                        UserHabit.pattern_type == habit_data["pattern_type"]
                    )
                ).first()
                
                if habit:
                    # Predict next occurrence
                    next_time = await self._predict_next_occurrence(habit)
                    habit.next_predicted = next_time
                    
                    # Generate proactive suggestions
                    suggestions = await self._generate_proactive_suggestions(habit)
                    habit.proactive_suggestions = suggestions
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating habit predictions: {e}")
    
    async def _predict_next_occurrence(self, habit: UserHabit) -> Optional[datetime]:
        """Predict when the habit will occur next"""
        try:
            if not habit.last_observed:
                return None
            
            pattern_data = habit.pattern_data
            
            if habit.pattern_type == "time_based":
                # For time-based habits, predict next occurrence
                last_time = habit.last_observed
                next_time = last_time + timedelta(days=1)
                
                # Adjust for specific time if available
                if "avg_time" in pattern_data:
                    time_parts = pattern_data["avg_time"].split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                return next_time
            
            elif habit.pattern_type == "frequency_based":
                # For frequency-based habits, add frequency interval
                frequency_hours = pattern_data.get("frequency_hours", 24)
                return habit.last_observed + timedelta(hours=frequency_hours)
            
            elif habit.pattern_type == "context_based":
                # For context-based habits, predict based on trigger frequency
                avg_gap = pattern_data.get("avg_gap_minutes", 60)
                return habit.last_observed + timedelta(minutes=avg_gap)
            
            elif habit.pattern_type == "sequence_based":
                # For sequence-based habits, predict based on sequence frequency
                return habit.last_observed + timedelta(hours=24)  # Daily sequences
            
            return None
            
        except Exception as e:
            logger.error(f"Error predicting next occurrence: {e}")
            return None
    
    async def _generate_proactive_suggestions(self, habit: UserHabit) -> List[Dict[str, Any]]:
        """Generate proactive suggestions for a habit"""
        try:
            suggestions = []
            pattern_data = habit.pattern_data
            
            if habit.pattern_type == "time_based":
                suggestions.append({
                    "type": "reminder",
                    "message": f"Time for your {pattern_data.get('action', 'habit')}",
                    "action": "set_reminder",
                    "confidence": habit.confidence
                })
            
            elif habit.pattern_type == "frequency_based":
                suggestions.append({
                    "type": "check",
                    "message": f"Check your {pattern_data.get('memory_type', 'items')}",
                    "action": "check_status",
                    "confidence": habit.confidence
                })
            
            elif habit.pattern_type == "context_based":
                suggestions.append({
                    "type": "follow_up",
                    "message": f"After {pattern_data.get('trigger', 'activity')}, remember to {pattern_data.get('action', 'follow up')}",
                    "action": "context_reminder",
                    "confidence": habit.confidence
                })
            
            elif habit.pattern_type == "sequence_based":
                suggestions.append({
                    "type": "sequence",
                    "message": f"Start your {pattern_data.get('action', 'routine')}",
                    "action": "start_sequence",
                    "confidence": habit.confidence
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating proactive suggestions: {e}")
            return []
    
    async def _generate_habit_suggestion(self, habit: Dict[str, Any], hours_until: float) -> Optional[Dict[str, Any]]:
        """Generate a suggestion for a specific habit"""
        try:
            pattern_data = habit.get('pattern_data', {})
            
            if hours_until <= 1:
                message = f"Time for your {pattern_data.get('action', 'habit')} now!"
                priority = "high"
            elif hours_until <= 2:
                message = f"Your {pattern_data.get('action', 'habit')} is due in {int(hours_until)} hours"
                priority = "medium"
            else:
                message = f"Your {pattern_data.get('action', 'habit')} is coming up in {int(hours_until)} hours"
                priority = "low"
            
            return {
                'type': 'habit_reminder',
                'priority': priority,
                'message': message,
                'action': 'execute_habit',
                'habit_id': habit.get('id'),
                'confidence': habit.get('confidence', 0.5),
                'hours_until': hours_until
            }
            
        except Exception as e:
            logger.error(f"Error generating habit suggestion: {e}")
            return None
    
    async def _generate_missed_habit_suggestion(self, habit: Dict[str, Any], hours_since: float) -> Optional[Dict[str, Any]]:
        """Generate a suggestion for a missed habit"""
        try:
            pattern_data = habit.get('pattern_data', {})
            
            message = f"You missed your {pattern_data.get('action', 'habit')} ({int(hours_since)} hours ago). Want to do it now?"
            
            return {
                'type': 'missed_habit',
                'priority': 'medium',
                'message': message,
                'action': 'execute_habit',
                'habit_id': habit.get('id'),
                'confidence': habit.get('confidence', 0.5),
                'hours_since': hours_since
            }
            
        except Exception as e:
            logger.error(f"Error generating missed habit suggestion: {e}")
            return None
    
    def _habit_to_dict(self, habit: UserHabit) -> Dict[str, Any]:
        """Convert habit object to dictionary"""
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

# Global habit engine instance
habit_engine = HabitEngine()
