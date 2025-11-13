# ai_module/langgraph_final/graph_state.py

from typing import TypedDict, List


# LangGraph 공유 상태 스키마
class GraphState(TypedDict):
    user_input: str
    subtasks: List[dict]
    feedback_message: str
    status: str
    retry_count: int
    srs_document: str | None
