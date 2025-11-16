# app/api/endpoints.py

import asyncio
from fastapi import APIRouter, HTTPException, Body
from ai_module.common.ids import normalize_ids
from ai_module.chains.prd_chain import generate_prd
from ai_module.chains.tasklist_chain import generate_tasklist
from ai_module.chains.codegen_chain import implement_subtask
from ai_module.graphs.decomposition_graph import decomposition_app, GraphState
from app.api.schemas import (
    ProjectInput,
    PRDOutput,
    TaskListInput,
    TaskListOutput,
    DecompositionInput,
    DecompositionOutput,
    DecompositionItem,
    SubTaskWithParent,
    RepoSnapshot,
    CodegenOutput,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# PRD 생성 API 엔드포인트
@router.post("/prd", response_model=PRDOutput, summary="PRD 생성")
def generate_prd_endpoint(
    project_input: ProjectInput = Body(
        ..., example={"user_input": "AI 기반 개발 지원 시스템 PRD 작성"}
    )
):
    try:
        logger.info("[PRD] 요청 수신")
        logger.debug("[PRD] 입력 미리보기: %s", project_input.user_input[:120])
        md = generate_prd(project_input.user_input)
        logger.info("[PRD] 문서 생성 완료 (길이=%d)", len(md or ""))
        return PRDOutput(prd_document=md)
    except Exception as e:
        logger.exception("[PRD] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"PRD 서버 오류: {e}")


# Task List 생성 API 엔드포인트
@router.post("/tasks", response_model=TaskListOutput, summary="Task List 생성")
def generate_tasklist_endpoint(
    project_input: TaskListInput = Body(
        ...,
        example={"prd_document": "PRD 내용", "user_input": "MVP 구현 태스크 목록 생성"},
    )
):
    try:
        logger.info("[TaskList] 요청 수신")
        logger.debug("[TaskList] 입력 미리보기: %s", project_input.user_input[:120])
        md = generate_tasklist(
            prd_document=project_input.prd_document,
            user_input=project_input.user_input,
        )
        logger.info("[TaskList] 생성 완료")
        return md
    except Exception as e:
        logger.exception("[TaskList] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"Task List 서버 오류: {e}")


# 여러 Task를 병렬로 SubTask/SRS로 분해하는 API 엔드포인트
@router.post(
    "/decompose",
    response_model=DecompositionOutput,
    summary="여러 Task 병렬 분해",
)
async def decompose(inp: DecompositionInput = Body(...)):
    logger.info("[Decompose] 시작 (tasks=%d)", len(inp.tasks))
    sem = asyncio.Semaphore(5)
    cfg = {"recursion_limit": 50}

    async def run_one(t):
        """
        단일 Task를 LangGraph decomposition_app으로 실행해 DecompositionItem으로 변환.
        """
        logger.debug(
            "[Decompose] run_one 시작 (task_id=%s, title=%s)", t.task_id, t.title
        )
        init: GraphState = {
            "user_input": t.description,
            "subtasks": [],
            "feedback_message": "",
            "status": "INITIAL",
            "retry_count": 0,
            "srs_document": None,
        }
        async with sem:
            final = await asyncio.to_thread(decomposition_app.invoke, init, cfg)

        if final.get("status") == "ERROR":
            msg = f"Task {t.task_id} 분해 실패: {final.get('feedback_message')}"
            logger.error("[Decompose] %s", msg)
            raise HTTPException(status_code=500, detail=msg)

        logger.debug(
            "[Decompose] task_id=%s subtasks=%d",
            t.task_id,
            len(final.get("subtasks", [])),
        )

        subtasks = []
        for st in final.get("subtasks", []):
            st = {**st, "parent_task_id": t.task_id}
            subtasks.append(SubTaskWithParent(**st))

        return DecompositionItem(
            task_id=t.task_id,
            title=t.title,
            assigned_role=t.assigned_role,
            subtasks=subtasks,
            srs_document=final.get("srs_document"),
        )

    results = await asyncio.gather(
        *(run_one(t) for t in inp.tasks), return_exceptions=True
    )

    items: list[DecompositionItem] = []
    errors: list[str] = []
    for r in results:
        if isinstance(r, Exception):
            logger.error("[DecomposeBatch] 개별 실패: %s", r)
            errors.append(str(r))
        else:
            items.append(r)

    if not items and errors:
        logger.error("[DecomposeBatch] 전부 실패: %s", "; ".join(errors))
        raise HTTPException(status_code=500, detail="; ".join(errors))

    all_subtasks: list[SubTaskWithParent] = []
    for it in items:
        all_subtasks.extend(it.subtasks)

    output = DecompositionOutput(items=items, all_subtasks=all_subtasks)
    normalized_dict = normalize_ids(output.model_dump())
    normalized = DecompositionOutput(**normalized_dict)
    logger.info("[DecomposeBatch] 완료 (success=%d, fail=%d)", len(items), len(errors))
    return normalized


# 단일 SubTask에 대한 코드 결과를 생성하는 API 엔드포인트
@router.post("/codegen", response_model=CodegenOutput)
async def generate_code_changes(
    subtask: SubTaskWithParent = Body(...),
) -> CodegenOutput:
    logger.info("[Codegen] 요청 수신")
    try:
        empty_snapshot = RepoSnapshot(
            root="",
            branch="",
            commit="",
            files=[],
        )

        result = implement_subtask(
            subtask=subtask,
            repo_snapshot=empty_snapshot,
        )

        logger.info(
            "[Codegen] 완료: subtask_id=%s, changes=%d",
            result.subtask_id,
            len(result.changes),
        )
        return result
    except Exception as e:
        logger.exception("[Codegen] 오류 발생: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Codegen 서버 오류: {e}",
        )
