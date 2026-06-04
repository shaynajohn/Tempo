from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.daily_metric import DailyMetric


async def compute_library_status(db: AsyncSession) -> dict[str, Any]:
    activity_count = (
        await db.execute(select(func.count()).select_from(Activity))
    ).scalar() or 0
    wellness_count = (
        await db.execute(select(func.count()).select_from(DailyMetric))
    ).scalar() or 0

    first_activity, latest_activity = (
        await db.execute(
            select(func.min(Activity.started_at), func.max(Activity.started_at))
        )
    ).one()
    first_wellness, latest_wellness = (
        await db.execute(
            select(func.min(DailyMetric.metric_date), func.max(DailyMetric.metric_date))
        )
    ).one()

    latest_data_date = _latest_date(latest_activity.date() if latest_activity else None, latest_wellness)
    days_since_latest = (date.today() - latest_data_date).days if latest_data_date else None
    freshness = _freshness(activity_count, wellness_count, days_since_latest)

    return {
        "activity_count": activity_count,
        "wellness_count": wellness_count,
        "first_activity_date": _iso_date(first_activity.date() if first_activity else None),
        "latest_activity_date": _iso_date(latest_activity.date() if latest_activity else None),
        "first_wellness_date": _iso_date(first_wellness),
        "latest_wellness_date": _iso_date(latest_wellness),
        "latest_data_date": _iso_date(latest_data_date),
        "days_since_latest": days_since_latest,
        "freshness": freshness,
        "needs_import": freshness in {"empty", "stale"},
        "summary": _summary(activity_count, wellness_count, days_since_latest, freshness),
    }


def _latest_date(*values: date | None) -> date | None:
    dates = [v for v in values if v is not None]
    return max(dates) if dates else None


def _freshness(
    activity_count: int, wellness_count: int, days_since_latest: int | None
) -> str:
    if activity_count == 0 and wellness_count == 0:
        return "empty"
    if days_since_latest is None:
        return "empty"
    if days_since_latest <= 3:
        return "fresh"
    if days_since_latest <= 14:
        return "aging"
    return "stale"


def _summary(
    activity_count: int,
    wellness_count: int,
    days_since_latest: int | None,
    freshness: str,
) -> str:
    if freshness == "empty":
        return "No Garmin data has been imported yet."
    if freshness == "fresh":
        return "Your local Tempo library is up to date."
    if freshness == "aging":
        return (
            f"Your latest imported Garmin data is {days_since_latest} days old. "
            "Re-import only if you have newer Garmin exports."
        )
    return (
        f"Your latest imported Garmin data is {days_since_latest} days old. "
        "Import a newer Garmin export to refresh recommendations."
    )


def _iso_date(value: date | None) -> str | None:
    return value.isoformat() if value else None
