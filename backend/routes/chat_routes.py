from fastapi import Depends, HTTPException, status, APIRouter
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from databases.connection import get_db
from services.task_service import TaskService
from schema.task_schema import TaskCreate, TaskUpdate, TaskResponce, TaskFilter, TaskPriority, TaskList, TaskSearch, StandardResponce
from typing import Any
from schema.task_schema import ChatMessageIn
from models.task_model import ChatMessage
from ai.chat_processor import ChatProcessor
from fastapi import Request

chat_router = APIRouter(prefix='/api/chat', tags=['chat'])

DEFAULT_CHAT_ID = "main_chat"

def serialize_msg(msg):
        d = msg.__dict__.copy()
        d.pop('_sa_instance_state', None)
        for k, v in d.items():
            if hasattr(v, 'value'):
                d[k] = v.value
            elif isinstance(v, datetime):
                d[k] = v.isoformat() if v else None
        return d

@chat_router.get("/history", response_model=List[Any])
async def get_all_history(db: Session = Depends(get_db)):
    try:
        msgs = (
            db.query(ChatMessage)
            .filter(ChatMessage.chat_id == DEFAULT_CHAT_ID)
            .order_by(ChatMessage.timestamp.asc())
            .all()
        )
        return [serialize_msg(m) for m in msgs]
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chat history: {str(e)}"
        )

@chat_router.post("/message", response_model=ChatMessageIn, status_code=201)
async def post_message(msg: ChatMessageIn, db: Session = Depends(get_db)):

    
    db_msg = ChatMessage(
        id=msg.id,
        chat_id=DEFAULT_CHAT_ID,  
        role=msg.role,
        parts=[p.dict() for p in msg.parts],           
        timestamp=msg.timestamp,
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg