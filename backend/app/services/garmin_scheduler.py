from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.db.session import async_session
from app.services.garmin_connect import sync_garmin_connect

logger = logging.getLogger(__name__)


async def garmin_sync_loop(stop_event: asyncio.Event) -> None:
    if not settings.garmin_configured or not settings.garmin_auto_sync:
        return

    interval_s = max(settings.garmin_sync_interval_minutes, 15) * 60
    while not stop_event.is_set():
        try:
            async with async_session() as db:
                result = await sync_garmin_connect(db)
                logger.info("Garmin Connect sync complete: %s", result)
        except Exception:
            logger.exception("Garmin Connect auto-sync failed")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_s)
        except asyncio.TimeoutError:
            continue
