# app/api/endpoints.py

import asyncio
from fastapi import APIRouter, HTTPException, Body, Depends
from ai_module.common.ids import normalize_ids
from ai_module.chains.pm_chain import (
    generate_pm_metadata,
    update_pm_metadata,
)
from ai_module.chains.task_ai_chain import (
    modify_task,
    add_task,
)
from ai_module.chains.prd_chain import (
    generate_prd,
    create_prd_chat_chain,
)
from ai_module.chains.srs_chain import (
    generate_srs,
    create_srs_chat_chain,
)
from ai_module.chains.userstory_chain import (
    generate_userstory,
    create_userstory_chat_chain,
)
from ai_module.chains.tasklist_chain import generate_tasklist
from ai_module.chains.codegen_chain import (
    implement_subtask,
    implement_interactive_subtask,
)
from ai_module.graphs.decomposition_graph import decomposition_app, GraphState
from app.api.schemas import (
    ProjectInput,
    PMAgentInput,
    PMAgentOutput,
    PMAgentChatInput,
    ProjectMetadata,
    TaskModifyInput,
    TaskAddInput,
    TaskAIOutput,
    PRDOutput,
    SRSOutput,
    UserStoryOutput,
    TaskListInput,
    TaskListOutput,
    DecompositionInput,
    DecompositionOutput,
    DecompositionItem,
    SubTaskWithParent,
    RepoSnapshot,
    CodegenOutput,
    SubTask,
    UserStoryInput,
    SRSInput,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# PM Agent 초기 메타데이터 추출 API 엔드포인트
@router.post(
    "/pm", response_model=PMAgentOutput, summary="PM Agent - 프로젝트 메타데이터 추출"
)
def pm_agent_endpoint(
    pm_input: PMAgentInput = Body(
        ...,
        example={
            "user_input": "AI 기반 Todo 앱을 만들고 싶어요. React와 FastAPI로 개발하고, GPT-4를 사용할 예정이에요."
        },
    )
):
    try:
        logger.info("[PM-Agent] 요청 수신")
        logger.debug("[PM-Agent] 입력: %s", pm_input.user_input[:120])
        result = generate_pm_metadata(pm_input.user_input)
        logger.info(
            "[PM-Agent] 메타데이터 추출 완료 (프로젝트명=%s)",
            result.metadata.project_name,
        )
        return result
    except Exception as e:
        logger.exception("[PM-Agent] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"PM Agent 서버 오류: {e}")


# PM Agent 대화형 수정 API 엔드포인트
@router.post(
    "/pm/chat",
    response_model=PMAgentOutput,
    summary="PM Agent - 대화형 메타데이터 수정",
)
def pm_agent_chat(
    pm_chat_input: PMAgentChatInput = Body(
        ...,
        example={
            "current_metadata": {
                "project_name": "AI Todo App",
                "main_color": "#3498db",
                "page_count": 5,
                "feature_count": 8,
                "ai_model": "GPT-4",
                "tech_stack": [
                    "React",
                    "TypeScript",
                    "FastAPI",
                    "Python",
                    "PostgreSQL",
                    "Docker",
                ],
                "service_description": "AI 기반 Todo 앱",
            },
            "user_feedback": "메인 컬러를 녹색 계열로 바꾸고, 페이지 수를 3개로 줄여줘",
        },
    )
):
    try:
        logger.info("[PM-Agent-Chat] 요청 수신")
        logger.debug("[PM-Agent-Chat] 피드백: %s", pm_chat_input.user_feedback[:120])
        result = update_pm_metadata(
            pm_chat_input.current_metadata, pm_chat_input.user_feedback
        )
        logger.info(
            "[PM-Agent-Chat] 메타데이터 수정 완료 (프로젝트명=%s)",
            result.metadata.project_name,
        )
        return result
    except Exception as e:
        logger.exception("[PM-Agent-Chat] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"PM Agent Chat 서버 오류: %e")


# Task AI Agent - Task 수정 API 엔드포인트
@router.post(
    "/task/modify",
    response_model=TaskAIOutput,
    summary="Task AI Agent - 기존 Task 수정",
)
def task_modify_endpoint(
    task_input: TaskModifyInput = Body(
        ...,
        example={
            "current_task": {
                "task_id": 1,
                "title": "회원 가입 API 구현",
                "description": "이메일과 비밀번호로 회원가입하는 API를 만들기",
                "assigned_role": "Backend",
                "priority": 8,
                "tag": "개발",
            },
            "user_feedback": "OAuth 소셜 로그인도 추가하고, 우선순위를 10으로 올려줘",
        },
    )
):
    try:
        logger.info("[Task-AI-Modify] 요청 수신 (task_id=%s)", task_input.current_task.task_id)
        logger.debug("[Task-AI-Modify] 피드백: %s", task_input.user_feedback[:120])
        result = modify_task(task_input.current_task, task_input.user_feedback)
        logger.info(
            "[Task-AI-Modify] Task 수정 완료 (task_id=%s, title=%s)",
            result.task.task_id,
            result.task.title,
        )
        return result
    except Exception as e:
        logger.exception("[Task-AI-Modify] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"Task Modify 서버 오류: {e}")


# Task AI Agent - Task 추가 API 엔드포인트
@router.post(
    "/task/add",
    response_model=TaskAIOutput,
    summary="Task AI Agent - 새 Task 추가",
)
def task_add_endpoint(
    task_input: TaskAddInput = Body(
        ...,
        example={
            "existing_tasks": [
                {
                    "task_id": 1,
                    "title": "회원 가입 API 구현",
                    "description": "이메일과 비밀번호로 회원가입하는 API를 만들기",
                    "assigned_role": "Backend",
                    "priority": 8,
                    "tag": "개발",
                },
                {
                    "task_id": 2,
                    "title": "로그인 화면 UI",
                    "description": "로그인 폼 디자인 및 구현",
                    "assigned_role": "Frontend",
                    "priority": 7,
                    "tag": "개발",
                },
            ],
            "user_request": "비밀번호 찾기 기능도 추가해줘. 이메일로 인증코드를 보내는 방식으로",
            "project_context": "회원 인증 시스템을 구축하는 프로젝트",
        },
    )
):
    try:
        logger.info("[Task-AI-Add] 요청 수신 (existing_tasks=%d)", len(task_input.existing_tasks))
        logger.debug("[Task-AI-Add] 요청: %s", task_input.user_request[:120])
        result = add_task(
            task_input.existing_tasks,
            task_input.user_request,
            task_input.project_context,
        )
        logger.info(
            "[Task-AI-Add] Task 추가 완료 (new_task_id=%s, title=%s)",
            result.task.task_id,
            result.task.title,
        )
        return result
    except Exception as e:
        logger.exception("[Task-AI-Add] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"Task Add 서버 오류: %e")


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
        prd = generate_prd(project_input.user_input)
        logger.info("[PRD] 문서 생성 완료 (길이=%d)", len(prd.prd_document or ""))
        return prd
    except Exception as e:
        logger.exception("[PRD] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"PRD 서버 오류: %e")


@router.post("/prd/chat", response_model=PRDOutput, summary="PRD 대화형 수정")
def prd_chat(
    prd_document: str = Body(...),
    user_feedback: str = Body(...),
):
    try:
        logger.info("[PRD-CHAT] 요청 수신")
        logger.debug(
            "[PRD-CHAT] 사용자 요청 미리보기: %s",
            user_feedback[:120] if user_feedback else "",
        )

        chain = create_prd_chat_chain()
        result = chain.invoke(
            {"prd_document": prd_document, "user_feedback": user_feedback}
        )

        logger.info(
            "[PRD-CHAT] 수정 완료 (길이=%d)",
            len(getattr(result, "prd_document", "") or ""),
        )
        return result
    except Exception as e:
        logger.exception("[PRD-CHAT] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"PRD Chat 서버 오류: %e")


@router.post("/srs", response_model=SRSOutput, summary="SRS 생성")
def generate_srs_endpoint(
    payload: SRSInput = Body(
        ..., example={"user_input": "이 PRD를 기반으로 SRS 초안을 생성해줘"}
    )
):
    try:
        logger.info("[SRS] 요청 수신")
        logger.debug("[SRS] 입력 미리보기: %s", payload.user_input[:120])
        srs = generate_srs(payload.user_input)
        logger.info("[SRS] 문서 생성 완료 (길이=%d)", len(srs.srs_document or ""))
        return srs
    except Exception as e:
        logger.exception("[SRS] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"SRS 서버 오류: %e")


# SRS 문서 대화형 생성/수정 API 엔드포인트
@router.post("/srs/chat", response_model=SRSOutput, summary="SRS 대화형 수정")
def srs_chat(
    srs_document: str = Body(...),
    user_feedback: str = Body(...),
):
    try:
        logger.info("[SRS-CHAT] 요청 수신")
        logger.debug(
            "[SRS-CHAT] 사용자 요청 미리보기: %s",
            user_feedback[:120] if user_feedback else "",
        )

        chain = create_srs_chat_chain()
        result = chain.invoke(
            {"srs_document": srs_document, "user_feedback": user_feedback}
        )

        logger.info(
            "[SRS-CHAT] 수정 완료 (길이=%d)",
            len(getattr(result, "srs_document", "") or ""),
        )
        return result
    except Exception as e:
        logger.exception("[SRS-CHAT] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"SRS Chat 서버 오류: %e")


@router.post(
    "/userstory",
    response_model=UserStoryOutput,
    summary="User Story 생성",
)
def generate_userstory_endpoint(
    payload: UserStoryInput = Body(
        ...,
        example={"user_input": "회원가입/로그인 플로우에 대한 User Story를 작성해줘"},
    )
):
    try:
        logger.info("[USERSTORY] 요청 수신")
        logger.debug("[USERSTORY] 입력 미리보기: %s", payload.user_input[:120])
        us = generate_userstory(payload.user_input)
        logger.info(
            "[USERSTORY] 문서 생성 완료 (길이=%d)",
            len(us.user_story or ""),
        )
        return us
    except Exception as e:
        logger.exception("[USERSTORY] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"User Story 서버 오류: %e")


# User Story 대화형 생성/수정 API 엔드포인트
@router.post(
    "/userstory/chat", response_model=UserStoryOutput, summary="User Story 대화형 수정"
)
def userstory_chat(
    user_story: str = Body(...),
    user_feedback: str = Body(...),
):
    try:
        logger.info("[USERSTORY-CHAT] 요청 수신")
        logger.debug(
            "[USERSTORY-CHAT] 사용자 요청 미리보기: %s",
            user_feedback[:120] if user_feedback else "",
        )

        chain = create_userstory_chat_chain()
        result = chain.invoke(
            {"user_story": user_story, "user_feedback": user_feedback}
        )

        logger.info(
            "[USERSTORY-CHAT] 수정 완료 (길이=%d)",
            len(getattr(result, "user_story", "") or ""),
        )
        return result
    except Exception as e:
        logger.exception("[USERSTORY-CHAT] 오류 발생: %s", e)
        raise HTTPException(status_code=500, detail=f"User Story Chat 서버 오류: %e")


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
        raise HTTPException(status_code=500, detail=f"Task List 서버 오류: %e")


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
    logger.info("[DecomposeBatch] 완료 (success=%d, fail=%d)", len(items), len(errors))
    return output


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
            detail=f"Codegen 서버 오류: %e",
        )


# 대화형 코드 생성(사용자 피드백 반영) API 엔드포인트
@router.post("/codegen/chat", response_model=CodegenOutput, summary="대화형 Codegen")
def interactive_codegen(
    subtask: SubTask = Body(...),
    repo_snapshot: RepoSnapshot = Body(...),
    user_feedback: str = Body(...),
):
    try:
        logger.info("[Codegen-CHAT] 요청 수신 (subtask_id=%s)", subtask.subtask_id)
        logger.debug(
            "[Codegen-CHAT] 사용자 피드백 미리보기: %s",
            user_feedback[:120] if user_feedback else "",
        )

        result = implement_interactive_subtask(subtask, repo_snapshot, user_feedback)

        logger.info(
            "[Codegen-CHAT] 완료: subtask_id=%s, changes=%d",
            result.subtask_id,
            len(result.changes),
        )
        return result
    except Exception as e:
        logger.exception("[Codegen-CHAT] 오류 발생: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Codegen Chat 서버 오류: %e",
        )
