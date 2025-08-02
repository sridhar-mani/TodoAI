import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from config import settings
from routes.task_routes import task_router
from routes.task_socket_chat import sio
from databases.connection import create_all, engine
from models.task_model import Task
from routes.chat_routes import chat_router


def create_app():
    app = FastAPI(
        title="Task Management API",
        description="A task management system with AI agent support",
        version="1.0.0",
        docs_url="/docs",
    )
    
    router = APIRouter()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(router=task_router, prefix='')
    app.include_router(router=chat_router, prefix='')
    
    return app


app = create_app()

try:
    from sqlalchemy import inspect
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    create_all()
    
    inspector = inspect(engine)
    new_tables = inspector.get_table_names()
    
    from sqlalchemy.orm import Session
    from databases.connection import Session as DBSession
    db = DBSession()
    try:
        tasks = db.query(Task).all()
    except Exception as e:
        pass
    finally:
        db.close()
        
except Exception as e:
    import traceback
    traceback.print_exc()

socket_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    uvicorn.run("app:socket_app", host="0.0.0.0", port=8000, reload=True)