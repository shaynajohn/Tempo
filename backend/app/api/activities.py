from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.activity import Activity
from app.schemas.activity import ActivityList, ActivityOut

router = APIRouter()


@router.get("", response_model=ActivityList)
async def list_activities(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ActivityList:
    total = (await db.execute(select(func.count()).select_from(Activity))).scalar() or 0
    rows = (
        await db.execute(
            select(Activity).order_by(Activity.started_at.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()
    return ActivityList(items=[ActivityOut.model_validate(r) for r in rows], total=total)


@router.get("/{activity_id}", response_model=ActivityOut)
async def get_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
) -> ActivityOut:
    activity = await db.get(Activity, activity_id)
    if not activity:
        raise HTTPException(404, "Activity not found")
    return ActivityOut.model_validate(activity)
