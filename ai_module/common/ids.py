# ai_module/common/ids.py

from __future__ import annotations
import re, time, uuid
from typing import Iterable, List, Dict, Any, Literal, TypeVar, Generic
from pydantic import BaseModel

ROLE = Literal["AI", "Backend", "Frontend"]
ROLE_MAP = {
    "ai": "AI",
    "be": "Backend",
    "fe": "Frontend",
    "backend": "Backend",
    "frontend": "Frontend",
}

ID_TASK_RE = re.compile(r"^T-[A-Z0-9]{2,8}-\d{4}$")
ID_SUBTASK_RE = re.compile(r"^ST-(T-[A-Z0-9]{2,8}-\d{4})-\d{4}$")

T = TypeVar("T", bound=BaseModel)


def _seq(n: int) -> str:
    """4자리 시퀀스 포맷."""
    return f"{n:04d}"


def _project_tag(project: str | None) -> str:
    """프로젝트 태그 정규화."""
    tag = (project or "MVP").upper().replace("-", "")[:8]
    return tag if tag else "MVP"


def make_task_id(project: str | None, n: int) -> str:
    """태스크 ID 생성: T-<PROJECT>-NNNN."""
    return f"T-{_project_tag(project)}-{_seq(n)}"


def make_subtask_id(task_id: str, n: int) -> str:
    """서브태스크 ID 생성: ST-<TASK_ID>-NNNN."""
    return f"ST-{task_id}-{_seq(n)}"


def normalize_ids(data: Any, project: str | None = None) -> Any:
    """
    범용 ID 정규화 엔트리포인트.
    TaskListOutput, DecompositionBatchOutput 등 모델/리스트/딕셔너리 입력을 자동 처리.
    """
    if isinstance(data, dict):
        if "subtasks" in data:
            task_id = (
                data.get("task_id")
                or data.get("parent_task_id")
                or random_task_id(project)
            )
            data["subtasks"] = normalize_ids_for_subtasks(data["subtasks"], task_id)
            data["task_id"] = task_id
        else:
            data = normalize_ids_for_task(data, project)
        return data
    elif isinstance(data, list):
        return coerce_batch(data, project)
    else:
        return data


def random_task_id(project: str | None = None) -> str:
    """랜덤 태스크 ID 생성."""
    base = _project_tag(project)
    tail = uuid.uuid4().hex[:4].upper()
    return f"T-{base}-{tail}"


def normalize_role(role: str | None) -> ROLE:
    """역할 문자열 표준화."""
    if not role:
        return "AI"
    return ROLE_MAP.get(role.lower(), role if role in {"AI", "Backend", "Frontend"} else "AI")  # type: ignore


def is_task_id(s: str) -> bool:
    """태스크 ID 형식 검증."""
    return bool(ID_TASK_RE.match(s or ""))


def is_subtask_id(s: str) -> bool:
    """서브태스크 ID 형식 검증."""
    return bool(ID_SUBTASK_RE.match(s or ""))


def normalize_ids_for_task(
    task: Dict[str, Any], project: str | None = None
) -> Dict[str, Any]:
    """단일 태스크의 ID/역할 표준화."""
    t = dict(task)
    if not is_task_id(t.get("task_id", "")):
        t["task_id"] = t.get("task_id") or random_task_id(project)
    t["assigned_role"] = normalize_role(t.get("assigned_role"))
    return t


def normalize_ids_for_subtasks(
    subtasks: List[Dict[str, Any]], task_id: str, start: int = 1
) -> List[Dict[str, Any]]:
    """서브태스크 배열의 ID/역할/부모 연결 표준화."""
    out = []
    k = start
    for s in subtasks:
        item = dict(s)
        item["assigned_role"] = normalize_role(item.get("assigned_role"))
        item["parent_task_id"] = task_id
        if not is_subtask_id(item.get("subtask_id", "")):
            item["subtask_id"] = make_subtask_id(task_id, k)
        k += 1
        out.append(item)
    return out


def reindex_subtasks(
    subtasks: List[Dict[str, Any]], task_id: str
) -> List[Dict[str, Any]]:
    """서브태스크 ID를 0001부터 재부여."""
    return normalize_ids_for_subtasks(subtasks, task_id, 1)


def coerce_batch(
    tasks: Iterable[Dict[str, Any]], project: str | None = None
) -> List[Dict[str, Any]]:
    """배치 태스크들의 ID/역할 표준화."""
    out = []
    n = 1
    for t in tasks:
        fixed = normalize_ids_for_task(
            t, project if t.get("project") is None else t.get("project")
        )
        if not is_task_id(fixed["task_id"]):
            fixed["task_id"] = make_task_id(_project_tag(project), n)
            n += 1
        out.append(fixed)
    return out
