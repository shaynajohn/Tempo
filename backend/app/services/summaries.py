from app.ingestion.types import ParsedActivity

METERS_PER_MILE = 1609.344
KM_TO_MILES = 0.621371


def format_pace(pace_s_per_km: float | None) -> str:
    if not pace_s_per_km:
        return "N/A"
    sec_per_mile = pace_s_per_km / KM_TO_MILES
    m, s = divmod(int(sec_per_mile), 60)
    return f"{m}:{s:02d}/mi"


def format_distance(m: float | None) -> str:
    if not m:
        return "N/A"
    return f"{m / METERS_PER_MILE:.2f} mi"


def build_activity_summary(p: ParsedActivity) -> str:
    """Text summary for embeddings and semantic search."""
    parts = [
        f"{p.name or 'Run'} on {p.started_at.strftime('%Y-%m-%d')}",
        f"distance {format_distance(p.distance_m)}",
        f"pace {format_pace(p.avg_pace_s_per_km)}",
    ]
    if p.avg_hr:
        parts.append(f"avg HR {p.avg_hr:.0f} bpm")
    if p.avg_cadence:
        parts.append(f"cadence {p.avg_cadence:.0f} spm")
    if p.temperature_c:
        parts.append(f"temp {p.temperature_c:.0f}°C")
    if p.training_load:
        parts.append(f"training load {p.training_load:.1f}")
    if p.splits:
        split_desc = _describe_splits(p.splits)
        if split_desc:
            parts.append(split_desc)
    return ". ".join(parts) + "."


def _describe_splits(splits: list[dict]) -> str:
    paces = [s.get("avg_pace_s_per_km") for s in splits if s.get("avg_pace_s_per_km")]
    if len(paces) < 2:
        return ""
    first_half = sum(paces[: len(paces) // 2]) / (len(paces) // 2)
    second_half = sum(paces[len(paces) // 2 :]) / (len(paces) - len(paces) // 2)
    if second_half > first_half * 1.03:
        return "pace faded in second half"
    if second_half < first_half * 0.97:
        return "negative split pattern"
    return "even pacing"
