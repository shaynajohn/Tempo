from __future__ import annotations

from datetime import date, timedelta
from statistics import median
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.daily_metric import DailyMetric


async def compute_readiness(db: AsyncSession) -> dict[str, Any]:
    metrics = (
        await db.execute(select(DailyMetric).order_by(DailyMetric.metric_date))
    ).scalars().all()
    activities = (
        await db.execute(select(Activity).order_by(Activity.started_at))
    ).scalars().all()

    if not metrics and not activities:
        return {
            "score": 0,
            "level": "unknown",
            "recommendation": "Import activities and wellness data to estimate readiness.",
            "factors": [],
            "latest_metric_date": None,
            "metrics": {},
            "training": {},
        }

    anchor = _anchor_date(metrics, activities)
    latest = _latest_metric_on_or_before(metrics, anchor)
    score = 70.0
    factors: list[dict[str, Any]] = []

    if latest:
        score += _score_sleep(latest, factors)
        score += _score_resting_hr(metrics, latest, factors)
        score += _score_stress(latest, factors)
        score += _score_body_battery(latest, factors)
    else:
        factors.append(
            {
                "label": "No recent wellness data",
                "impact": "neutral",
                "detail": "Readiness is based mostly on training load.",
            }
        )

    training_delta, training_summary = _score_training_load(activities, anchor, factors)
    score += training_delta

    score = max(0, min(100, round(score)))
    level = _level(score)

    return {
        "score": score,
        "level": level,
        "recommendation": _recommendation(level, factors),
        "factors": factors,
        "latest_metric_date": latest.metric_date.isoformat() if latest else None,
        "metrics": _metric_summary(latest),
        "training": training_summary,
    }


def _anchor_date(metrics: list[DailyMetric], activities: list[Activity]) -> date:
    dates: list[date] = []
    if metrics:
        dates.append(max(m.metric_date for m in metrics))
    if activities:
        dates.append(max(a.started_at.date() for a in activities))
    return max(dates) if dates else date.today()


def _latest_metric_on_or_before(
    metrics: list[DailyMetric], anchor: date
) -> DailyMetric | None:
    eligible = [m for m in metrics if m.metric_date <= anchor]
    return max(eligible, key=lambda m: m.metric_date) if eligible else None


def _score_sleep(latest: DailyMetric, factors: list[dict[str, Any]]) -> float:
    delta = 0.0
    if latest.sleep_hours is not None:
        if latest.sleep_hours >= 7.5:
            delta += 8
            _factor(factors, "Sleep duration", "positive", f"{latest.sleep_hours:.1f}h")
        elif latest.sleep_hours < 5.5:
            delta -= 22
            _factor(factors, "Short sleep", "negative", f"{latest.sleep_hours:.1f}h")
        elif latest.sleep_hours < 6.5:
            delta -= 12
            _factor(factors, "Low sleep", "negative", f"{latest.sleep_hours:.1f}h")

    if latest.sleep_score is not None:
        if latest.sleep_score >= 80:
            delta += 6
            _factor(factors, "Sleep quality", "positive", f"score {latest.sleep_score}")
        elif latest.sleep_score < 60:
            delta -= 10
            _factor(factors, "Sleep quality", "negative", f"score {latest.sleep_score}")
    return delta


def _score_resting_hr(
    metrics: list[DailyMetric], latest: DailyMetric, factors: list[dict[str, Any]]
) -> float:
    if latest.resting_hr is None:
        return 0.0

    baseline_values = [
        m.resting_hr
        for m in metrics
        if m.resting_hr is not None
        and latest.metric_date - timedelta(days=45) <= m.metric_date < latest.metric_date
    ]
    if len(baseline_values) < 5:
        return 0.0

    baseline = median(baseline_values)
    diff = latest.resting_hr - baseline
    if diff >= 7:
        _factor(factors, "Resting HR spike", "negative", f"+{diff:.0f} bpm vs baseline")
        return -20
    if diff >= 4:
        _factor(factors, "Elevated resting HR", "negative", f"+{diff:.0f} bpm")
        return -12
    if diff <= -3:
        _factor(factors, "Resting HR below baseline", "positive", f"{diff:.0f} bpm")
        return 5
    return 0.0


def _score_stress(latest: DailyMetric, factors: list[dict[str, Any]]) -> float:
    if latest.stress_avg is None:
        return 0.0
    if latest.stress_avg >= 50:
        _factor(factors, "High stress", "negative", f"avg {latest.stress_avg:.0f}")
        return -15
    if latest.stress_avg >= 40:
        _factor(factors, "Elevated stress", "negative", f"avg {latest.stress_avg:.0f}")
        return -8
    if latest.stress_avg <= 25:
        _factor(factors, "Low stress", "positive", f"avg {latest.stress_avg:.0f}")
        return 5
    return 0.0


def _score_body_battery(latest: DailyMetric, factors: list[dict[str, Any]]) -> float:
    if latest.body_battery is None:
        return 0.0
    if latest.body_battery >= 70:
        _factor(factors, "Body Battery", "positive", str(latest.body_battery))
        return 10
    if latest.body_battery < 35:
        _factor(factors, "Low Body Battery", "negative", str(latest.body_battery))
        return -15
    return 0.0


def _score_training_load(
    activities: list[Activity], anchor: date, factors: list[dict[str, Any]]
) -> tuple[float, dict[str, Any]]:
    distances = [
        (a.started_at.date(), (a.distance_m or 0) / 1000)
        for a in activities
        if a.distance_m
    ]
    last_7 = sum(km for d, km in distances if anchor - timedelta(days=6) <= d <= anchor)
    prev_28 = sum(
        km for d, km in distances if anchor - timedelta(days=34) <= d < anchor - timedelta(days=6)
    )
    baseline_week = prev_28 / 4 if prev_28 else 0
    days_since_run = min(
        ((anchor - d).days for d, km in distances if d <= anchor),
        default=None,
    )

    delta = 0.0
    if baseline_week and last_7 > baseline_week * 1.3 and last_7 > 8:
        delta -= 12
        _factor(
            factors,
            "Volume spike",
            "negative",
            f"{last_7:.1f} km this week vs {baseline_week:.1f} km baseline",
        )
    elif baseline_week and last_7 < baseline_week * 0.6:
        delta += 4
        _factor(factors, "Reduced load", "positive", f"{last_7:.1f} km last 7 days")

    if days_since_run is not None and days_since_run >= 2:
        delta += 4
        _factor(factors, "Recovery window", "positive", f"{days_since_run} days since run")

    return delta, {
        "last_7_days_km": round(last_7, 1),
        "baseline_weekly_km": round(baseline_week, 1),
        "days_since_run": days_since_run,
    }


def _metric_summary(metric: DailyMetric | None) -> dict[str, Any]:
    if not metric:
        return {}
    return {
        "resting_hr": metric.resting_hr,
        "sleep_hours": metric.sleep_hours,
        "sleep_score": metric.sleep_score,
        "stress_avg": metric.stress_avg,
        "body_battery": metric.body_battery,
    }


def _level(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 55:
        return "moderate"
    if score > 0:
        return "low"
    return "unknown"


def _recommendation(level: str, factors: list[dict[str, Any]]) -> str:
    negative = [f["label"].lower() for f in factors if f["impact"] == "negative"]
    if level == "high":
        return "Good day for quality work if your legs feel normal."
    if level == "moderate":
        return "Keep the plan flexible: easy running or controlled intensity is safest."
    if level == "low":
        reasons = ", ".join(negative[:2]) if negative else "multiple recovery signals"
        return f"Recovery looks constrained by {reasons}. Prefer rest or an easy run."
    return "Import more data to estimate workout readiness."


def _factor(
    factors: list[dict[str, Any]], label: str, impact: str, detail: str
) -> None:
    factors.append({"label": label, "impact": impact, "detail": detail})
