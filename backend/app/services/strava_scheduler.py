from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.db.session import async_session
from app.services.strava import sync_strava_activities

logger = logging.getLogger(__name__)


async def strava_sync_loop(stop_event: asyncio.Event) -> None:
    if not settings.strava_configured or not settings.strava_auto_sync:
        return

    interval_s = max(settings.strava_sync_interval_minutes, 5) * 60
    while not stop_event.is_set():
        try:
            async with async_session() as db:
                result = await sync_strava_activities(db)
                if result.get("connected"):
                    logger.info("Strava sync complete: %s", result)
        except Exception:
            logger.exception("Strava auto-sync failed")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_s)
        except asyncio.TimeoutError:
            continue
