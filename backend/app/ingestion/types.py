from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class ParsedActivity:
    external_id: str | None
    activity_type: str
    name: str | None
    started_at: datetime
    distance_m: float | None = None
    duration_s: float | None = None
    avg_hr: float | None = None
    max_hr: float | None = None
    avg_cadence: float | None = None
    avg_pace_s_per_km: float | None = None
    elevation_gain_m: float | None = None
    calories: int | None = None
    training_load: float | None = None
    vo2_max: float | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None
    laps: list[dict[str, Any]] | None = None
    hr_zones: dict[str, Any] | None = None
    splits: list[dict[str, Any]] | None = None
    raw: dict[str, Any] | None = None


@dataclass
class ParsedDailyMetric:
    metric_date: date
    resting_hr: float | None = None
    hrv_ms: float | None = None
    sleep_hours: float | None = None
    sleep_score: int | None = None
    stress_avg: float | None = None
    body_battery: int | None = None
    recovery_score: float | None = None
    training_load_7d: float | None = None
    vo2_max: float | None = None


@dataclass
class ParseResult:
    activities: list[ParsedActivity] = field(default_factory=list)
    daily_metrics: list[ParsedDailyMetric] = field(default_factory=list)
