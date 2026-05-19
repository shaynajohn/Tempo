import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_text
from app.config import settings
from app.models.activity import Activity
from app.models.embedding import WorkoutEmbedding
from app.schemas.insight import SearchResult


async def index_all_activities(db: AsyncSession) -> int:
    if not settings.openai_api_key:
        return 0

    activities = (
        await db.execute(
            select(Activity).where(Activity.summary_text.isnot(None))
        )
    ).scalars().all()

    count = 0
    for act in activities:
        existing = await db.execute(
            select(WorkoutEmbedding).where(WorkoutEmbedding.activity_id == act.id)
        )
        if existing.scalar_one_or_none():
            continue

        content = act.summary_text or ""
        vector = await embed_text(content)
        db.add(
            WorkoutEmbedding(
                activity_id=act.id,
                content=content,
                content_type="summary",
                embedding=vector,
            )
        )
        count += 1

    await db.commit()
    return count


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


async def semantic_search(
    db: AsyncSession, query: str, limit: int = 10
) -> list[SearchResult]:
    if not settings.openai_api_key:
        return []

    query_vec = await embed_text(query)

    if settings.uses_sqlite:
        rows = (await db.execute(select(WorkoutEmbedding))).scalars().all()
        scored = [
            (emb, _cosine_similarity(query_vec, emb.embedding))
            for emb in rows
            if emb.embedding
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        rows_scored = scored[:limit]
    else:
        distance = WorkoutEmbedding.embedding.cosine_distance(query_vec)
        similarity = (1 - distance).label("similarity")
        stmt = (
            select(WorkoutEmbedding, similarity)
            .order_by(distance)
            .limit(limit)
        )
        rows_scored = [(emb, float(sim)) for emb, sim in (await db.execute(stmt)).all()]

    results: list[SearchResult] = []
    for emb, sim in rows_scored:
        act = await db.get(Activity, emb.activity_id)
        if not act:
            continue
        results.append(
            SearchResult(
                activity_id=act.id,
                name=act.name,
                started_at=act.started_at,
                distance_m=act.distance_m,
                avg_pace_s_per_km=act.avg_pace_s_per_km,
                content=emb.content,
                similarity=sim,
            )
        )

    return results
