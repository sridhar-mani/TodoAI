from pydantic import BaseModel, validator
from typing import Optional, List, Any
from datetime import datetime
from models.task_model import TaskStatus, TaskPriority, Task


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM

class TaskResponce(TaskBase):
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskDelete(BaseModel):
    msg: str
    deleted_task: int

class TaskList(BaseModel):
    tasks: list[TaskResponce]
    total: int
    skip: int
    limit: int

class TaskSearch(BaseModel):
    tasks: List[TaskResponce]
    search_term: str
    total_found: int

class TaskCreate(TaskBase):
    @validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v
    
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    @validator('title')
    def title_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("Title cannot be empty")
        return v



class TaskFilter(BaseModel):
    status: Optional[TaskStatus] =None
    priority: Optional[TaskPriority] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None

class TaskSearch(BaseModel):
    tasks: List[TaskResponce]
    search_term:str
    total_found:int

class StandardResponce(BaseModel):
    msg: str
    data: Any = None