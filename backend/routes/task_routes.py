from fastapi import Depends, HTTPException, status, Query, APIRouter
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from databases.connection import get_db
from services.task_service import TaskService
from schema.task_schema import TaskCreate, TaskUpdate, TaskResponce, TaskFilter, TaskPriority,TaskList, TaskSearch, StandardResponce
from models.task_model import TaskStatus

task_router = APIRouter(prefix='/api/tasks',tags=['tasks'])

def get_task_services(df:Session = Depends(get_db)):
    return TaskService(db=df)

@task_router.post('/',response_model=TaskResponce, status_code=status.HTTP_201_CREATED, summary="Create a new task")
def create_task(task: TaskCreate, task_service: TaskService = Depends(get_task_services)):
    try:
        task_service.create_task(task_data=task)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create task:{str(e)}")
    return TaskResponce(**task.dict)

@task_router.get('/update/{task_id}', response_model=TaskResponce, summary="Update an existing task")
def update_task(task_id:int, task: TaskUpdate, task_service: TaskService = Depends(get_task_services)):
    updated_task = task_service.update_task(task_id=task_id, task_data=task)
    if not updated_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponce(**updated_task.dict())

@task_router.get('/get/{task_id}', response_model=TaskResponce, summary="Get a task by ID")
def get_task(task_id: int, task_service: TaskService = Depends(get_task_services)):
    cur_task = task_service.get_task_by_id(task_id=task_id)
    if not cur_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponce(**cur_task.dict())

@task_router.delete('/delete/{task}',response_model=StandardResponce, summary="Delete a task by ID")
def delete_task(task_id:int, task_service: TaskService = Depends(get_task_services)):
    delete_tak = task_service.delete_task(task_id=task_id)
    if not delete_tak:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "Task not found")
    return {
        "msg": "Task deleted successfully",
        "data": delete_tak
    }

@task_router.get('/', response_model=TaskList, summary="List all tasks")
def list_tasks(skip:int ,limit: int, task_service: TaskService = Depends(get_task_services)):
    tasks, total = task_service.list_tasks(skip=skip,limit=limit)
    return TaskList(
        tasks=tasks,
        total=total,
        skip=skip,
        limit=limit
    )

@task_router.get('/filter-by-criteria', response_model=List[TaskResponce], summary="Filter tasks")
def filter_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    due_before: Optional[datetime] = None,
    dur_after: Optional[datetime] = None,
    service: TaskService = Depends(get_task_services)
):
    filters = TaskFilter(
        status=status,
        priority=priority,
        due_before=due_before,
        dur_after=dur_after
    )
    return service.filter_tasks(filters=filters)

@task_router.get('/search/', response_model=TaskSearch,summary="Search tasks by title")
def search_tasks(search_term:str = "", skip: int = 0, limit: int = 0, service: TaskService = Depends(get_task_services)):
    tasks, total_found = service.search_tasks(search_term=search_term,skip=skip,limit=limit)
    return TaskSearch(
        tasks=tasks,
        search_term=search_term,
        total_found=len(total_found)
    )

@task_router.get('/get-overdue-tasks', response_model=List[TaskResponce], summary="Get overdue tasks")
def get_overdue_tasks(service: TaskService = Depends(get_task_services)):
    return service.get_overdue_tasks()