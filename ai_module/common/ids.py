# ai_module/common/ids.py

from __future__ import annotations
from typing import Any, Dict, List


# Taskdml ID/역할/부모 연결 표준화
def normalize_ids(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload

    items: List[Dict[str, Any]] = payload.get("items", [])
    all_subtasks: List[Dict[str, Any]] = payload.get("all_subtasks", [])

    id_map: Dict[str, str] = {}

    # items 내부 subtasks에 새 ID 부여
    for item in items:
        tid = item["task_id"]
        seq = 1
        for st in item.get("subtasks", []):
            old_id = st.get("subtask_id", "")
            new_id = f"ST-{tid}-{seq:02d}"
            id_map[old_id] = new_id
            st["subtask_id"] = new_id
            st["dependencies"] = [id_map.get(d, d) for d in st.get("dependencies", [])]
            seq += 1

    # all_subtasks 에도 동일한 규칙 적용
    for st in all_subtasks:
        old_id = st.get("subtask_id", "")
        if old_id in id_map:
            st["subtask_id"] = id_map[old_id]
        st["dependencies"] = [id_map.get(d, d) for d in st.get("dependencies", [])]

    return {"items": items, "all_subtasks": all_subtasks}
