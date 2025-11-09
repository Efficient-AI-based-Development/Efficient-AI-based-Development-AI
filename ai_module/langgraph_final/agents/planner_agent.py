# ai_module/langgraph_final/agents/planner_agent.py

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from langchain_community.chat_models import FakeListChatModel
from app.api.schemas import PlannerOutput, SubTask
from app.core.config import settings


# planner LLM 초기화
def initialize_planner_llm():
    m = settings.LLM_MODEL_DECOMPOSER
    if not settings.UPSTAGE_API_KEY:
        mock = PlannerOutput(
            parent_task_id="TASK-AI-001",
            analysis="분해 완료.",
            subtasks=[
                SubTask(
                    subtask_id="ST-1",
                    title="환경 설정",
                    description="패키지 설치.",
                    assigned_role="AI",
                    dependencies=[],
                ),
                SubTask(
                    subtask_id="ST-2",
                    title="스키마 정의",
                    description="모델 확정.",
                    assigned_role="AI",
                    dependencies=["ST-1"],
                ),
                SubTask(
                    subtask_id="ST-3",
                    title="FastAPI 연동",
                    description="엔드포인트 연결.",
                    assigned_role="Backend",
                    dependencies=["ST-2"],
                ),
                SubTask(
                    subtask_id="ST-4",
                    title="FE 연계",
                    description="UI 훅업.",
                    assigned_role="Frontend",
                    dependencies=["ST-3"],
                ),
                SubTask(
                    subtask_id="ST-5",
                    title="테스트",
                    description="케이스 작성.",
                    assigned_role="AI",
                    dependencies=["ST-3"],
                ),
            ],
        )
        return FakeListChatModel(
            responses=[json.dumps(mock.model_dump())], name=f"MOCK-PLANNER-{m}"
        )
    if "solar" in m.lower():
        return ChatUpstage(
            model=m, temperature=0.3, upstage_api_key=settings.UPSTAGE_API_KEY
        )
    raise ValueError(f"Unsupported LLM Model: {m}")


# planner 체인 구성 및 구조화 출력
def create_planner_chain() -> Runnable:
    llm = initialize_planner_llm()
    system_prompt = """
    당신은 프로젝트 플래너 에이전트입니다.
    상위 Task를 실행 가능한 SubTask로 분해하고, 아래 스키마를 정확히 따르세요.

    [출력 스키마 규칙]
    {{
        "parent_task_id": "string",
        "analysis": "string",
        "subtasks": [
            {{
                "subtask_id": "string",
                "title": "string",
                "description": "string",
                "assigned_role": "AI|Backend|Frontend",
                "dependencies": ["string"]
            }}
        ]
    }}
    ** 추가 키 금지 / 필드명 대소문자 변경 금지 / JSON 외 텍스트 금지 **
    """
    human_prompt = (
        "Task ID: {parent_task_id}\n설명: {task_description}\n피드백: {feedback}"
    )
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_prompt)]
    )
    return prompt | llm.with_structured_output(PlannerOutput)
