from fastapi import Depends
from sqlalchemy.orm import Session
from databases.connection import get_db
from services.task_service import TaskService
from schema.task_schema import TaskResponce, TaskDelete, TaskCreate, TaskFilter, TaskList, TaskStatus, TaskUpdate
from datetime import datetime

def create_task(title:str, description:str = '', due_date:datetime =None, priority: str = None):
    db = next(get_db())
    task_service = TaskService(db=db)
    task = task_service.create_task(
        TaskCreate(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority if priority else "medium"
        )
    )
    return task.__dict__

def update_task(task_id:int = None, title:str = None, description:str = None, due_date: datetime = None, priority: str = None, status: str = None):

    db = next(get_db())
    task_service = TaskService(db=db)
    
    search_title = title
    
    if task_id is None and search_title:
        found = task_service.get_task_by_title(title=search_title)
        task_id = found.id if found else None
        title = None 
    
    if task_id is None:
        return {"error": "Task ID or title must be provided"}
    
    update_data = {}
    if title is not None:
        update_data['title'] = title
    if description is not None:
        update_data['description'] = description
    if due_date is not None:
        update_data['due_date'] = due_date
    if priority is not None:
        update_data['priority'] = priority
    if status is not None:
        update_data['status'] = status
    
    task_update = TaskUpdate(**update_data)
    updated_task = task_service.update_task(task_id=task_id, task_data=task_update)
    return updated_task.__dict__ if updated_task else {"error": "Task not found"}

def delete_task(task_id:int):
    db = next(get_db())
    task_service = TaskService(db=db)
    result = task_service.delete_task(task_id=task_id)
    if result:
        return {"success": True, "message": f"Task {task_id} deleted"}
    else:
        return {"error": "Task not found"}

def list_task(skip: int = 0, limit: int = 10):
    db = next(get_db())
    task_service = TaskService(db=db)
    tasks = task_service.list_tasks(skip=skip, limit=limit)
    return {
    "tasks": [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value if hasattr(task.status, "value") else task.status,
            "priority": task.priority.value if hasattr(task.priority, "value") else task.priority,
            "due_date": task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }
        for task in tasks
    ],
    "total": len(tasks)
}


def filter_tasks(status: str = None, priority: str = None, due_date: datetime = None):
   
    db = next(get_db())
    task_service = TaskService(db=db)
    task_filter = TaskFilter(
        status=status,
        priority=priority,
        due_date=due_date
    )
    tasks = task_service.filter_tasks(filters=task_filter)
    return {
    "tasks": [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value if hasattr(task.status, "value") else task.status,
            "priority": task.priority.value if hasattr(task.priority, "value") else task.priority,
            "due_date": task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }
        for task in tasks
    ],
    "total": len(tasks)
}
