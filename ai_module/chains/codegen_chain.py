# ai_module/chains/codegen_chain.py

from __future__ import annotations

import json
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from ai_module.common.llm import get_llm, with_structured
from ai_module.common.prompts import codegen_system
from app.api.schemas import SubTask, CodegenOutput, RepoSnapshot


# CodegenOutput Pydantic 스키마를 LLM 프롬프트에 안전하게 넣기 위한 유틸
def _escape_json_for_template(d: dict) -> str:
    """
    ChatPromptTemplate이 JSON의 { } 를 프롬프트 변수로 오인하지 않도록 이스케이프.
    CodegenOutput.model_json_schema() 결과에만 사용한다.
    """
    return (
        json.dumps(d, ensure_ascii=False, indent=2)
        .replace("{", "{{")
        .replace("}", "}}")
    )


# SubTask + RepoSnapshot을 입력으로 받아 CodegenOutput을 생성하는 LLM 체인 생성
def create_codegen_chain() -> Runnable:
    """
    SubTask와 RepoSnapshot을 기반으로 코드 변경 제안(CodegenOutput)을 생성하는 체인.
    """
    llm = with_structured(get_llm("codegen", temperature=0.25), CodegenOutput)

    schema_text = _escape_json_for_template(CodegenOutput.model_json_schema())
    system_prompt = codegen_system(schema_text)

    human_prompt = (
        "다음은 구현해야 할 SubTask와 현재 레포지토리 스냅샷입니다.\n\n"
        "=== SubTask JSON ===\n"
        "{subtask_json}\n\n"
        "=== RepoSnapshot JSON ===\n"
        "{repo_snapshot_json}\n\n"
        "위 정보를 바탕으로, 반드시 CodegenOutput 스키마에 맞는 JSON만 출력하세요."
    )

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_prompt)]
    )
    return prompt | llm


# 단일 SubTask를 실제 CodegenOutput 결과로 변환하는 헬퍼 함수
def implement_subtask(
    subtask: SubTask, repo_snapshot: Optional[RepoSnapshot] = None
) -> CodegenOutput:
    """
    단일 SubTask를 실제 코드 변경 제안(CodegenOutput)으로 구현한다.
    - 입력: SubTask, RepoSnapshot (없으면 None 허용)
    - 출력: CodegenOutput (LLM 응답을 Pydantic으로 파싱)
    """
    chain = create_codegen_chain()

    subtask_json = subtask.model_dump_json(ensure_ascii=False, indent=2)

    if repo_snapshot:
        repo_snapshot_json = repo_snapshot.model_dump_json(ensure_ascii=False, indent=2)
    else:
        # RepoSnapshot이 없을 때는 최소한의 빈 구조를 전달
        repo_snapshot_json = json.dumps(
            {"root": "", "branch": "", "commit": "", "files": []},
            ensure_ascii=False,
            indent=2,
        )

    result = chain.invoke(
        {
            "subtask_json": subtask_json,
            "repo_snapshot_json": repo_snapshot_json,
        }
    )

    if isinstance(result, CodegenOutput):
        return result

    if isinstance(result, dict):
        return CodegenOutput(**result)

    raise ValueError(f"Unexpected LLM result type for CodegenOutput: {type(result)}")
