from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.services import garmin_connect as garmin_service

router = APIRouter()


@router.get("/status")
async def status() -> dict:
    return {
        "configured": settings.garmin_configured,
        "auto_sync_enabled": settings.garmin_auto_sync,
        "auto_sync_interval_minutes": settings.garmin_sync_interval_minutes,
        "sync_limit": settings.garmin_sync_limit,
        "last_synced_at": garmin_service.last_sync_at.isoformat()
        if garmin_service.last_sync_at
        else None,
    }


@router.post("/sync")
async def sync(db: AsyncSession = Depends(get_db)) -> dict:
    if not settings.garmin_configured:
        raise HTTPException(
            status_code=400,
            detail="Set GARMIN_EMAIL and GARMIN_PASSWORD in backend/.env.",
        )
    return await garmin_service.sync_garmin_connect(db)
