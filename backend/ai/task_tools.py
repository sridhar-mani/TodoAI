from langchain_core.tools import tool
from fastapi import Depends
from sqlalchemy.orm import Session
from databases.connection import get_db
from services.task_service import TaskService
from schema.task_schema import TaskResponce, TaskDelete, TaskCreate, TaskFilter, TaskList, TaskStatus, TaskUpdate
from datetime import datetime

@tool('create_Task')
def create_task(title:str, description:str = '', due_date:datetime =None, priority: str = None):
    """Create a new task with the given details."""
    db = next(get_db())
    task_service = TaskService(db=db)
    task = task_service.create_task(
        TaskCreate(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority if priority else TaskStatus.PENDING
        )
    )
    return task.__dict__

@tool('update_task')
def update_task(task_id:int, title:str = None, description:str = None, due_date: datetime = None, priority: str = None, status: str = None):
    """Update an existing task by ID or title."""
    db = next(get_db())
    task_service = TaskService(db=db)
    if task_id is None and title:
        found = task_service.get_task_by_title(title=title)
        task_id = found.id if found else None
    if task_id is None:
        return {"error": "Task ID or title must be provided"}
    task = task_service.update_task(task_id=task_id, task_data= TaskUpdate(
        title=title, description=description, due_date=due_date, priority=priority, status=status
    ))
    return task.__dict__ if task else {"error": "Task not found"}

@tool('delete_task')
def delete_task(task_id:int):
    """Delete a task by its ID."""
    db = next(get_db())
    task_service = TaskService(db=db)
    deleted_task = task_service.delete_task(task_id=task_id)
    if not deleted_task:
        return {"error": "Task not found"}
    return TaskDelete(msg="Task deleted successfully", deleted_task=deleted_task.id)

@tool('list_task')
def list_task(task_id: int = None, skip: int = 0, limit: int = 10):
    """List tasks or get a specific task by ID."""
    db = next(get_db())
    task_service = TaskService(db=db)
    if task_id is not None:
        task = task_service.get_task_by_id(task_id=task_id)
        return TaskResponce(**task.__dict__) if task else {"error": "Task not found"}
    
    tasks, total = task_service.list_tasks(skip=skip, limit=limit)
    return TaskList(tasks=[TaskResponce(**t.__dict__) for t in tasks], total=total, skip=skip, limit=limit)

@tool('filter_tasks')
def filter_tasks(status: str = None, priority: str = None, due_before: datetime = None, due_after: datetime = None):
    """Filter tasks by status, priority, and due date criteria."""
    db = next(get_db())
    task_service = TaskService(db=db)
    filters = TaskFilter(
        status=status,
        priority=priority,
        due_before=due_before,
        due_after=due_after
    )
    tasks = task_service.filter_tasks(filters=filters)
    return [TaskResponce(**task.__dict__) for task in tasks]