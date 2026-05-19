"""LangGraph multi-agent pipeline for coaching insights."""

from typing import Any

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.nodes import (
    coaching_node,
    fatigue_node,
    forecast_node,
    insight_node,
)
from app.ai.agents.state import AgentState


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("fatigue", fatigue_node)
    graph.add_node("insight", insight_node)
    graph.add_node("coaching", coaching_node)
    graph.add_node("forecast", forecast_node)

    graph.set_entry_point("fatigue")
    graph.add_edge("fatigue", "insight")
    graph.add_edge("insight", "coaching")
    graph.add_edge("coaching", "forecast")
    graph.add_edge("forecast", END)

    return graph


async def run_coaching_pipeline(
    db: AsyncSession, activity_id: int | None = None
) -> dict[str, Any]:
    """Run all agents and return consolidated coaching report."""
    graph = build_graph().compile()
    initial: AgentState = {"activity_id": activity_id}
    result = await graph.ainvoke(initial, config={"configurable": {"db": db}})
    return dict(result)
