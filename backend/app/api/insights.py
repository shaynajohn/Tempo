from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.explanations import explain_run
from app.db.session import get_db
from app.models.insight import Insight
from app.schemas.insight import InsightOut

router = APIRouter()


@router.get("", response_model=list[InsightOut])
async def list_insights(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[InsightOut]:
    rows = (
        await db.execute(select(Insight).order_by(Insight.created_at.desc()).limit(limit))
    ).scalars().all()
    return [InsightOut.model_validate(r) for r in rows]


@router.post("/explain/{activity_id}", response_model=InsightOut)
async def explain_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
) -> InsightOut:
    try:
        insight = await explain_run(db, activity_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    return InsightOut.model_validate(insight)
