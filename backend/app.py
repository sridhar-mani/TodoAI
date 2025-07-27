import socketio, uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from config import settings
from routes.task_routes import task_router
from routes.task_socket_chat import sio

def create_app():
    app = FastAPI()
    router = APIRouter()

    app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    app.include_router(router=task_router)

    app.config = settings
    
    return app


app=create_app()

socket_app = socketio.ASGIApp(sio,app)

uvicorn.run(socket_app, host='0.0.0.0', port=8000)