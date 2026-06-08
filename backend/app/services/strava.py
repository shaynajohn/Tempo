from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.ingestion.types import ParsedActivity
from app.models.strava_connection import StravaConnection

AUTH_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"


def authorization_url() -> str:
    params = {
        "client_id": settings.strava_client_id,
        "redirect_uri": settings.strava_redirect_uri,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "read,activity:read_all",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


async def exchange_code(db: AsyncSession, code: str, scope: str | None) -> StravaConnection:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.strava_client_id,
                "client_secret": settings.strava_client_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        payload = resp.json()

    athlete = payload.get("athlete") or {}
    athlete_id = athlete.get("id")
    if not athlete_id:
        raise ValueError("Strava did not return an athlete id.")

    result = await db.execute(
        select(StravaConnection).where(StravaConnection.athlete_id == athlete_id)
    )
    connection = result.scalar_one_or_none()
    if not connection:
        connection = StravaConnection(
            athlete_id=athlete_id,
            athlete_name=_athlete_name(athlete),
            access_token=payload["access_token"],
            refresh_token=payload["refresh_token"],
            expires_at=payload["expires_at"],
            scope=scope,
        )
        db.add(connection)
    else:
        connection.athlete_name = _athlete_name(athlete)
        connection.access_token = payload["access_token"]
        connection.refresh_token = payload["refresh_token"]
        connection.expires_at = payload["expires_at"]
        connection.scope = scope

    await db.commit()
    await db.refresh(connection)
    return connection


async def get_connection(db: AsyncSession) -> StravaConnection | None:
    return (
        await db.execute(select(StravaConnection).order_by(StravaConnection.created_at.desc()))
    ).scalars().first()


async def ensure_valid_token(db: AsyncSession, connection: StravaConnection) -> str:
    if connection.expires_at > int(time.time()) + 60:
        return connection.access_token

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.strava_client_id,
                "client_secret": settings.strava_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": connection.refresh_token,
            },
        )
        resp.raise_for_status()
        payload = resp.json()

    connection.access_token = payload["access_token"]
    connection.refresh_token = payload["refresh_token"]
    connection.expires_at = payload["expires_at"]
    await db.commit()
    await db.refresh(connection)
    return connection.access_token


async def fetch_activities(
    db: AsyncSession, connection: StravaConnection, per_page: int = 100
) -> list[dict[str, Any]]:
    token = await ensure_valid_token(db, connection)
    headers = {"Authorization": f"Bearer {token}"}
    params: dict[str, Any] = {"page": 1, "per_page": min(per_page, 100)}
    if connection.last_synced_at:
        params["after"] = int(connection.last_synced_at.replace(tzinfo=timezone.utc).timestamp())

    activities: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            resp = await client.get(ACTIVITIES_URL, headers=headers, params=params)
            resp.raise_for_status()
            page = resp.json()
            if not page:
                break
            activities.extend(page)
            if len(page) < params["per_page"]:
                break
            params["page"] += 1
            if params["page"] > 5:
                break

    return activities


async def sync_strava_activities(db: AsyncSession) -> dict[str, Any]:
    connection = await get_connection(db)
    if not connection:
        return {"connected": False, "imported": 0, "fetched": 0}

    raw_activities = await fetch_activities(db, connection)
    parsed = [
        activity
        for activity in (_parse_activity(a) for a in raw_activities)
        if activity is not None
    ]

    # Avoid importing persistence at module import time; it imports summary helpers.
    from app.ingestion.persist import persist_activities

    imported = await persist_activities(db, parsed)
    connection.last_synced_at = datetime.utcnow()
    await db.commit()

    return {
        "connected": True,
        "fetched": len(raw_activities),
        "imported": imported,
        "athlete_name": connection.athlete_name,
        "last_synced_at": connection.last_synced_at.isoformat(),
    }


def _parse_activity(raw: dict[str, Any]) -> ParsedActivity | None:
    if raw.get("type") != "Run" and raw.get("sport_type") not in {
        "Run",
        "TrailRun",
        "VirtualRun",
    }:
        return None

    started_at = _parse_dt(raw.get("start_date_local") or raw.get("start_date"))
    distance_m = _float(raw.get("distance"))
    moving_time = _float(raw.get("moving_time"))
    elapsed_time = _float(raw.get("elapsed_time"))
    avg_speed = _float(raw.get("average_speed"))
    avg_pace = 1000 / avg_speed if avg_speed and avg_speed > 0 else None
    cadence = _float(raw.get("average_cadence"))
    if cadence and cadence < 120:
        cadence *= 2

    activity_id = raw.get("id")
    if activity_id is None or not started_at:
        return None

    return ParsedActivity(
        external_id=f"strava:{activity_id}",
        activity_type=str(raw.get("sport_type") or raw.get("type") or "running").lower(),
        name=raw.get("name") or "Strava Run",
        started_at=started_at,
        distance_m=distance_m,
        duration_s=moving_time or elapsed_time,
        avg_hr=_float(raw.get("average_heartrate")),
        max_hr=_float(raw.get("max_heartrate")),
        avg_cadence=cadence,
        avg_pace_s_per_km=avg_pace,
        elevation_gain_m=_float(raw.get("total_elevation_gain")),
        calories=_int(raw.get("calories")),
        raw=raw,
    )


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


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


def _athlete_name(athlete: dict[str, Any]) -> str | None:
    parts = [athlete.get("firstname"), athlete.get("lastname")]
    name = " ".join([p for p in parts if p])
    return name or athlete.get("username")
