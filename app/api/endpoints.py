# app/api/endpoints.py

import logging
from fastapi import APIRouter, HTTPException, Body
from app.api.schemas import ProjectInput, PRDOutput, TaskListOutput, DecompositionInput
from ai_module.langchain_mvp.prd_chain import generate_prd
from ai_module.langchain_mvp.tasklist_chain import generate_tasklist
from ai_module.langgraph_final.decomposition_graph import decomposition_app, GraphState
from ai_module.langgraph_final.agents.planner_agent import PlannerOutput

logger = logging.getLogger(__name__)
router = APIRouter()


# PRD 생성 API
@router.post("/prd", response_model=PRDOutput, summary="PRD 생성")
def generate_prd_endpoint(
    project_input: ProjectInput = Body(
        ..., example={"user_input": "AI 기반 개발 지원 시스템 PRD 작성"}
    )
):
    try:
        logger.info(f"PRD start: {project_input.user_input[:50]}...")
        md = generate_prd(project_input.user_input)
        return PRDOutput(prd_document=md)
    except Exception as e:
        logger.error(f"PRD error: {e}")
        raise HTTPException(status_code=500, detail=f"PRD 서버 오류: {e}")


# Task list 생성 API
@router.post("/tasks", response_model=TaskListOutput, summary="Task List 생성")
def generate_tasklist_endpoint(
    project_input: ProjectInput = Body(
        ..., example={"user_input": "MVP 구현 태스크 목록 생성"}
    )
):
    try:
        logger.info(f"Tasks start: {project_input.user_input[:50]}...")
        return generate_tasklist(project_input.user_input)
    except Exception as e:
        logger.error(f"Tasks error: {e}")
        raise HTTPException(status_code=500, detail=f"Task List 서버 오류: {e}")


# Task 분해 순환 실행 API
@router.post("/decompose", response_model=PlannerOutput, summary="Task 분해")
async def decompose_task_endpoint(
    decomposition_input: DecompositionInput = Body(
        ...,
        example={
            "parent_task_id": "TASK-AI-001",
            "task_description": "LangGraph로 Task를 SubTask로 분해하는 에이전트 구축",
        },
    )
):
    try:
        logger.info(f"Decompose start: {decomposition_input.parent_task_id}")
        initial_state: GraphState = {
            "user_input": decomposition_input.task_description,
            "subtasks": [],
            "feedback_message": "",
            "status": "INITIAL",
            "retry_count": 0,
        }
        final_state = decomposition_app.invoke(
            initial_state, config={"recursion_limit": 50}
        )
        if final_state["status"] == "ERROR":
            raise HTTPException(
                status_code=500,
                detail=f"Task 분해 오류: {final_state['feedback_message']}",
            )
        out = PlannerOutput(
            parent_task_id=decomposition_input.parent_task_id,
            analysis=final_state.get("feedback_message", "분해 완료"),
            subtasks=final_state["subtasks"],
        )
        if "srs_document" in final_state:
            out.analysis = "SRS 문서 생성 완료"
            print(final_state["srs_document"][:500])
        return out
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Decompose error: {e}")
        raise HTTPException(status_code=500, detail=f"Task 분해 서버 오류: {e}")
