# ai_module/common/text.py

import json
import re

_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$", re.MULTILINE)


def strip_code_fences(s: str | None) -> str:
    """LLM이 반환한 코드펜스를 제거하고 깨끗한 문자열 반환."""
    if not s:
        return ""
    return re.sub(_FENCE_RE, "", s).strip()


def escape_json_for_template(d: dict) -> str:
    """ChatPromptTemplate에서 {} 충돌 방지를 위해 JSON의 중괄호를 이스케이프."""
    return (
        json.dumps(d, ensure_ascii=False, indent=2)
        .replace("{", "{{")
        .replace("}", "}}")
    )
