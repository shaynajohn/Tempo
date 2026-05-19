from datetime import date
from typing import Any

from pydantic import BaseModel


class FatiguePoint(BaseModel):
    date: date
    score: float
    risk_level: str
    factors: list[str]


class FatigueOut(BaseModel):
    current_score: float
    risk_level: str
    trend: list[FatiguePoint]
    recommendation: str


class PatternOut(BaseModel):
    pattern_type: str
    title: str
    description: str
    evidence: dict[str, Any]
    confidence: float


class DashboardStats(BaseModel):
    total_activities: int
    total_distance_km: float
    avg_weekly_km: float
    recent_fatigue_score: float | None
    recent_insights: int
