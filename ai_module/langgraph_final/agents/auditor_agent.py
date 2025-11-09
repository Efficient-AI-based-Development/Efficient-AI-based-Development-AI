# ai_module/langgraph_final/agents/auditor_agent.py

import json
from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from langchain_community.chat_models import FakeListChatModel
from app.core.config import settings


# auditor 결과(다음 행동, 피드백, 검토목록) 출력 형식 정의
class AuditorOutput(BaseModel):
    next_action: Literal["REFINEMENT", "PASS"] = Field(...)
    feedback: str = Field(...)
    subtasks_review: List[Dict[str, Any]] = Field(default_factory=list)


# auditor 결과 모킹 생성
def get_mock_auditor_output() -> AuditorOutput:
    return AuditorOutput(next_action="PASS", feedback="충분. PASS.", subtasks_review=[])


# auditor LLM 초기화
def initialize_auditor_llm() -> BaseChatModel:
    m = settings.LLM_MODEL_AUDITOR
    if not settings.UPSTAGE_API_KEY:
        return FakeListChatModel(
            responses=[json.dumps(get_mock_auditor_output().model_dump())],
            name=f"MOCK-AUDITOR-{m}",
        )
    if "solar" in m.lower():
        return ChatUpstage(
            model=m, temperature=0.0, upstage_api_key=settings.UPSTAGE_API_KEY
        )
    raise ValueError(f"Unsupported LLM Model for Auditor: {m}")


# auditor 체인 구성 및 구조화 출력
def create_auditor_chain() -> Runnable:
    llm = initialize_auditor_llm()
    system_prompt = """
    당신은 Planner가 생성한 SubTask 목록을 검토하는 소프트웨어 아키텍트입니다.

    [검증 목표]
    상위 Task 설명과 SubTask 목록을 비교하여 충분히 세분화되었는지, 역할 분배가 적절한지 판단합니다.

    [PASS 판단 기준]
    - SubTask가 5개 이상이거나,
    - AI/Backend/Frontend 세 역할 중 최소 2개 이상이 포함되어 있고,
    - 각 SubTask가 실행 가능한 단위(제목+설명+의존성)가 갖추어져 있다면 PASS.

    [출력 규칙]
    - 충분하면 next_action='PASS'
    - 부족하면 next_action='REFINEMENT'
    - feedback에 구체적 이유 작성

    응답은 다음 Pydantic 스키마를 따르는 JSON만 출력:
    {{
    "next_action": "REFINEMENT" | "PASS",
    "feedback": "string",
      "subtasks_review": [ ... ]
    }}
    """
    human_prompt = "상위 Task: {parent_task_description}\nSubTask JSON: {subtasks_json}"
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_prompt)]
    )
    return prompt | llm.with_structured_output(AuditorOutput)
