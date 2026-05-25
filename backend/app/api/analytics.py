from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.graph import run_coaching_pipeline
from app.analytics.fatigue import compute_fatigue
from app.analytics.patterns import discover_patterns
from app.analytics.performance import compute_performance
from app.analytics.trends import compute_trends
from app.db.session import get_db
from app.models.activity import Activity
from app.models.insight import Insight
from app.schemas.analytics import DashboardStats, FatigueOut, PatternOut

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
    total = (await db.execute(select(func.count()).select_from(Activity))).scalar() or 0
    dist = (
        await db.execute(select(func.sum(Activity.distance_m)))
    ).scalar() or 0
    fatigue = await compute_fatigue(db)
    insight_count = (
        await db.execute(select(func.count()).select_from(Insight))
    ).scalar() or 0

    return DashboardStats(
        total_activities=total,
        total_distance_km=dist / 1000,
        avg_weekly_km=(dist / 1000) / max(1, total / 3),
        recent_fatigue_score=fatigue.current_score if fatigue.trend else None,
        recent_insights=insight_count,
    )


@router.get("/fatigue", response_model=FatigueOut)
async def fatigue(db: AsyncSession = Depends(get_db)) -> FatigueOut:
    return await compute_fatigue(db)


@router.get("/patterns", response_model=list[PatternOut])
async def patterns(db: AsyncSession = Depends(get_db)) -> list[PatternOut]:
    return await discover_patterns(db)


@router.get("/trends")
async def trends(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    return await compute_trends(db)


@router.get("/performance")
async def performance(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    return await compute_performance(db)


@router.get("/coaching-report")
@router.post("/coaching-report")
async def coaching_report(
    activity_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await run_coaching_pipeline(db, activity_id)
