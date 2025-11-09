# ai_module/langchain_mvp/prd_chain.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_upstage import ChatUpstage
from langchain_community.chat_models import FakeListChatModel
from langchain.chains import LLMChain
from langchain_core.language_models import BaseChatModel
from app.core.config import settings


# PRD 작성용 LLM 초기화
def initialize_writer_llm() -> BaseChatModel:
    m = settings.LLM_MODEL_WRITER
    if not settings.UPSTAGE_API_KEY:
        resp = f"# [MOCK] PRD for {settings.APP_NAME}\n\n## 개요\n모킹 실행.\n"
        return FakeListChatModel(responses=[resp], name=f"MOCK-{m}")
    if "solar" in m.lower():
        return ChatUpstage(
            model=m, temperature=0.7, upstage_api_key=settings.UPSTAGE_API_KEY
        )
    raise ValueError(f"Unsupported LLM Model: {m}")


# PRD 생성 chain 구성
def create_prd_generation_chain():
    llm = initialize_writer_llm()
    template = (
        "제품 관리자 역할. 입력 기반 PRD 초안 작성. 마크다운 출력.\n입력: {user_input}"
    )
    prompt = ChatPromptTemplate.from_template(template)
    return LLMChain(llm=llm, prompt=prompt, output_key="prd_document")


# PRD 생성 실행
def generate_prd(user_input: str) -> str:
    chain = create_prd_generation_chain()
    r = chain.invoke({"user_input": user_input})
    return r.get("prd_document", "# PRD 생성 실패")
