from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    insight_type: str
    title: str
    body: str
    confidence: float | None
    activity_id: int | None
    metadata_: dict[str, Any] | None = Field(None, validation_alias="metadata_")
    created_at: datetime


class SearchResult(BaseModel):
    activity_id: int
    name: str | None
    started_at: datetime
    distance_m: float | None
    avg_pace_s_per_km: float | None
    content: str
    similarity: float
