import json
from datetime import datetime
from pathlib import Path
from typing import Any

from dateutil import parser as date_parser

from app.ingestion.types import ParsedActivity, ParsedDailyMetric

RUN_ACTIVITY_TYPES = frozenset(
    {
        "running",
        "treadmill_running",
        "trail_running",
        "track_running",
        "virtual_run",
        "indoor_running",
    }
)


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000
        return datetime.fromtimestamp(ts)
    return date_parser.parse(str(value))


def _distance_meters(value: Any) -> float | None:
    if value is None:
        return None
    d = float(value)
    # Garmin DI summarized export uses centimeters
    if d > 1000:
        return d / 100
    if d < 500:
        return d * 1000
    return d


def _duration_seconds(value: Any) -> float | None:
    if value is None:
        return None
    d = float(value)
    if d > 10000:
        return d / 1000
    return d


def _pace_from_speed_mps(speed: float | None) -> float | None:
    if not speed or speed <= 0:
        return None
    return 1000.0 / speed


def _activity_type_key(raw: dict[str, Any]) -> str:
    t = raw.get("activityType") or raw.get("type") or ""
    if isinstance(t, dict):
        return str(t.get("typeKey") or t.get("typeId") or "").lower()
    return str(t).lower()


def _is_running(raw: dict[str, Any]) -> bool:
    key = _activity_type_key(raw)
    if key in RUN_ACTIVITY_TYPES:
        return True
    sport = str(raw.get("sportType") or "").upper()
    return sport == "RUNNING" or (key.endswith("_running") and "wheelchair" not in key)


def _normalize_activity(raw: dict[str, Any]) -> ParsedActivity | None:
    if not _is_running(raw):
        return None

    started = _parse_dt(
        raw.get("startTimeLocal")
        or raw.get("startTimeGMT")
        or raw.get("beginTimestamp")
        or raw.get("start_time")
        or raw.get("date")
    )
    if not started:
        return None

    dist_m = _distance_meters(raw.get("distance") or raw.get("distanceInMeters"))
    duration = _duration_seconds(
        raw.get("movingDuration") or raw.get("duration") or raw.get("elapsedDuration")
    )

    pace = raw.get("avgPace") or raw.get("averagePace")
    avg_speed = raw.get("avgSpeed") or raw.get("averageSpeed")
    if pace is None and avg_speed:
        speed = float(avg_speed)
        if speed < 1.0:
            speed *= 10
        pace = _pace_from_speed_mps(speed)
    if pace is None and dist_m and duration and dist_m > 0:
        pace = duration / (dist_m / 1000)

    cadence = _float(
        raw.get("avgDoubleCadence")
        or raw.get("averageDoubleCadence")
        or raw.get("avgRunCadence")
        or raw.get("averageCadence")
    )
    if cadence and cadence < 100 and raw.get("avgRunCadence"):
        cadence = _float(raw.get("avgRunCadence"))
        if cadence and cadence < 100:
            cadence *= 2

    splits = raw.get("splits") or raw.get("lapDTOs") or raw.get("laps")
    if splits and isinstance(splits, list):
        splits = [_normalize_split(s) for s in splits if isinstance(s, dict)]

    activity_id = raw.get("activityId") or raw.get("id")
    return ParsedActivity(
        external_id=str(activity_id) if activity_id is not None else None,
        activity_type=_activity_type_key(raw) or "running",
        name=raw.get("name") or raw.get("activityName"),
        started_at=started,
        distance_m=dist_m,
        duration_s=duration,
        avg_hr=_float(raw.get("avgHr") or raw.get("avgHR") or raw.get("averageHR")),
        max_hr=_float(raw.get("maxHr") or raw.get("maxHR") or raw.get("maxHeartRate")),
        avg_cadence=cadence,
        avg_pace_s_per_km=_float(pace),
        elevation_gain_m=_elevation_m(raw.get("elevationGain") or raw.get("elevationGainInMeters")),
        calories=_int(raw.get("calories")),
        training_load=_float(raw.get("activityTrainingLoad") or raw.get("trainingEffect")),
        vo2_max=_float(raw.get("vO2MaxValue") or raw.get("vo2Max")),
        temperature_c=_float(raw.get("avgTemperature") or raw.get("temperature")),
        splits=splits,
        raw=raw,
    )


def _elevation_m(value: Any) -> float | None:
    v = _float(value)
    if v is None:
        return None
    if v > 5000:
        return v / 100
    return v


def _normalize_split(s: dict[str, Any]) -> dict[str, Any]:
    return {
        "distance_m": _distance_meters(s.get("distance") or s.get("distanceInMeters")),
        "duration_s": _duration_seconds(s.get("duration") or s.get("movingDuration")),
        "avg_hr": _float(s.get("averageHR") or s.get("avgHR") or s.get("avgHr")),
        "avg_cadence": _float(s.get("averageCadence") or s.get("avgCadence")),
        "avg_pace_s_per_km": _float(s.get("averagePace") or s.get("avgPace")),
    }


def _normalize_daily(raw: dict[str, Any]) -> ParsedDailyMetric | None:
    d = raw.get("calendarDate") or raw.get("date") or raw.get("metric_date")
    if not d:
        return None
    metric_date = date_parser.parse(str(d)).date()
    sleep_s = _float(raw.get("sleepTimeSeconds") or raw.get("sleepDuration"))
    sleep_hours = sleep_s / 3600 if sleep_s else _float(raw.get("sleepHours"))

    return ParsedDailyMetric(
        metric_date=metric_date,
        resting_hr=_float(
            raw.get("restingHeartRate")
            or raw.get("currentDayRestingHeartRate")
            or raw.get("resting_hr")
        ),
        hrv_ms=_float(raw.get("hrvStatus") or raw.get("hrv") or raw.get("weeklyAvgHrv")),
        sleep_hours=sleep_hours,
        sleep_score=_int(raw.get("sleepScore")),
        stress_avg=_float(raw.get("averageStressLevel") or raw.get("stress")),
        body_battery=_int(raw.get("bodyBatteryMostRecentValue") or raw.get("bodyBattery")),
        recovery_score=_float(raw.get("recoveryScore") or raw.get("recovery")),
        training_load_7d=_float(raw.get("trainingLoadBalance") or raw.get("trainingLoad7d")),
        vo2_max=_float(raw.get("vo2Max") or raw.get("vO2MaxValue")),
    )


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


def _extract_activities(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        if (
            len(data) == 1
            and isinstance(data[0], dict)
            and "summarizedActivitiesExport" in data[0]
        ):
            return data[0]["summarizedActivitiesExport"]
        return [
            x
            for x in data
            if isinstance(x, dict) and ("activityId" in x or "startTimeLocal" in x)
        ]
    if isinstance(data, dict):
        for key in ("summarizedActivitiesExport", "activities", "activityList", "runs"):
            if key in data and isinstance(data[key], list):
                return data[key]
        if "activityId" in data:
            return [data]
    return []


def parse_garmin_json(path: Path) -> tuple[list[ParsedActivity], list[ParsedDailyMetric]]:
    data = json.loads(path.read_text())
    activities: list[ParsedActivity] = []
    metrics: list[ParsedDailyMetric] = []

    for item in _extract_activities(data):
        act = _normalize_activity(item)
        if act:
            activities.append(act)

    if isinstance(data, dict):
        for key in ("dailySummaries", "wellness", "metrics", "daily_metrics"):
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    m = _normalize_daily(item)
                    if m:
                        metrics.append(m)

    return activities, metrics
