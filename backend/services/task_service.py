from sqlalchemy import  and_, or_
from sqlalchemy.orm import Session
from models.task_model import Task, TaskStatus, TaskPriority
from schema.task_schema import TaskCreate, TaskUpdate, TaskFilter, TaskResponce
from typing import List, Optional
from datetime import datetime

class TaskService:
    def __init__(self, db:Session):
        self.db: Session = db
    
    def create_task(self, task_data: TaskCreate) -> Task:
        db_task = Task(**task_data.dict())
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task
    
    def get_task_by_id(self, task_id:int)-> Optional[Task]:
        return self.db.query(Task).filter(Task.id==task_id).first()
    
    def get_task_by_title(self, title:str)-> Optional[Task]:
        return self.db.query(Task).filter(Task.title==title).first()

    def update_task(self, task_id:int, task_data:TaskUpdate)->Optional[Task]:
        task = self.get_task_by_id(task_id)
        if not task:
            return None
    
        update_data = task_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def delete_task(self, task_id:int)->bool:
        task = self.get_task_by_id(task_id)
        if not task:
            return False
        self.db.delete(task)
        self.db.commit()
        return True
    
    def list_tasks(self, skip:int=0, limit:int = 100)-> List[Task]:
        return self.db.query(Task).offset(skip).limit(limit).all()

    def filter_tasks(self, filters: TaskFilter) -> List[Task]:
        query = self.db.query(Task)

        if filters.status:
            query = query.filter(Task.status == filters.status)
        
        if filters.priority:
            query = query.filter(Task.priority == filters.priority)
        
        if filters.due_before:
            query = query.filter(Task.due_date <= filters.due_before)

        if filters.due_after:
            query = query.filter(Task.due_date >= filters.due_after)

        return query.all()
    
    def mark_task_complete(self, task_id:int) -> Optional[Task]:
        return self.update_task(task_id, TaskUpdate(status= TaskStatus.COMPLETED))

    def get_overdue_tasks(self)-> List[Task]:
        now = datetime.utcnow()
        return self.db.query(Task).filter(
            and_(
                Task.due_date < now,
                Task.status != TaskStatus.COMPLETED
            )
        ).all()