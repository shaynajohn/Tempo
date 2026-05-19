from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.ai.agents.state import AgentState
from app.analytics.fatigue import compute_fatigue
from app.analytics.patterns import discover_patterns
from app.config import settings


async def fatigue_node(state: AgentState, config) -> dict[str, Any]:
    db = config["configurable"]["db"]
    fatigue = await compute_fatigue(db)
    summary = (
        f"Fatigue score {fatigue.current_score} ({fatigue.risk_level}). "
        f"{fatigue.recommendation}"
    )
    return {"fatigue_summary": summary}


async def insight_node(state: AgentState, config) -> dict[str, Any]:
    db = config["configurable"]["db"]
    patterns = await discover_patterns(db)
    return {
        "patterns": [
            {"title": p.title, "description": p.description, "confidence": p.confidence}
            for p in patterns
        ]
    }


async def coaching_node(state: AgentState, config) -> dict[str, Any]:
    if not settings.openai_api_key:
        return {"run_explanation": "Configure OPENAI_API_KEY for AI coaching."}

    db = config["configurable"]["db"]
    activity_id = state.get("activity_id")

    context = f"Fatigue: {state.get('fatigue_summary')}\nPatterns: {state.get('patterns')}"
    if activity_id:
        from app.ai.explanations import explain_run

        insight = await explain_run(db, activity_id)
        context += f"\nLatest run: {insight.body}"

    llm = ChatOpenAI(model=settings.chat_model, api_key=settings.openai_api_key)
    resp = await llm.ainvoke(
        [
            SystemMessage(content="Synthesize a brief coaching report (3-4 sentences)."),
            HumanMessage(content=context),
        ]
    )
    return {"final_report": resp.content.strip(), "run_explanation": resp.content.strip()}


async def forecast_node(state: AgentState, config) -> dict[str, Any]:
    fatigue = state.get("fatigue_summary", "")
    risk = "high" in fatigue.lower() or "elevated" in fatigue.lower()
    forecast = (
        "Next 48h: prioritize easy running or rest."
        if risk
        else "Next 48h: good window for a quality session if you feel fresh."
    )
    return {"forecast": forecast}
