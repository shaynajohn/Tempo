from datetime import datetime
from pathlib import Path

import pandas as pd
from dateutil import parser as date_parser

from app.ingestion.types import ParsedActivity, ParsedDailyMetric


def parse_garmin_csv(path: Path) -> tuple[list[ParsedActivity], list[ParsedDailyMetric]]:
    df = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in df.columns}
    activities: list[ParsedActivity] = []
    metrics: list[ParsedDailyMetric] = []

    if _is_activity_export(cols):
        for _, row in df.iterrows():
            act = _row_to_activity(row, cols)
            if act:
                activities.append(act)
    elif _is_wellness_export(cols):
        for _, row in df.iterrows():
            m = _row_to_daily(row, cols)
            if m:
                metrics.append(m)

    return activities, metrics


def _is_activity_export(cols: dict[str, str]) -> bool:
    return any(k in cols for k in ("distance", "activity type", "activity name", "date"))


def _is_wellness_export(cols: dict[str, str]) -> bool:
    return any(k in cols for k in ("sleep", "resting heart rate", "hrv", "stress"))


def _get(row, cols: dict[str, str], *keys: str):
    for k in keys:
        lk = k.lower()
        if lk in cols:
            v = row[cols[lk]]
            if pd.notna(v):
                return v
    return None


def _row_to_activity(row, cols: dict[str, str]) -> ParsedActivity | None:
    date_val = _get(row, cols, "Date", "Activity Date", "Start Time")
    if date_val is None:
        return None
    started = date_parser.parse(str(date_val))

    dist = _get(row, cols, "Distance")
    dist_m = None
    if dist is not None:
        dist_f = float(dist)
        dist_m = dist_f * 1000 if dist_f < 100 else dist_f

    duration = _get(row, cols, "Time", "Moving Time", "Elapsed Time")
    duration_s = _parse_duration(duration)

    pace = _get(row, cols, "Avg Pace", "Average Pace")
    pace_s = _parse_pace(pace)

    return ParsedActivity(
        external_id=str(_get(row, cols, "Activity ID", "Id") or f"csv-{started.isoformat()}"),
        activity_type=str(_get(row, cols, "Activity Type", "Type") or "running").lower(),
        name=str(_get(row, cols, "Activity Name", "Title") or ""),
        started_at=started,
        distance_m=dist_m,
        duration_s=duration_s,
        avg_hr=_float(_get(row, cols, "Avg HR", "Average HR")),
        max_hr=_float(_get(row, cols, "Max HR")),
        avg_cadence=_float(_get(row, cols, "Avg Cadence", "Average Cadence")),
        avg_pace_s_per_km=pace_s,
        elevation_gain_m=_float(_get(row, cols, "Elevation Gain")),
        calories=_int(_get(row, cols, "Calories")),
        training_load=_float(_get(row, cols, "Training Effect", "Training Load")),
    )


def _row_to_daily(row, cols: dict[str, str]) -> ParsedDailyMetric | None:
    date_val = _get(row, cols, "Date", "Calendar Date")
    if date_val is None:
        return None
    return ParsedDailyMetric(
        metric_date=date_parser.parse(str(date_val)).date(),
        resting_hr=_float(_get(row, cols, "Resting Heart Rate", "Resting HR")),
        hrv_ms=_float(_get(row, cols, "HRV", "HRV Status")),
        sleep_hours=_float(_get(row, cols, "Sleep Hours", "Sleep Duration")),
        sleep_score=_int(_get(row, cols, "Sleep Score")),
        stress_avg=_float(_get(row, cols, "Stress", "Average Stress")),
        vo2_max=_float(_get(row, cols, "VO2 Max", "Vo2Max")),
    )


def _parse_duration(val) -> float | None:
    if val is None:
        return None
    s = str(val).strip()
    if ":" in s:
        parts = s.split(":")
        parts = [float(p) for p in parts]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
    try:
        return float(s)
    except ValueError:
        return None


def _parse_pace(val) -> float | None:
    if val is None:
        return None
    s = str(val).strip()
    if ":" in s:
        parts = [float(p) for p in s.split(":")]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
    try:
        return float(s)
    except ValueError:
        return None


def _float(v) -> float | None:
    try:
        return float(v) if v is not None and pd.notna(v) else None
    except (TypeError, ValueError):
        return None


def _int(v) -> int | None:
    try:
        return int(v) if v is not None and pd.notna(v) else None
    except (TypeError, ValueError):
        return None
