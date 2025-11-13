# ai_module/langgraph_final/agents/auditor_agent.py

import json
from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from ai_module.common.llm import get_llm, with_structured
from ai_module.common.prompts import auditor_system
from app.utils.logger import get_logger
from app.api.schemas import AuditorOutput

logger = get_logger(__name__)


def create_auditor_chain() -> Runnable:
    llm = with_structured(get_llm("auditor", temperature=0.0), AuditorOutput)
    system_prompt = auditor_system()
    schema_text = json.dumps(
        AuditorOutput.model_json_schema(), ensure_ascii=False, indent=2
    )
    human_prompt = "상위 Task: {parent_task_description}\nSubTask JSON: {subtasks_json}"
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_prompt)]
    ).partial(schema_text=schema_text)
    return prompt | llm
