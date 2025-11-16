# app/api/schemas.py

from typing import List, Literal, Optional, Dict, Any

from pydantic import BaseModel, Field


# 프로젝트 입력
class ProjectInput(BaseModel):
    user_input: str = Field(..., description="프로젝트 개요/요구사항 자연어 입력")


# PRD
class PRDOutput(BaseModel):
    prd_document: str


# Task List
class TaskListInput(BaseModel):
    prd_document: Optional[str] = None
    user_input: Optional[str] = None


class Task(BaseModel):
    task_id: int
    title: str
    description: str
    assigned_role: Literal["Backend", "Frontend"]
    priority: int = Field(..., ge=0, le=10)
    tag: Literal["개발", "디자인", "문서"]


class TaskListOutput(BaseModel):
    project_name: str
    tasks: List[Task]


# Planner / SubTask
class SubTask(BaseModel):
    subtask_id: str
    title: str
    description: str
    assigned_role: Literal["Backend", "Frontend"]
    dependencies: List[str] = Field(default_factory=list)


class WriterOutput(BaseModel):
    parent_task_id: str
    srs_document: str


class AuditorOutput(BaseModel):
    next_action: Literal["REFINEMENT", "PASS"]
    feedback: str
    subtasks_review: List[Dict[str, Any]] = Field(default_factory=list)


class PlannerOutput(BaseModel):
    parent_task_id: str
    analysis: str
    subtasks: List[SubTask] = Field(default_factory=list)


# Decomposition
class DecompositionInput(BaseModel):
    tasks: List[Task]


class SubTaskWithParent(SubTask):
    parent_task_id: int


class DecompositionItem(BaseModel):
    task_id: int
    title: str
    assigned_role: Literal["Backend", "Frontend"]
    subtasks: List[SubTaskWithParent]
    srs_document: Optional[str] = None


class DecompositionOutput(BaseModel):
    items: List[DecompositionItem]
    all_subtasks: List[SubTaskWithParent]


# Codegen / Repo 스냅샷
class CodeChange(BaseModel):
    file_path: str
    action: Literal["create", "update", "delete"]
    content: str | None = None


class CodegenOutput(BaseModel):
    subtask_id: str
    subtask_title: str
    assigned_role: Literal["Backend", "Frontend"]
    summary: str
    changes: List[CodeChange] = Field(default_factory=list)
    notes: str | None = None


class RepoFile(BaseModel):
    path: str
    content: str


class RepoSnapshot(BaseModel):
    root: Optional[str] = None
    branch: Optional[str] = None
    commit: Optional[str] = None
    files: List[RepoFile] = Field(default_factory=list)
