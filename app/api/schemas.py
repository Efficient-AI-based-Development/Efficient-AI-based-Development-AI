# app/api/schemas.py


from typing import List, Literal
from pydantic import BaseModel, Field


# PRD/Task 생성용 사용자 입력 형식
class ProjectInput(BaseModel):
    user_input: str = Field(...)


# 개별 Task 항목 형식
class Task(BaseModel):
    task_id: int = Field(...)
    title: str = Field(...)
    description: str = Field(...)
    assigned_role: str = Field(...)
    priority: str = Field(...)


# Task list 출력 형식
class TaskListOutput(BaseModel):
    project_name: str = Field(...)
    tasks: List[Task] = Field(...)


# PRD 문서 출력 형식
class PRDOutput(BaseModel):
    prd_document: str = Field(...)


# 분해 요청 입력 형식
class DecompositionInput(BaseModel):
    parent_task_id: str = Field(...)
    task_description: str = Field(...)


# 분해된 Subtask 형식
class SubTask(BaseModel):
    subtask_id: str = Field(...)
    title: str = Field(...)
    description: str = Field(...)
    assigned_role: Literal["AI", "Backend", "Frontend"] = Field(...)
    dependencies: List[str] = Field(default_factory=list)


# planner 결과 출력 형식
class PlannerOutput(BaseModel):
    parent_task_id: str = Field(...)
    analysis: str = Field(...)
    subtasks: List[SubTask] = Field(default_factory=list)
