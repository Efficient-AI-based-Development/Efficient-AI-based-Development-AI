# app/api/schemas.py

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


# 입력
class ProjectInput(BaseModel):
    user_input: str = Field(..., description="프로젝트 개요/요구사항 자연어 입력")


# PRD
class PRDOutput(BaseModel):
    prd_document: str


# TaskList
class TaskListInput(BaseModel):
    prd_document: Optional[str] = None
    user_input: Optional[str] = None


class Task(BaseModel):
    task_id: int
    title: str
    description: str
    assigned_role: Literal["AI", "Backend", "Frontend"]
    priority: Literal["High", "Medium", "Low"]


class TaskListOutput(BaseModel):
    project_name: str
    tasks: List[Task]


# Planner
class SubTask(BaseModel):
    subtask_id: str
    title: str
    description: str
    assigned_role: Literal["AI", "Backend", "Frontend"]
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


# Decompose
class DecompositionInput(BaseModel):
    tasks: List[Task]


class SubTaskWithParent(SubTask):
    parent_task_id: int


class DecompositionItem(BaseModel):
    task_id: int
    title: str
    assigned_role: Literal["AI", "Backend", "Frontend"]
    subtasks: List[SubTaskWithParent]
    srs_document: Optional[str] = None


class DecompositionOutput(BaseModel):
    items: List[DecompositionItem]
    all_subtasks: List[SubTaskWithParent]
