# ai_module/langchain_mvp/tasklist_chain.py

import json
from app.core.config import settings
from app.api.schemas import Task, TaskListOutput
from langchain_community.chat_models import FakeListChatModel
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage


# Task planner LLM 초기화
def initialize_task_planner_llm() -> BaseChatModel:
    m = settings.LLM_MODEL_WRITER
    if not settings.UPSTAGE_API_KEY:
        mock = TaskListOutput(
            project_name=f"[MOCK] {settings.APP_NAME}",
            tasks=[
                Task(
                    task_id=1,
                    title="FastAPI 백엔드 구축",
                    description="환경 구성 실행",
                    assigned_role="Backend",
                    priority="High",
                ),
                Task(
                    task_id=2,
                    title="PRD/Task 체인 구현",
                    description="체인 연동 실행",
                    assigned_role="AI",
                    priority="High",
                ),
                Task(
                    task_id=3,
                    title="FE 대시보드 세팅",
                    description="UI 초기화 실행",
                    assigned_role="Frontend",
                    priority="Medium",
                ),
            ],
        )
        return FakeListChatModel(
            responses=[json.dumps(mock.model_dump())], name=f"MOCK-TASK-{m}"
        )
    if "solar" in m.lower():
        return ChatUpstage(
            model=m, temperature=0.3, upstage_api_key=settings.UPSTAGE_API_KEY
        )
    raise ValueError(f"Unsupported LLM Model: {m}")


# Task list 생성 chain 구성
def create_tasklist_generation_chain() -> Runnable:
    llm = initialize_task_planner_llm()
    system = f"프로젝트 플래너 역할. 입력 분석. {TaskListOutput.__name__} JSON 구조로 출력. 역할은 AI/Backend/Frontend 사용."
    human = "입력: {user_input}"
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
    return prompt | llm.with_structured_output(TaskListOutput)


# Task list 생성 실행
def generate_tasklist(user_input: str) -> TaskListOutput:
    chain = create_tasklist_generation_chain()
    return chain.invoke({"user_input": user_input})
