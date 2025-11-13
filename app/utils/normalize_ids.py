# app/utils/nomalize_ids.py


def normalize_ids(payload):
    items = payload.get("items", [])
    all_subtasks = payload.get("all_subtasks", [])

    id_map = {}
    for item in items:
        tid = item["task_id"]
        seq = 1
        for st in item.get("subtasks", []):
            new_id = f"ST-{tid}-{seq:02d}"
            id_map[st["subtask_id"]] = new_id
            st["subtask_id"] = new_id
            st["dependencies"] = [id_map.get(d, d) for d in st.get("dependencies", [])]
            seq += 1

    for st in all_subtasks:
        if st["subtask_id"] in id_map:
            st["subtask_id"] = id_map[st["subtask_id"]]
        st["dependencies"] = [id_map.get(d, d) for d in st.get("dependencies", [])]

    return {"items": items, "all_subtasks": all_subtasks}
