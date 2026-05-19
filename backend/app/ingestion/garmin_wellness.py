import json
from pathlib import Path
from typing import Any

from dateutil import parser as date_parser

from app.ingestion.types import ParsedDailyMetric


def _float(v: Any) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _int(v: Any) -> int | None:
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _stress_avg(raw: dict[str, Any]) -> float | None:
    stress = raw.get("allDayStress")
    if isinstance(stress, dict):
        for agg in stress.get("aggregatorList") or []:
            if agg.get("type") == "TOTAL":
                return _float(agg.get("averageStressLevel"))
        return _float(stress.get("averageStressLevel"))
    return _float(stress)


def _body_battery(raw: dict[str, Any]) -> int | None:
    bb = raw.get("bodyBattery")
    if isinstance(bb, dict):
        for stat in bb.get("bodyBatteryStatList") or []:
            if stat.get("bodyBatteryStatType") == "MOSTRECENT":
                return _int(stat.get("statsValue"))
        return _int(bb.get("chargedValue"))
    return _int(bb)


def parse_uds_file(path: Path) -> list[ParsedDailyMetric]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        return []

    metrics: list[ParsedDailyMetric] = []
    for raw in data:
        if not isinstance(raw, dict):
            continue
        d = raw.get("calendarDate")
        if not d:
            continue
        metrics.append(
            ParsedDailyMetric(
                metric_date=date_parser.parse(str(d)).date(),
                resting_hr=_float(
                    raw.get("restingHeartRate") or raw.get("currentDayRestingHeartRate")
                ),
                stress_avg=_stress_avg(raw),
                body_battery=_body_battery(raw),
                vo2_max=_float(raw.get("vo2MaxValue") or raw.get("vO2MaxValue")),
            )
        )
    return metrics


def parse_sleep_file(path: Path) -> list[ParsedDailyMetric]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        return []

    metrics: list[ParsedDailyMetric] = []
    for raw in data:
        if not isinstance(raw, dict):
            continue
        d = raw.get("calendarDate")
        if not d:
            continue
        total_s = sum(
            _float(raw.get(k)) or 0
            for k in ("deepSleepSeconds", "lightSleepSeconds", "remSleepSeconds")
        )
        scores = raw.get("sleepScores") or {}
        sleep_score = _int(scores.get("overallScore")) if isinstance(scores, dict) else None

        metrics.append(
            ParsedDailyMetric(
                metric_date=date_parser.parse(str(d)).date(),
                sleep_hours=total_s / 3600 if total_s else None,
                sleep_score=sleep_score,
            )
        )
    return metrics


def merge_daily_metrics(rows: list[ParsedDailyMetric]) -> list[ParsedDailyMetric]:
    """Merge multiple records per date (UDS + sleep files)."""
    by_date: dict = {}
    for m in rows:
        existing = by_date.get(m.metric_date)
        if not existing:
            by_date[m.metric_date] = m
            continue
        by_date[m.metric_date] = ParsedDailyMetric(
            metric_date=m.metric_date,
            resting_hr=m.resting_hr or existing.resting_hr,
            hrv_ms=m.hrv_ms or existing.hrv_ms,
            sleep_hours=m.sleep_hours or existing.sleep_hours,
            sleep_score=m.sleep_score or existing.sleep_score,
            stress_avg=m.stress_avg or existing.stress_avg,
            body_battery=m.body_battery or existing.body_battery,
            recovery_score=m.recovery_score or existing.recovery_score,
            training_load_7d=m.training_load_7d or existing.training_load_7d,
            vo2_max=m.vo2_max or existing.vo2_max,
        )
    return sorted(by_date.values(), key=lambda x: x.metric_date)
