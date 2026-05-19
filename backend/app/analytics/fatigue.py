from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.daily_metric import DailyMetric
from app.schemas.analytics import FatigueOut, FatiguePoint


async def compute_fatigue(db: AsyncSession, lookback_days: int = 28) -> FatigueOut:
    end = date.today()
    start = end - timedelta(days=lookback_days)

    activities = (
        await db.execute(
            select(Activity)
            .where(Activity.started_at >= start)
            .order_by(Activity.started_at)
        )
    ).scalars().all()

    metrics = (
        await db.execute(
            select(DailyMetric)
            .where(DailyMetric.metric_date >= start)
            .order_by(DailyMetric.metric_date)
        )
    ).scalars().all()

    act_df = _activities_to_df(activities)
    met_df = _metrics_to_df(metrics)
    trend = _score_series(act_df, met_df, start, end)

    if not trend:
        return FatigueOut(
            current_score=0.0,
            risk_level="unknown",
            trend=[],
            recommendation="Import more activities and wellness data to assess fatigue.",
        )

    current = trend[-1]
    rec = _recommendation(current.score, current.factors)

    return FatigueOut(
        current_score=round(current.score, 1),
        risk_level=current.risk_level,
        trend=trend,
        recommendation=rec,
    )


def _activities_to_df(activities: list[Activity]) -> pd.DataFrame:
    if not activities:
        return pd.DataFrame()
    rows = []
    for a in activities:
        rows.append(
            {
                "date": a.started_at.date(),
                "distance_km": (a.distance_m or 0) / 1000,
                "training_load": a.training_load or 0,
                "pace": a.avg_pace_s_per_km,
            }
        )
    return pd.DataFrame(rows)


def _metrics_to_df(metrics: list[DailyMetric]) -> pd.DataFrame:
    if not metrics:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "date": m.metric_date,
                "resting_hr": m.resting_hr,
                "hrv": m.hrv_ms,
                "sleep_hours": m.sleep_hours,
                "stress": m.stress_avg,
            }
            for m in metrics
        ]
    )


def _score_series(
    act_df: pd.DataFrame, met_df: pd.DataFrame, start: date, end: date
) -> list[FatiguePoint]:
    dates = pd.date_range(start, end, freq="D")
    points: list[FatiguePoint] = []

    for d in dates:
        d_date = d.date()
        factors: list[str] = []
        score = 0.0

        if not act_df.empty:
            week_mask = (act_df["date"] > d_date - timedelta(days=7)) & (
                act_df["date"] <= d_date
            )
            vol = act_df.loc[week_mask, "distance_km"].sum()
            if vol > 60:
                score += 25
                factors.append("high weekly volume")
            elif vol > 45:
                score += 12
                factors.append("elevated volume")

            recent = act_df[act_df["date"] <= d_date].tail(5)
            if len(recent) >= 3 and recent["pace"].notna().sum() >= 2:
                paces = recent["pace"].dropna()
                if paces.iloc[-1] > paces.mean() * 1.04:
                    score += 20
                    factors.append("pace regression")

        if not met_df.empty:
            row = met_df[met_df["date"] == d_date]
            if not row.empty:
                rhr = row.iloc[0].get("resting_hr")
                if rhr and not met_df["resting_hr"].dropna().empty:
                    baseline = met_df["resting_hr"].dropna().median()
                    if rhr > baseline + 5:
                        score += 20
                        factors.append("elevated resting HR")
                sleep = row.iloc[0].get("sleep_hours")
                if sleep is not None and sleep < 6.5:
                    score += 15
                    factors.append("low sleep")
                stress = row.iloc[0].get("stress")
                if stress is not None and stress > 45:
                    score += 10
                    factors.append("high stress")

        risk = "low" if score < 25 else "moderate" if score < 50 else "high"
        points.append(
            FatiguePoint(date=d_date, score=min(score, 100), risk_level=risk, factors=factors)
        )

    return points


def _recommendation(score: float, factors: list[str]) -> str:
    if score < 25:
        return "Recovery looks adequate. Good day for quality work if you feel fresh."
    if score < 50:
        return "Moderate fatigue signals. Consider an easy day or cut intensity by 10–15%."
    factor_str = ", ".join(factors[:3]) if factors else "multiple stressors"
    return f"Elevated burnout risk ({factor_str}). Prioritize sleep and reduce volume this week."
