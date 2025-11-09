# ai_module/langgraph_final/agents/writer_agent.py

import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from langchain_community.chat_models import FakeListChatModel
from app.core.config import settings


# writer 출력형식
class WriterOutput(BaseModel):
    parent_task_id: str = Field(...)
    srs_document: str = Field(...)


# writer LLM 초기화
def initialize_writer_llm() -> BaseChatModel:
    m = settings.LLM_MODEL_WRITER
    if not settings.UPSTAGE_API_KEY:
        mock = WriterOutput(
            parent_task_id="TASK-AI-001",
            srs_document="# SRS\n## 개요\n생성.\n## 기능 요구사항\n기술.\n## 품질 요구사항\n기술.\n## 추적성\n기술.\n## 결론\n정리.",
        )
        return FakeListChatModel(
            responses=[json.dumps(mock.model_dump())], name=f"MOCK-WRITER-{m}"
        )
    if "solar" in m.lower():
        return ChatUpstage(
            model=m, temperature=0.4, upstage_api_key=settings.UPSTAGE_API_KEY
        )
    raise ValueError(f"Unsupported LLM Model: {m}")


# writer 체인 구성 및 SRS 생성
def create_writer_chain() -> Runnable:
    llm = initialize_writer_llm()

    system_prompt = """
    당신은 소프트웨어 요구사항 명세서(SRS) 작성 전문가입니다.
    다음의 정보를 기반으로 완전한 SRS 문서를 **Markdown 형식**으로 작성하세요.

    [입력]
    - 상위 Task ID
    - SubTask 목록(JSON 형식)
    
    [출력 규칙]
    1. SRS 문서는 반드시 Markdown (#, ##, ###) 형식을 따르세요.
    2. 주요 항목:
       - Overview
       - Functional Requirements
       - Non-functional Requirements
       - Traceability
       - Conclusion
    3. 응답은 다음 Pydantic 스키마에 정확히 부합해야 합니다:
    {{
      "parent_task_id": "string",
      "srs_document": "Markdown 텍스트"
    }}
    """

    human_prompt = "Task ID: {parent_task_id}\nSubTask JSON: {subtasks_json}"
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_prompt)]
    )
    return prompt | llm.with_structured_output(WriterOutput)
