from typing import Any

from app.models.activity import Activity


def analyze_run_splits(activity: Activity) -> dict[str, Any]:
    """Rule-based split analysis feeding the AI explanation layer."""
    splits = activity.splits or []
    if not splits:
        return {"has_splits": False}

    paces = [s.get("avg_pace_s_per_km") for s in splits if s.get("avg_pace_s_per_km")]
    cadences = [s.get("avg_cadence") for s in splits if s.get("avg_cadence")]

    result: dict[str, Any] = {"has_splits": True, "split_count": len(paces)}

    if len(paces) >= 4:
        mid = len(paces) // 2
        first_avg = sum(paces[:mid]) / mid
        second_avg = sum(paces[mid:]) / (len(paces) - mid)
        fade_pct = (second_avg - first_avg) / first_avg if first_avg else 0

        result["first_half_pace"] = first_avg
        result["second_half_pace"] = second_avg
        result["pace_fade_pct"] = round(fade_pct * 100, 1)
        result["negative_split"] = fade_pct < -0.02

        if fade_pct > 0.04:
            # Approximate mile where fade started (assuming ~1mi splits)
            fade_idx = _find_fade_point(paces)
            result["pace_fade_mile"] = fade_idx + 1

    if len(cadences) >= 2:
        cadence_std = _std(cadences)
        result["cadence_stable"] = cadence_std < 3.0
        result["cadence_std"] = round(cadence_std, 1)

    if len(paces) >= 2:
        result["fastest_split_pace"] = min(paces)
        result["slowest_split_pace"] = max(paces)

    return result


def _find_fade_point(paces: list[float]) -> int:
    for i in range(1, len(paces)):
        if paces[i] > paces[i - 1] * 1.03:
            return i
    return len(paces) // 2


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
