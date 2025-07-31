import socketio, asyncio, json, logging
from typing import List, Optional, Dict
from datetime import datetime
from ai.task_graph import compiled_graph
from langchain_core.messages import HumanMessage
from ai.task_tools import list_task
from databases.connection import get_db
from schema.task_schema import TaskResponce
from ai.memory_system import memory_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

active_conns: Dict[str, dict] = {}
user_threads: Dict[str, str] = {}

@sio.event
async def connect(sid, environ, auth):
    try:
        user_id = auth.get('user_id') if auth else f"user_{sid[:8]}"
        active_conns[sid] = {
            "connected_at": asyncio.get_event_loop().time(),
            "user_id": user_id,
            "status": "ready"
        }
        user_threads[sid] = asyncio.current_task().get_name()
        
        logger.info(f"Client {sid} connected as {user_id}")
        
        await sio.emit('system_message', {
            'message': "Connected to Task Management System",
            'type': 'welcome',
            'status': 'ready'
        }, room=sid)
        
        await get_task_list(sid, {})
        
    except Exception as e:
        logger.error(f"Error during connection for {sid}: {str(e)}")

@sio.event
async def disconnect(sid):
    try:
        user_id = active_conns.get(sid, {}).get('user_id', 'unknown')
        logger.info(f"Client {sid} ({user_id}) disconnected")
        active_conns.pop(sid, None)
        user_threads.pop(sid, None)
    except Exception as e:
        logger.error(f"Error during disconnection for {sid}: {str(e)}")

@sio.event
async def chat_message(sid, data):
    typing_sent = False
    
    try:
        user_message = data.get('message', '').strip()
        if not user_message:
            await sio.emit('error', {
                'message': 'Message cannot be empty',
                'status': 'ready'
            }, room=sid)
            return

        if sid in active_conns:
            active_conns[sid]['status'] = 'processing'

        await sio.emit('agent_typing', {"typing": True}, room=sid)
        typing_sent = True

        user_id = active_conns.get(sid, {}).get('user_id', f"user_{sid[:8]}")
        logger.info(f"Processing message from {user_id}: {user_message[:50]}...")

        from ai.chat_processor import ChatProcessor
        chat_processor = ChatProcessor()

        try:
            response, task_actions = chat_processor.process_chat(user_message, user_id)
            
            await sio.emit('chat_response', {
                'message': response,
                'timestamp': asyncio.get_event_loop().time(),
                'thread_id': user_threads.get(sid, f'thread_{sid}'),
                'intent': 'processed',
                'confidence': 0.9,
                'task_actions': task_actions,
                'status': 'ready'
            }, room=sid)
            
            if sid in active_conns:
                active_conns[sid]['status'] = 'ready'
            
            if task_actions:
                logger.info(f"Broadcasting task updates due to actions: {task_actions}")
                await broadcast_task_update(exclude_sid=sid)
                
        except Exception as e:
            logger.error(f"Error processing message from {sid}: {str(e)}")
            await sio.emit('error', {
                'message': 'Error processing your request. Please try again.',
                'error_details': str(e) if logger.level == logging.DEBUG else None,
                'status': 'ready'
            }, room=sid)
            
            if sid in active_conns:
                active_conns[sid]['status'] = 'ready'
                
    except Exception as e:
        logger.error(f"Critical error in chat_message for {sid}: {str(e)}")
        await sio.emit('error', {
            'message': 'Invalid message format',
            'status': 'ready'
        }, room=sid)
        
        if sid in active_conns:
            active_conns[sid]['status'] = 'ready'
    finally:
        if typing_sent:
            await sio.emit('agent_typing', {"typing": False}, room=sid)

@sio.event
async def get_task_list(sid, data):
    try:
        db = next(get_db())
        try:
            tasks = list_task(skip=0, limit=100)
            def serialize_task(task):
                d = TaskResponce.from_orm(task).dict()
                for k, v in d.items():
                    if hasattr(v, 'value'):
                        d[k] = v.value
                    elif isinstance(v, (datetime,)):
                        d[k] = v.isoformat() if v else None
                return d
            task_dicts = [serialize_task(task) for task in tasks['tasks']]
            await sio.emit('task_list_update', {
                'tasks': task_dicts,
                'total': tasks.get('total', len(tasks['tasks'])),
                'timestamp': asyncio.get_event_loop().time()
            }, room=sid)
            logger.info(f"Sent task list to {sid}: {len(tasks['tasks'])} tasks")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error fetching task list for {sid}: {str(e)}")
        await sio.emit('error', {
            'message': 'Error fetching tasks. Please try again.',
            'status': 'ready'
        }, room=sid)

@sio.event
async def task_action(sid, data):
    try:
        action = data.get('action')
        task_id = data.get('task_id')

        if not action or not task_id:
            await sio.emit('error', {
                'message': 'Invalid action or task ID',
                'status': 'ready'
            }, room=sid)
            return

        if action == "complete":
            command = f"Mark task {task_id} as completed"
        elif action == "delete":
            command = f"Delete task {task_id}"
        elif action == "update":
            updates = data.get('updates', {})
            update_parts = []
            for key, value in updates.items():
                update_parts.append(f"{key} to {value}")
            command = f"Update task {task_id} {', '.join(update_parts)}"
        else:
            await sio.emit('error', {
                'message': f'Unknown action: {action}',
                'status': 'ready'
            }, room=sid)
            return

        logger.info(f"Processing task action from {sid}: {command}")
        
        await chat_message(sid, {'message': command})
        
    except Exception as e:
        logger.error(f"Error in task_action for {sid}: {str(e)}")
        await sio.emit('error', {
            'message': f'Task action failed: {str(e)}',
            'type': "task_action_error",
            'status': 'ready'
        }, room=sid)

async def broadcast_task_update(exclude_sid: str = None):
    try:
        db = next(get_db())
        try:
            tasks = list_task(skip=0, limit=100)
            def serialize_task(task):
                d = TaskResponce.from_orm(task).dict()
                for k, v in d.items():
                    if hasattr(v, 'value'):
                        d[k] = v.value
                    elif isinstance(v, (datetime,)):
                        d[k] = v.isoformat() if v else None
                return d
            task_dicts = [serialize_task(task) for task in tasks['tasks']]
            broadcast_data = {
                "type": 'task_update',
                'tasks': task_dicts,
                'total': tasks.get('total', len(tasks['tasks'])),
                'timestamp': asyncio.get_event_loop().time()
            }
            
            clients_notified = 0
            for sid in list(active_conns.keys()):
                if sid != exclude_sid:
                    try:
                        await sio.emit('task_list_update', broadcast_data, room=sid)
                        clients_notified += 1
                    except Exception as e:
                        logger.error(f"Failed to send task update to {sid}: {str(e)}")
                        
            logger.info(f"Broadcasted task update to {clients_notified} clients")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error broadcasting task update: {str(e)}")

@sio.event
async def join_room(sid, data):

    try:
        room = data.get('room', 'general')
        await sio.enter_room(sid, room=room)
        await sio.emit('room_joined', {'room': room}, room=sid)
        logger.info(f"Client {sid} joined room {room}")
    except Exception as e:
        logger.error(f"Error joining room for {sid}: {str(e)}")

@sio.event
async def leave_room(sid, data):
  
    try:
        room = data.get('room', 'general')
        await sio.leave_room(sid, room=room)
        await sio.emit('room_left', {'room': room}, room=sid)
        logger.info(f"Client {sid} left room {room}")
    except Exception as e:
        logger.error(f"Error leaving room for {sid}: {str(e)}")

@sio.event
async def ping(sid, data):
    
    try:
        await sio.emit('pong', {
            'timestamp': asyncio.get_event_loop().time(),
            'received_at': data.get('timestamp'),
            'status': active_conns.get(sid, {}).get('status', 'unknown')
        }, room=sid)
    except Exception as e:
        logger.error(f"Error handling ping for {sid}: {str(e)}")

@sio.event
async def get_connection_status(sid, data):
    
    try:
        status = active_conns.get(sid, {})
        await sio.emit('connection_status', {
            'status': status.get('status', 'unknown'),
            'connected_at': status.get('connected_at'),
            'user_id': status.get('user_id'),
            'timestamp': asyncio.get_event_loop().time()
        }, room=sid)
    except Exception as e:
        logger.error(f"Error getting connection status for {sid}: {str(e)}")

# Health check endpoint for monitoring
async def get_server_stats():
    
    return {
        'active_connections': len(active_conns),
        'connected_users': list(set(conn.get('user_id') for conn in active_conns.values())),
        'server_time': asyncio.get_event_loop().time()
    }