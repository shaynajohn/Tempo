from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    activity_id: int | None
    fatigue_summary: str
    patterns: list[dict[str, Any]]
    run_explanation: str
    forecast: str
    final_report: str
