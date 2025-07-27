from sqlalchemy import Column, Integer, String , DateTime, Enum , Text
from sqlalchemy.sql import func
from databases.connection import Base
from datetime import datetime
from enum import Enum as pyEnum

class TaskStatus(pyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskPriority(pyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key = True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus),default=TaskStatus.PENDING,nullable=False)
    due_date = Column(DateTime, nullable=True)
    priority = Column(Enum(TaskPriority),default=TaskPriority.MEDIUM, nullable=False)
    created_at = Column(DateTime, server_default=func.now(),nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status}, priority={self.priority})>"