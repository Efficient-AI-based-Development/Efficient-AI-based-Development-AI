# ai_module/langgraph_final/decomposition_graph.py

import json
from langgraph.graph import END
from langgraph.graph.state import StateGraph

from .graph_state import GraphState
from .agents.planner_agent import create_planner_chain, PlannerOutput
from .agents.auditor_agent import create_auditor_chain, AuditorOutput
from .agents.writer_agent import create_writer_chain, WriterOutput


# planner 실행 및 SubTask 생성
def planner_node(state: GraphState) -> GraphState:
    print("PLANNER start")
    parent_task = state["user_input"]
    if state.get("feedback_message"):
        print(f"REFINE: {state['feedback_message']}")
    chain = create_planner_chain()
    retry = state.get("retry_count", 0) + 1
    try:
        r: PlannerOutput = chain.invoke(
            {
                "parent_task_id": "TASK-AI-001",
                "task_description": parent_task,
                "feedback": state.get("feedback_message", ""),
            }
        )
        subtasks = [t.model_dump() for t in r.subtasks]
        return {
            "subtasks": subtasks,
            "status": "REVIEW_NEEDED",
            "feedback_message": f"Planner ok: {len(subtasks)}",
            "retry_count": retry,
        }
    except Exception as e:
        print(f"PLANNER error: {e}")
        return {
            "subtasks": state.get("subtasks", []),
            "status": "ERROR",
            "feedback_message": f"Planner error: {e}",
            "retry_count": retry,
        }


# auditor 실행 및 다음 상태 결정
def auditor_node(state: GraphState) -> GraphState:
    print("AUDITOR start")
    chain = create_auditor_chain()
    subtasks_json = json.dumps(state["subtasks"], ensure_ascii=False, indent=2)
    try:
        r: AuditorOutput = chain.invoke(
            {
                "parent_task_description": state["user_input"],
                "subtasks_json": subtasks_json,
            }
        )
        return {
            "subtasks": state["subtasks"],
            "status": r.next_action,
            "feedback_message": r.feedback,
        }
    except Exception as e:
        print(f"AUDITOR error: {e}")
        return {
            "subtasks": state["subtasks"],
            "status": "ERROR",
            "feedback_message": f"Auditor error: {e}",
        }


# writer 실행 및 SRS 생성
def writer_node(state: GraphState) -> GraphState:
    print("WRITER start")
    chain = create_writer_chain()
    subtasks_json = json.dumps(state["subtasks"], ensure_ascii=False, indent=2)
    try:
        r: WriterOutput = chain.invoke(
            {
                "parent_task_id": "TASK-AI-001",
                "subtasks_json": subtasks_json,
            }
        )
        print("WRITER done")
        return {
            "subtasks": state["subtasks"],
            "status": "DONE",
            "feedback_message": "SRS done",
            "srs_document": r.srs_document,
        }
    except Exception as e:
        print(f"WRITER error: {e}")
        return {
            "subtasks": state.get("subtasks", []),
            "status": "ERROR",
            "feedback_message": f"Writer error: {e}",
        }


# 상태 기반 분기 결정
MAX_REFINEMENT_ATTEMPTS = 10


def decide_next_step(state: GraphState) -> str:
    print(f"DECISION: {state.get('status')}")
    retry = state.get("retry_count", 0)
    status = state.get("status", "ERROR")
    if status == "PASS":
        return "writer"
    if status == "REFINEMENT":
        if retry >= MAX_REFINEMENT_ATTEMPTS:
            print("REFINE limit. END")
            return END
        return "planner"
    return END


workflow = StateGraph(GraphState)
workflow.add_node("planner", planner_node)
workflow.add_node("auditor", auditor_node)
workflow.add_node("writer", writer_node)
workflow.set_entry_point("planner")
workflow.add_edge("planner", "auditor")
workflow.add_conditional_edges("auditor", decide_next_step)
workflow.add_edge("writer", END)
decomposition_app = workflow.compile()
