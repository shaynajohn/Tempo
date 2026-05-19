from fastapi import APIRouter

from app.api import activities, analytics, ingest, insights, search

router = APIRouter(prefix="/api/v1")
router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
router.include_router(activities.router, prefix="/activities", tags=["activities"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(insights.router, prefix="/insights", tags=["insights"])
router.include_router(search.router, prefix="/search", tags=["search"])
