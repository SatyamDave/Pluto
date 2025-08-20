from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PublicWorkCardProjection(BaseModel):
    headline: str
    role_fit: Optional[str] = None
    top_skills: List[str]
    trust_score: int = Field(ge=0, le=100)
    availability: Optional[str] = None
    location: Optional[str] = None
    highlights: List[str] = []
    verification_badges: List[str] = []
    share_assets: Dict[str, Any] = Field(default_factory=dict)
    versions: Dict[str, Any] = Field(default_factory=dict)


class TrustScoreBreakdown(BaseModel):
    base: int
    verified_skills: int
    verified_experiences: int
    recent_activity: int
    total: int


