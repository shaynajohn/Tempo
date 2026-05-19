from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str | None
    activity_type: str
    name: str | None
    started_at: datetime
    distance_m: float | None
    duration_s: float | None
    avg_hr: float | None
    max_hr: float | None
    avg_cadence: float | None
    avg_pace_s_per_km: float | None
    elevation_gain_m: float | None
    training_load: float | None
    vo2_max: float | None
    temperature_c: float | None
    summary_text: str | None
    splits: list[dict[str, Any]] | None


class ActivityList(BaseModel):
    items: list[ActivityOut]
    total: int
