# ai_module/chains/prd_chain.py

from __future__ import annotations
import json
from langchain_core.prompts import ChatPromptTemplate
from ai_module.common.llm import get_llm, with_structured
from ai_module.common.prompts import prd_system
from app.api.schemas import PRDOutput


# PRD 초안 생성을 위한 LLM 파이프라인
def create_prd_generation_chain():
    """
    사용자 입력을 받아 PRD 문서를 생성하는 LLM 체인을 구성한다.
    """
    llm = with_structured(get_llm("writer"), PRDOutput)
    system_template = prd_system()
    human_prompt = "제품 요구사항 입력: {user_input}"

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_template), ("human", human_prompt)]
    )

    schema_text = json.dumps(
        PRDOutput.model_json_schema(), ensure_ascii=False, indent=2
    )
    return prompt | llm, schema_text


# PRD 문서 생성
def generate_prd(user_input: str) -> str:
    """
    사용자 입력 문자열을 받아 PRD 문서를 생성하고 문자열 형태로 반환한다.
    """
    chain, schema_text = create_prd_generation_chain()
    result = chain.invoke({"user_input": user_input, "schema_text": schema_text})

    if isinstance(result, PRDOutput):
        return result.prd_document
    if isinstance(result, dict) and "prd_document" in result:
        return result["prd_document"]
    return "# PRD 생성 실패"
