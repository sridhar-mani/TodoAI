import socketio, asyncio, json, logging
from typing import List, Optional, Dict
from ai.task_graph import compiled_graph
from langchain_core.messages import HumanMessage
from ai.task_tools import list_task
from databases.connection import get_db

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger = True
)

active_conns: Dict[str, dict] = {}
user_threads: Dict[str, str] = {}

@sio.event
async def connect(sid, environ, auth):
    active_conns[sid]={
        "connected_at":asyncio.get_event_loop().time(),
        "user_id":auth.get('user_id') if auth else f"user_{sid[:8]}",
    }
    user_threads[sid] = asyncio.current_task().get_name()
    await sio.emit('system_message',{
        'message': "Connected to Task Management System",
        'type':'welcome'
    },room=sid)

@sio.event
async def disconnect(sid):
    active_conns.pop(sid,None)
    user_threads.pop(sid,None)

@sio.event
async def chat_message(sid, data):
    try:
        user_message = data.get('message','').strip()
        if not user_message:
            await sio.emit('error', {'message': 'Message cannot be empty'}, room=sid)
            return
        await sio.emit('agent_typing', {"typing":True}, room=sid)

        inputs = {
            "messages": [HumanMessage(content=user_message)]
        }

        thread_id = user_threads.get(sid,'thread_{sid}')
        try:
            output = await compiled_graph.invoke(input=inputs, config={'configurable':{'thread_id': thread_id}})
            agent_responce = output['messages'][-1].content
            await sio.emit(
                'chat_response',{
                    'message':agent_responce,
                    'timestamp': asyncio.get_event_loop().time(),
                    'thread_id':thread_id
                },room=sid
            )
            await broadcast_task_update(agent_responce,exclude_sid = sid)

        except Exception as e:
            logging.error(f"Error processing message from {sid}:{str(e)}")
            await sio.emit('error', {'message': 'Error processing your request'}, room=sid)
        await sio.emit('agent_typing', {"typing":False}, room=sid)
    except Exception as e:
        logging.error(f"Error processing message from {sid}: {str(e)}")
        await sio.emit('error', {'message': 'Invalid message format'}, room=sid)
        return
    
@sio.event
async def get_task_list(sid, data):
    try:
        db = get_db()
        tasks = list_task(db=db)
        await sio.emit('task_list_update',{
            'tasks':tasks['tasks'],
            'timestamp':asyncio.get_event_loop().time()
        },room=sid)
    finally:
        db.close()

@sio.event
async def task_action(sid, data):
    try:
        action = data.get('action')
        task_id = data.get('task_id')

        if not action or not task_id:
            await sio.emit('error',{'message':'Invalid action or task ID'}, room=sid)
            return
        if action == "complete":
            command = f"Mark task {task_id} as completed"
        elif action == "delete":
            command = f"Delete task {task_id}"
        elif action == "update":
            updates = data.get('updates',{})
            command = f"Update task {task_id} with {updates}"
        else:
            await sio.emit('error', {'message': 'Unknown action'}, room=sid)
            return
    
        await chat_message(sid, {'message': command})
    except Exception as e:
        await sio.emit('error', {'message': f'Task failed: {str(e)}', "type":"task_action_error"}, room=sid)

@sio.event
async def broadcast_task_update(message: str, exclude_sid: str = None):
    try:
        task_keywords = ['task','updated','created','deleted','completed']
        if any(keyword in message.lower() for keyword in task_keywords):
            broadcast_data = {
                "type":'task_update',
                'message':message,
                  'timestamp': asyncio.get_event_loop().time()
            }
            for sid in active_conns:
                if sid != exclude_sid:
                    await sio.emit('task_broadcast',broadcast_data,room=sid)
        
    except Exception as e:
        logging.error(f"Error broadcasting task update: {str(e)}")

@sio.event
async def join_room(sid,data):
    room = data.get('room','general')
    await sio.enter_room(sid,room=room)
    await sio.emit('room_joined',{'room':room},room=sid)

@sio.event
async def leave_room(sid,data):
    room = data.get('room','general')
    await sio.leave_room(sid,room=room)
    await sio.emit('room_left',{'room':room},room=sid)

@sio.event
async def pong(sid,data):
    await sio.emit('pong',{'timestamp':asyncio.get_event_loop().time()},room=sid)