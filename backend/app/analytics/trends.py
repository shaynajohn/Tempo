from collections import defaultdict
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.daily_metric import DailyMetric


async def compute_trends(db: AsyncSession) -> dict:
    activities = (
        await db.execute(select(Activity).order_by(Activity.started_at))
    ).scalars().all()

    metrics = (
        await db.execute(select(DailyMetric).order_by(DailyMetric.metric_date))
    ).scalars().all()

    weekly_volume = _weekly_volume(activities)
    pace_trend = _pace_trend(activities)
    wellness = _wellness_series(metrics)

    return {
        "weekly_volume": weekly_volume,
        "pace_trend": pace_trend,
        "wellness": wellness,
    }


def _weekly_volume(activities: list[Activity]) -> list[dict]:
    if not activities:
        return []

    rows = [
        {
            "week": a.started_at.date().isocalendar()[:2],
            "km": (a.distance_m or 0) / 1000,
        }
        for a in activities
    ]
    df = pd.DataFrame(rows)
    grouped = df.groupby("week")["km"].sum().reset_index()
    return [
        {"week": f"{y}-W{w:02d}", "km": round(km, 1)}
        for (y, w), km in zip(grouped["week"], grouped["km"])
    ]


def _pace_trend(activities: list[Activity]) -> list[dict]:
    items = [
        {
            "date": a.started_at.date().isoformat(),
            "pace": a.avg_pace_s_per_km,
            "name": a.name or "Run",
            "id": a.id,
        }
        for a in activities
        if a.avg_pace_s_per_km
    ]
    return sorted(items, key=lambda x: x["date"])


def _wellness_series(metrics: list[DailyMetric]) -> list[dict]:
    return [
        {
            "date": m.metric_date.isoformat(),
            "resting_hr": m.resting_hr,
            "sleep_hours": m.sleep_hours,
            "hrv": m.hrv_ms,
            "stress": m.stress_avg,
        }
        for m in metrics
    ]
