import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.run_analysis import analyze_run_splits
from app.config import settings
from app.models.activity import Activity
from app.models.insight import Insight

METERS_PER_MILE = 1609.344


SYSTEM_PROMPT = """You are Tempo, an expert running coach analyzing Garmin data.
Write 2-3 sentences explaining what happened in this run — be specific about pace, cadence, HR, and splits.
Reference evidence from the analysis. Avoid generic advice. Sound like a coach who studied the data."""


async def explain_run(db: AsyncSession, activity_id: int) -> Insight:
    activity = await db.get(Activity, activity_id)
    if not activity:
        raise ValueError(f"Activity {activity_id} not found")

    analysis = analyze_run_splits(activity)
    context = _build_context(activity, analysis)

    if not settings.openai_api_key:
        body = _fallback_explanation(activity, analysis)
    else:
        llm = ChatOpenAI(model=settings.chat_model, api_key=settings.openai_api_key)
        resp = await llm.ainvoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=context),
            ]
        )
        body = resp.content.strip()

    insight = Insight(
        insight_type="run_explanation",
        title=f"Run analysis: {activity.name or 'Run'}",
        body=body,
        confidence=0.85,
        activity_id=activity_id,
        metadata_={"analysis": analysis},
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight


def _build_context(activity: Activity, analysis: dict[str, Any]) -> str:
    return json.dumps(
        {
            "name": activity.name,
            "date": activity.started_at.isoformat(),
            "distance_mi": (activity.distance_m or 0) / METERS_PER_MILE,
            "duration_min": (activity.duration_s or 0) / 60,
            "avg_hr": activity.avg_hr,
            "avg_cadence": activity.avg_cadence,
            "avg_pace_s_per_mi": (
                activity.avg_pace_s_per_km / 0.621371
                if activity.avg_pace_s_per_km
                else None
            ),
            "temperature_c": activity.temperature_c,
            "analysis": analysis,
            "summary": activity.summary_text,
        },
        indent=2,
    )


def _fallback_explanation(activity: Activity, analysis: dict[str, Any]) -> str:
    parts = [
        f"On {activity.started_at.strftime('%b %d')}, "
        f"you covered {(activity.distance_m or 0) / METERS_PER_MILE:.1f} mi."
    ]
    if analysis.get("pace_fade_mile"):
        parts.append(
            f"Your pace dropped significantly after mile {analysis['pace_fade_mile']} "
            f"despite {'stable' if analysis.get('cadence_stable') else 'variable'} cadence, "
            "likely indicating cardiovascular fatigue rather than muscular fatigue."
        )
    elif analysis.get("negative_split"):
        parts.append("You negative-split this run — stronger in the second half.")
    else:
        parts.append("Pacing was relatively even throughout.")
    return " ".join(parts)
