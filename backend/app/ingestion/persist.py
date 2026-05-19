from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.types import ParsedActivity, ParsedDailyMetric
from app.models.activity import Activity
from app.models.daily_metric import DailyMetric
from app.services.summaries import build_activity_summary


async def persist_activities(db: AsyncSession, parsed: list[ParsedActivity]) -> int:
    count = 0
    for p in parsed:
        if p.external_id:
            existing = await db.execute(
                select(Activity).where(Activity.external_id == p.external_id)
            )
            if existing.scalar_one_or_none():
                continue

        summary = build_activity_summary(p)
        activity = Activity(
            external_id=p.external_id or None,
            activity_type=p.activity_type,
            name=p.name,
            started_at=p.started_at,
            distance_m=p.distance_m,
            duration_s=p.duration_s,
            avg_hr=p.avg_hr,
            max_hr=p.max_hr,
            avg_cadence=p.avg_cadence,
            avg_pace_s_per_km=p.avg_pace_s_per_km,
            elevation_gain_m=p.elevation_gain_m,
            calories=p.calories,
            training_load=p.training_load,
            vo2_max=p.vo2_max,
            temperature_c=p.temperature_c,
            humidity_pct=p.humidity_pct,
            laps=p.laps,
            hr_zones=p.hr_zones,
            splits=p.splits,
            raw=p.raw,
            summary_text=summary,
        )
        db.add(activity)
        count += 1
    return count


async def persist_daily_metrics(db: AsyncSession, parsed: list[ParsedDailyMetric]) -> int:
    count = 0
    for p in parsed:
        result = await db.execute(
            select(DailyMetric).where(DailyMetric.metric_date == p.metric_date)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.resting_hr = p.resting_hr or existing.resting_hr
            existing.hrv_ms = p.hrv_ms or existing.hrv_ms
            existing.sleep_hours = p.sleep_hours or existing.sleep_hours
            existing.sleep_score = p.sleep_score or existing.sleep_score
            existing.stress_avg = p.stress_avg or existing.stress_avg
            existing.body_battery = p.body_battery or existing.body_battery
            existing.recovery_score = p.recovery_score or existing.recovery_score
            existing.training_load_7d = p.training_load_7d or existing.training_load_7d
            existing.vo2_max = p.vo2_max or existing.vo2_max
            count += 1
            continue

        db.add(
            DailyMetric(
                metric_date=p.metric_date,
                resting_hr=p.resting_hr,
                hrv_ms=p.hrv_ms,
                sleep_hours=p.sleep_hours,
                sleep_score=p.sleep_score,
                stress_avg=p.stress_avg,
                body_battery=p.body_battery,
                recovery_score=p.recovery_score,
                training_load_7d=p.training_load_7d,
                vo2_max=p.vo2_max,
            )
        )
        count += 1
    return count
