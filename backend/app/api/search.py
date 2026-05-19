from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.search import index_all_activities, semantic_search
from app.db.session import get_db
from app.schemas.insight import SearchResult

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


@router.post("", response_model=list[SearchResult])
async def search_workouts(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> list[SearchResult]:
    return await semantic_search(db, body.query, body.limit)


@router.post("/index")
async def index_workouts(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    count = await index_all_activities(db)
    return {"indexed": count}
