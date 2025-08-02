import os
from typing import Dict, List, Any, Annotated
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from config import settings
from ai.task_tools import create_task as create_task_service
from ai.task_tools import update_task as update_task_service
from ai.task_tools import delete_task as delete_task_service
from ai.task_tools import list_task as list_task_service
from ai.task_tools import filter_tasks as filter_tasks_service

class AgentState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]
    task_actions: List[str] = []

@tool
def create_task_tool(title: str, description: str = "", priority: str = "medium", due_date: str = None) -> Dict[str, Any]:
    """Create a new task with the given title, description, priority, and optional due date.
    
    Args:
        title: The task title (required)
        description: Task description (optional)
        priority: Task priority (low, medium, high, urgent)
        due_date: Due date in YYYY-MM-DD format (optional)
    """
    try:
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
            except:
                pass
                
        result = create_task_service(
            title=title,
            description=description,
            due_date=due_date_obj,
            priority=priority
        )
        return {"success": True, "message": f"Created task: {title}", "task": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool
def update_task_tool(task_identifier: str, status: str = None, title: str = None, 
                    priority: str = None, due_date: str = None, description: str = None) -> Dict[str, Any]:
    """Update an existing task by ID or title.
    
    Args:
        task_identifier: Task ID (number) or task title (string) to identify the task
        status: New status (pending, in_progress, completed, failed)
        title: New title
        priority: New priority (low, medium, high, urgent)
        due_date: New due date in YYYY-MM-DD format
        description: New description
    """
    try:
        try:
            task_id = int(task_identifier)
        except ValueError:
            task_id = None
            
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
            except:
                pass
                
        result = update_task_service(
            task_id=task_id,
            title=task_identifier if task_id is None else title,
            description=description,
            due_date=due_date_obj,
            priority=priority,
            status=status
        )
        
        if "error" in result:
            return {"success": False, "error": result["error"]}
        else:
            return {"success": True, "message": f"Updated task: {task_identifier}", "task": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool  
def delete_task_tool(task_identifier: str) -> Dict[str, Any]:
    """Delete a task by ID or title.
    
    Args:
        task_identifier: Task ID (number) or task title (string) to identify the task
    """
    try:
        try:
            task_id = int(task_identifier)
            result = delete_task_service(task_id=task_id)
        except ValueError:
            tasks_result = list_task_service(skip=0, limit=100)
            tasks = tasks_result.get('tasks', [])
            
            task_to_delete = None
            for task in tasks:
                if task.title.lower() == task_identifier.lower():
                    task_to_delete = task
                    break
                    
            if task_to_delete:
                result = delete_task_service(task_id=task_to_delete.id)
            else:
                return {"success": False, "error": f"Task '{task_identifier}' not found"}
        
        if "error" in result:
            return {"success": False, "error": result["error"]}
        else:
            return {"success": True, "message": f"Deleted task: {task_identifier}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool
def list_tasks_tool(limit: int = 100) -> Dict[str, Any]:
    """List all tasks.
    
    Args:
        limit: Maximum number of tasks to return (default: 100)
    """
    try:
        result = list_task_service(skip=0, limit=limit)
        tasks = result.get('tasks', [])
        
        if not tasks:
            return {"success": True, "message": "No tasks found", "tasks": [], "count": 0}
            
        task_list = []
        for task in tasks:
            task_info = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status.value if hasattr(task.status, 'value') else task.status,
                "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                "due_date": task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
                "created_at": task.created_at.strftime('%Y-%m-%d') if task.created_at else None
            }
            task_list.append(task_info)
            
        return {
            "success": True, 
            "message": f"Found {len(task_list)} tasks",
            "tasks": task_list,
            "count": len(task_list)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool
def filter_tasks_tool(status: str = None, priority: str = None, due_date: str = None) -> Dict[str, Any]:
    """Filter tasks by status, priority, or due date.
    
    Args:
        status: Filter by status (pending, in_progress, completed, failed)
        priority: Filter by priority (low, medium, high, urgent)
        due_date: Filter by due date in YYYY-MM-DD format
    """
    try:
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
            except:
                pass
                
        result = filter_tasks_service(
            status=status,
            priority=priority,
            due_date=due_date_obj
        )
        
        tasks = result.get('tasks', [])
        task_list = []
        for task in tasks:
            task_info = {
                "id": task.id,
                "title": task.title,
                "status": task.status.value if hasattr(task.status, 'value') else task.status,
                "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                "due_date": task.due_date.strftime('%Y-%m-%d') if task.due_date else None
            }
            task_list.append(task_info)
            
        return {
            "success": True,
            "message": f"Found {len(task_list)} filtered tasks",
            "tasks": task_list,
            "count": len(task_list)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

tools = [create_task_tool, update_task_tool, delete_task_tool, list_tasks_tool, filter_tasks_tool]

def get_llm():
    """Get the configured LLM (Ollama Gemma)"""
    # Use Ollama with Gemma model
    try:
        return ChatOllama(
            model=settings.ollama_model_name,
            base_url=settings.ollama_base_url,
            temperature=0.1,
        )
    except Exception as e:
        print(f"Failed to connect to Ollama: {e}")
        raise Exception("No LLM available - please ensure Ollama is running with gemma3n:e2b model")

SYSTEM_PROMPT = """You are a helpful task management assistant. You can help users manage their tasks through natural language commands.

Available tools:
- create_task_tool: Create new tasks with title, description, priority, and due date
- update_task_tool: Update existing tasks (status, title, priority, due date)
- delete_task_tool: Delete tasks by ID or title
- list_tasks_tool: Show all tasks
- filter_tasks_tool: Filter tasks by criteria

When a user wants to create a task:
1. Identify the task title from their message
2. Use create_task_tool with the appropriate title
3. Include any other details like priority or due date if specified

When a user wants to update a task:
1. Identify the task by ID number or by title
2. Use update_task_tool with task id and the fields to update

When a user wants to delete a task:
1. Identify the task by ID number or by title
2. Use delete_task_tool with the task id

When a user wants to list tasks:
1. Use list_tasks_tool to show all tasks
2. If they want filtered tasks, use filter_tasks_tool with the appropriate criteria

For all commands:
- Respond conversationally and confirm the action you've taken
- Be helpful and clear in your responses
- If the user message is ambiguous, ask for clarification

Examples:
- "Create a task to buy milk" → Use create_task_tool with title="buy milk"
- "Mark task 5 as done" → Use update_task_tool with task_identifier="5", status="completed"
- "Delete the shopping task" → Use delete_task_tool with task_identifier="shopping"
- "Show my tasks" → Use list_tasks_tool
- "Show high priority tasks" → Use filter_tasks_tool with priority="high"

Do not return JSON responses directly to the user. Always format your responses as natural language.
"""

def should_continue(state: AgentState):
    """Determine if the agent should continue or end"""
    messages = state.messages
    last_message = messages[-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return END

def call_model(state: AgentState):
    """Call the LLM with the current state"""
    messages = state.messages
    
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    try:
        llm = get_llm()
        llm_with_tools = llm.bind_tools(tools)
        response = llm_with_tools.invoke(messages)
        
 
        if not response.content or response.content.strip() == '{}':
 
            fallback_message = "I'll help you with your task. Let me process that."
            return {"messages": [AIMessage(content=fallback_message)]}
        
        return {"messages": [response]}
    except Exception as e:
  
        fallback_message = "I'm having trouble processing your request. Could you try rephrasing it?"
        return {"messages": [AIMessage(content=fallback_message)]}

workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
)

workflow.add_edge("tools", "agent")

compiled_graph = workflow.compile()