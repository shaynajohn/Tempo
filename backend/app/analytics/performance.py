from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity


@dataclass(frozen=True)
class TargetDistance:
    key: str
    label: str
    meters: float


TARGETS = [
    TargetDistance("mile", "1 mile", 1609.34),
    TargetDistance("5k", "5K", 5000),
    TargetDistance("10k", "10K", 10000),
    TargetDistance("half", "Half marathon", 21097.5),
    TargetDistance("marathon", "Marathon", 42195),
]
METERS_PER_MILE = 1609.344
KM_TO_MILES = 0.621371


async def compute_performance(db: AsyncSession) -> dict[str, Any]:
    activities = (
        await db.execute(select(Activity).order_by(Activity.started_at.desc()))
    ).scalars().all()

    valid = [
        a
        for a in activities
        if a.distance_m
        and a.duration_s
        and a.distance_m >= 800
        and a.duration_s >= 180
    ]

    if not valid:
        return {
            "personal_bests": [],
            "race_projections": [],
            "fastest_run": None,
            "longest_run": None,
            "summary": "Import more runs to calculate performance trends.",
        }

    fastest = min(valid, key=lambda a: a.duration_s / (a.distance_m / 1000))
    longest = max(valid, key=lambda a: a.distance_m or 0)
    source = _projection_source(valid)

    personal_bests = [_personal_best(valid, target) for target in TARGETS]
    projections = [_projection(source, target) for target in TARGETS]

    return {
        "personal_bests": [pb for pb in personal_bests if pb],
        "race_projections": projections,
        "fastest_run": _activity_summary(fastest),
        "longest_run": _activity_summary(longest),
        "projection_source": _activity_summary(source),
        "summary": _summary(source, fastest, longest),
    }


def _personal_best(
    activities: list[Activity], target: TargetDistance
) -> dict[str, Any] | None:
    eligible = [a for a in activities if (a.distance_m or 0) >= target.meters]
    if not eligible:
        return None

    best = min(eligible, key=lambda a: _scaled_time(a, target.meters))
    seconds = _scaled_time(best, target.meters)
    return {
        "distance_key": target.key,
        "distance_label": target.label,
        "seconds": round(seconds),
        "formatted_time": _format_duration(seconds),
        "pace_s_per_km": round(seconds / (target.meters / 1000)),
        "activity": _activity_summary(best),
        "method": "Estimated from average pace of an activity at least this long.",
    }


def _projection(source: Activity, target: TargetDistance) -> dict[str, Any]:
    seconds = _riegel(source.duration_s or 0, source.distance_m or 1, target.meters)
    return {
        "distance_key": target.key,
        "distance_label": target.label,
        "seconds": round(seconds),
        "formatted_time": _format_duration(seconds),
        "pace_s_per_km": round(seconds / (target.meters / 1000)),
        "source_activity": _activity_summary(source),
        "method": "Riegel formula from your strongest whole-activity effort.",
    }


def _projection_source(activities: list[Activity]) -> Activity:
    # Prefer efforts long enough to say something meaningful, then choose the best
    # equivalent 5K. This avoids tiny warmups dominating race projections.
    candidates = [a for a in activities if (a.distance_m or 0) >= 2500]
    if not candidates:
        candidates = activities
    return min(candidates, key=lambda a: _riegel(a.duration_s or 0, a.distance_m or 1, 5000))


def _scaled_time(activity: Activity, target_meters: float) -> float:
    return (activity.duration_s or 0) * (target_meters / (activity.distance_m or 1))


def _riegel(seconds: float, source_meters: float, target_meters: float) -> float:
    return seconds * ((target_meters / source_meters) ** 1.06)


def _activity_summary(activity: Activity) -> dict[str, Any]:
    pace = (activity.duration_s or 0) / ((activity.distance_m or 1) / 1000)
    return {
        "id": activity.id,
        "name": activity.name or "Run",
        "started_at": _iso(activity.started_at),
        "distance_m": activity.distance_m,
        "duration_s": activity.duration_s,
        "pace_s_per_km": round(pace),
    }


def _summary(source: Activity, fastest: Activity, longest: Activity) -> str:
    source_mi = (source.distance_m or 0) / METERS_PER_MILE
    fastest_pace = (fastest.duration_s or 0) / ((fastest.distance_m or 1) / 1000)
    return (
        f"Your projections are based on {source.name or 'your strongest run'} "
        f"({source_mi:.1f} mi). Fastest average pace is "
        f"{_format_pace(fastest_pace)}, and your longest imported run is "
        f"{(longest.distance_m or 0) / METERS_PER_MILE:.1f} mi."
    )


def _format_duration(seconds: float) -> str:
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _format_pace(seconds: float) -> str:
    sec_per_mile = seconds / KM_TO_MILES
    minutes, secs = divmod(int(round(sec_per_mile)), 60)
    return f"{minutes}:{secs:02d}/mi"


def _iso(value: datetime) -> str:
    return value.isoformat()
