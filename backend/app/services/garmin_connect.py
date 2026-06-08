from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from garminconnect import Garmin
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.search import index_all_activities
from app.config import settings
from app.ingestion.persist import persist_activities
from app.ingestion.types import ParsedActivity

last_sync_at: datetime | None = None


def configured() -> bool:
    return settings.garmin_configured


async def sync_garmin_connect(db: AsyncSession) -> dict[str, Any]:
    global last_sync_at

    if not settings.garmin_configured:
        return {"configured": False, "fetched": 0, "imported": 0}

    raw_activities = await asyncio.to_thread(_fetch_recent_activities)
    parsed = [
        activity
        for activity in (_parse_activity(a) for a in raw_activities)
        if activity is not None
    ]

    imported = await persist_activities(db, parsed)
    await db.commit()

    if imported > 0:
        await index_all_activities(db)

    last_sync_at = datetime.utcnow()
    return {
        "configured": True,
        "fetched": len(raw_activities),
        "runs_found": len(parsed),
        "imported": imported,
        "last_synced_at": last_sync_at.isoformat(),
    }


def _fetch_recent_activities() -> list[dict[str, Any]]:
    client = Garmin(settings.garmin_email, settings.garmin_password)
    client.login()
    return client.get_activities(0, settings.garmin_sync_limit)


def _parse_activity(raw: dict[str, Any]) -> ParsedActivity | None:
    if not _is_running(raw):
        return None

    activity_id = raw.get("activityId") or raw.get("activity_id") or raw.get("id")
    started_at = _parse_dt(
        raw.get("startTimeLocal")
        or raw.get("startTimeGMT")
        or raw.get("start_time")
        or raw.get("beginTimestamp")
    )
    if activity_id is None or started_at is None:
        return None

    distance_m = _distance_meters(raw.get("distance") or raw.get("distanceInMeters"))
    duration_s = _duration_seconds(
        raw.get("movingDuration")
        or raw.get("duration")
        or raw.get("elapsedDuration")
        or raw.get("elapsed_time")
    )
    pace = raw.get("averagePace") or raw.get("avgPace")
    avg_speed = _float(raw.get("averageSpeed") or raw.get("avgSpeed"))
    if pace is None and avg_speed:
        pace = _pace_from_speed_mps(avg_speed)
    if pace is None and distance_m and duration_s and distance_m > 0:
        pace = duration_s / (distance_m / 1000)

    cadence = _float(
        raw.get("avgDoubleCadence")
        or raw.get("averageDoubleCadence")
        or raw.get("avgRunCadence")
        or raw.get("averageCadence")
    )
    if cadence and cadence < 100:
        cadence *= 2

    return ParsedActivity(
        external_id=str(activity_id),
        activity_type=_activity_type_key(raw) or "running",
        name=raw.get("activityName") or raw.get("name") or "Garmin run",
        started_at=started_at,
        distance_m=distance_m,
        duration_s=duration_s,
        avg_hr=_float(raw.get("averageHR") or raw.get("avgHR") or raw.get("avgHr")),
        max_hr=_float(raw.get("maxHR") or raw.get("maxHeartRate") or raw.get("maxHr")),
        avg_cadence=cadence,
        avg_pace_s_per_km=_float(pace),
        elevation_gain_m=_elevation_m(raw.get("elevationGain") or raw.get("elevationGainInMeters")),
        calories=_int(raw.get("calories")),
        training_load=_float(raw.get("activityTrainingLoad") or raw.get("trainingEffect")),
        vo2_max=_float(raw.get("vO2MaxValue") or raw.get("vo2Max")),
        temperature_c=_float(raw.get("avgTemperature") or raw.get("temperature")),
        raw={**raw, "tempo_source": "garmin_connect"},
    )


def _activity_type_key(raw: dict[str, Any]) -> str:
    activity_type = raw.get("activityType") or raw.get("type") or ""
    if isinstance(activity_type, dict):
        return str(activity_type.get("typeKey") or activity_type.get("typeId") or "").lower()
    return str(activity_type).lower()


def _is_running(raw: dict[str, Any]) -> bool:
    key = _activity_type_key(raw)
    sport = str(raw.get("sportType") or "").upper()
    return (
        "running" in key
        or key in {"run", "trail_run", "virtual_run"}
        or sport == "RUNNING"
    )


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000
        return datetime.fromtimestamp(ts)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _distance_meters(value: Any) -> float | None:
    distance = _float(value)
    if distance is None:
        return None
    if distance < 500:
        return distance * 1000
    if distance > 100000:
        return distance / 100
    return distance


def _duration_seconds(value: Any) -> float | None:
    duration = _float(value)
    if duration is None:
        return None
    if duration > 10000:
        return duration / 1000
    return duration


def _pace_from_speed_mps(speed: float | None) -> float | None:
    if not speed or speed <= 0:
        return None
    if speed > 20:
        speed /= 3.6
    return 1000.0 / speed


def _elevation_m(value: Any) -> float | None:
    elevation = _float(value)
    if elevation is None:
        return None
    if elevation > 5000:
        return elevation / 100
    return elevation


def _float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
