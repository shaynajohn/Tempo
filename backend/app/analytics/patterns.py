from collections import defaultdict
from datetime import timedelta

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.daily_metric import DailyMetric
from app.schemas.analytics import PatternOut


async def discover_patterns(db: AsyncSession) -> list[PatternOut]:
    activities = (
        await db.execute(select(Activity).order_by(Activity.started_at))
    ).scalars().all()

    if len(activities) < 5:
        return [
            PatternOut(
                pattern_type="insufficient_data",
                title="Need more runs",
                description="Import at least 5 activities to discover training patterns.",
                evidence={"count": len(activities)},
                confidence=0.0,
            )
        ]

    patterns: list[PatternOut] = []
    patterns.extend(_mileage_sweet_spot(activities))
    patterns.extend(_recovery_window(activities))
    patterns.extend(_temperature_performance(activities))
    patterns.extend(_time_of_day(activities))
    return patterns


def _mileage_sweet_spot(activities: list[Activity]) -> list[PatternOut]:
    df = pd.DataFrame(
        [
            {
                "week": a.started_at.isocalendar()[:2],
                "distance_km": (a.distance_m or 0) / 1000,
                "pace": a.avg_pace_s_per_km,
            }
            for a in activities
            if a.avg_pace_s_per_km
        ]
    )
    if df.empty:
        return []

    weekly = df.groupby("week").agg(distance_km=("distance_km", "sum"), pace=("pace", "mean"))
    weekly = weekly[weekly["distance_km"] > 0]
    if len(weekly) < 3:
        return []

    # Bin weekly volume and find fastest average pace bin
    weekly["vol_bin"] = pd.cut(weekly["distance_km"], bins=min(4, len(weekly)))
    by_bin = weekly.groupby("vol_bin", observed=True)["pace"].mean()
    best_bin = by_bin.idxmin()
    low, high = best_bin.left, best_bin.right

    return [
        PatternOut(
            pattern_type="mileage_sweet_spot",
            title="Ideal weekly mileage range",
            description=(
                f"Your fastest average paces cluster around {low:.0f}–{high:.0f} km/week. "
                "Volume above this range may correlate with slower efforts."
            ),
            evidence={"km_low": float(low), "km_high": float(high), "weeks_analyzed": len(weekly)},
            confidence=min(0.85, 0.5 + len(weekly) * 0.05),
        )
    ]


def _recovery_window(activities: list[Activity]) -> list[PatternOut]:
    runs = sorted(activities, key=lambda a: a.started_at)
    gaps: list[tuple[int, float]] = []
    for i in range(1, len(runs)):
        if not runs[i].avg_pace_s_per_km or not runs[i - 1].started_at:
            continue
        gap_days = (runs[i].started_at.date() - runs[i - 1].started_at.date()).days
        gaps.append((gap_days, runs[i].avg_pace_s_per_km))

    if len(gaps) < 5:
        return []

    df = pd.DataFrame(gaps, columns=["gap_days", "pace"])
    two_day = df[df["gap_days"] == 2]["pace"].mean()
    one_day = df[df["gap_days"] == 1]["pace"].mean()
    if pd.isna(two_day) or pd.isna(one_day):
        return []

    if two_day < one_day * 0.98:
        return [
            PatternOut(
                pattern_type="recovery_window",
                title="2-day recovery pattern",
                description=(
                    "Runs after 2 consecutive recovery days tend to be faster than "
                    "runs with only 1 day between hard efforts."
                ),
                evidence={"pace_after_2d": float(two_day), "pace_after_1d": float(one_day)},
                confidence=0.7,
            )
        ]
    return []


def _temperature_performance(activities: list[Activity]) -> list[PatternOut]:
    with_temp = [a for a in activities if a.temperature_c and a.avg_pace_s_per_km]
    if len(with_temp) < 5:
        return []

    cool = [a.avg_pace_s_per_km for a in with_temp if a.temperature_c < 18]
    warm = [a.avg_pace_s_per_km for a in with_temp if a.temperature_c >= 24]
    if len(cool) < 2 or len(warm) < 2:
        return []

    cool_avg, warm_avg = np.mean(cool), np.mean(warm)
    if cool_avg < warm_avg * 0.97:
        return [
            PatternOut(
                pattern_type="conditions",
                title="Cool-weather advantage",
                description=(
                    "Your strongest performances tend to occur below ~65°F (18°C). "
                    f"Cool runs average {cool_avg:.0f}s/km vs {warm_avg:.0f}s/km in heat."
                ),
                evidence={"cool_pace": float(cool_avg), "warm_pace": float(warm_avg)},
                confidence=0.75,
            )
        ]
    return []


def _time_of_day(activities: list[Activity]) -> list[PatternOut]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for a in activities:
        if not a.avg_pace_s_per_km:
            continue
        hour = a.started_at.hour
        if hour < 10:
            buckets["morning"].append(a.avg_pace_s_per_km)
        elif hour < 14:
            buckets["midday"].append(a.avg_pace_s_per_km)
        else:
            buckets["evening"].append(a.avg_pace_s_per_km)

    if len(buckets) < 2:
        return []

    avgs = {k: np.mean(v) for k, v in buckets.items() if len(v) >= 2}
    if not avgs:
        return []

    best = min(avgs, key=avgs.get)
    return [
        PatternOut(
            pattern_type="time_of_day",
            title=f"{best.title()} runs are fastest",
            description=f"Your average pace is strongest during {best} runs.",
            evidence={k: float(v) for k, v in avgs.items()},
            confidence=0.65,
        )
    ]
