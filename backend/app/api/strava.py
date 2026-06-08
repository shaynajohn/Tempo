from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.services.strava import (
    authorization_url,
    exchange_code,
    get_connection,
    sync_strava_activities,
)

router = APIRouter()


@router.get("/status")
async def status(db: AsyncSession = Depends(get_db)) -> dict:
    connection = await get_connection(db)
    return {
        "configured": settings.strava_configured,
        "auto_sync_enabled": settings.strava_auto_sync,
        "auto_sync_interval_minutes": settings.strava_sync_interval_minutes,
        "connected": connection is not None,
        "athlete_name": connection.athlete_name if connection else None,
        "athlete_id": connection.athlete_id if connection else None,
        "last_synced_at": connection.last_synced_at.isoformat()
        if connection and connection.last_synced_at
        else None,
        "auth_url": authorization_url() if settings.strava_configured else None,
    }


@router.get("/authorize")
async def authorize() -> dict:
    if not settings.strava_configured:
        raise HTTPException(
            status_code=400,
            detail="Set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in backend/.env.",
        )
    return {"auth_url": authorization_url()}


@router.get("/callback")
async def callback(
    code: str | None = Query(None),
    scope: str | None = Query(None),
    error: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if error:
        return RedirectResponse(f"{settings.frontend_url}/import?strava=error")
    if not code:
        raise HTTPException(status_code=400, detail="Missing Strava authorization code.")

    await exchange_code(db, code, scope)
    return RedirectResponse(f"{settings.frontend_url}/import?strava=connected")


@router.post("/sync")
async def sync(db: AsyncSession = Depends(get_db)) -> dict:
    if not settings.strava_configured:
        raise HTTPException(
            status_code=400,
            detail="Set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in backend/.env.",
        )
    return await sync_strava_activities(db)
