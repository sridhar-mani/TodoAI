from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
from ai.task_tools import create_task, update_task, delete_task, list_task, filter_tasks
from ai.memory_system import memory_manager
from config import settings
import json
import re
from pydantic import BaseModel, Field
from typing import Union

class TaskOperation(BaseModel):
    """Individual task operation to perform"""
    operation: str = Field(description="Operation type: 'create', 'update', 'delete', 'list', 'filter'")
    parameters: Dict[str, Any] = Field(description="Parameters for the operation")

class ChatProcessingResult(BaseModel):
    """Complete structured response from the LLM"""
    intent: str = Field(description="Overall intent: 'task_management', 'general', 'help'")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    user_message_analysis: str = Field(description="LLM's analysis of what the user wants")
    operations: List[TaskOperation] = Field(description="List of task operations to perform")
    response_template: str = Field(description="Template for the final response to user")
    requires_task_data: bool = Field(description="Whether operations need to fetch current task data first")

class ChatProcessor:
    
    def __init__(self):
        self.primary_llm = None
        self.fallback_llm = None
        self.structured_primary_llm = None
        self.structured_fallback_llm = None
        self._configure_llms()
    
    def _configure_llms(self):
        """Configure both LLMs with proper structured output"""
    
        if settings.google_api_key and not settings.debug:
            try:
                self.primary_llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-pro",
                    google_api_key=settings.google_api_key,
                    temperature=0, 
                    convert_system_message_to_human=True,
                )
                self.structured_primary_llm = self.primary_llm.with_structured_output(ChatProcessingResult)
     
            except Exception as e:
                raise e
        
        if OPENAI_AVAILABLE:
            try:
                self.fallback_llm = ChatOpenAI(
                    base_url=settings.lmstudio_base_url,
                    api_key="lm-studio",
                    model=settings.deepseek_model_name,
                    temperature=0
                )
                self.structured_fallback_llm = self.fallback_llm
             
            except Exception as e:
                raise e
        else:
            raise e
    
    def _get_system_prompt(self) -> str:
        """Comprehensive system prompt for LLM-driven task management"""
        return """You are an intelligent task management assistant. Your job is to analyze user messages and create structured responses that include both intent analysis and specific operations to perform.

AVAILABLE TASK OPERATIONS:
1. CREATE: Create new tasks
   - Parameters: title (required), description, priority (low/medium/high/urgent), due_date (YYYY-MM-DD)
2. UPDATE: Update existing tasks
   - Parameters: task_id OR title (for finding), status (pending/in_progress/completed/failed), new_title, priority, due_date, description
3. DELETE: Delete tasks
   - Parameters: task_id OR title (for finding)
4. LIST: Show all tasks
   - Parameters: limit (optional, default 100)
5. FILTER: Filter tasks by criteria
   - Parameters: status, priority, due_date

TASK TITLE EXTRACTION RULES:
- "Create a task to [ACTION]" → title = "[ACTION]"
- "Create a task for [PURPOSE]" → title = "[PURPOSE]"  
- "Add task [DESCRIPTION]" → title = "[DESCRIPTION]"
- "New task: [TITLE]" → title = "[TITLE]"

EXAMPLES:
- "Create a task to buy groceries" → title = "buy groceries"
- "Create a task for deleting files" → title = "deleting files"
- "Add task call mom tomorrow" → title = "call mom tomorrow"
- "New task: finish report" → title = "finish report"

RESPONSE STRUCTURE:
You must analyze the user's message and return a structured response with:
- intent: "task_management" for task operations, "general" for conversations, "help" for assistance
- confidence: Your confidence in understanding the request (0.0-1.0)
- user_message_analysis: Your interpretation of what the user wants
- operations: List of specific task operations to perform (can be empty for general chat)
- response_template: Template for the final response (use {result} placeholder for operation results)
- requires_task_data: true if you need current task data before operations

OPERATION EXAMPLES:

CREATE TASK:
User: "Create a task for deleting files"
operations: [{"operation": "create", "parameters": {"title": "deleting files"}}]
response_template: "✓ Created task 'deleting files'"

UPDATE TASK:
User: "Mark task 5 as completed"
operations: [{"operation": "update", "parameters": {"task_id": 5, "status": "completed"}}]
response_template: "✓ Marked task #{task_id} as completed"

DELETE TASK:
User: "Delete the shopping task"
operations: [{"operation": "delete", "parameters": {"title": "shopping"}}]
response_template: "✓ Deleted task 'shopping'"

LIST TASKS:
User: "Show me my tasks"
operations: [{"operation": "list", "parameters": {}}]
response_template: "{result}"

FILTER TASKS:
User: "Show completed tasks"
operations: [{"operation": "filter", "parameters": {"status": "completed"}}]
response_template: "{result}"

GENERAL CONVERSATION:
User: "Hello" or "How are you?"
intent: "general"
operations: []
response_template: "👋 Hello! I'm here to help you manage your tasks. What would you like to do?"

IMPORTANT RULES:
- Always extract clean, concise task titles
- Remove unnecessary words like "create a task to", "add task", etc.
- Focus on the actual task action or purpose
- Use higher confidence for clear requests
- Be intelligent about context and user intent"""

    def _get_json_system_prompt(self) -> str:
        """System prompt for JSON-only models (DeepSeek) - using prompt engineering instead of response_format"""
        return self._get_system_prompt() + """

CRITICAL JSON RESPONSE FORMAT:
You MUST respond with ONLY a valid JSON object in this exact structure:

{
  "intent": "task_management" | "general" | "help",
  "confidence": 0.0-1.0,
  "user_message_analysis": "string describing what user wants",
  "operations": [
    {
      "operation": "create|update|delete|list|filter",
      "parameters": {"key": "value"}
    }
  ],
  "response_template": "string with {result} placeholder if needed",
  "requires_task_data": true | false
}

CRITICAL RULES:
- Return ONLY the JSON object
- NO explanations, markdown, or extra text
- NO code blocks or formatting
- Must be valid JSON that can be parsed
- Follow the exact structure above"""

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON from text response"""
   
        text = re.sub(r'```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```', '', text)
        
        json_match = re.search(r'({[\s\S]*})', text.strip())
        if json_match:
            return json_match.group(1).strip()
        
        text = text.strip()
        if text.startswith('{') and text.endswith('}'):
            return text
            
        return None

    def _process_with_structured_gemini(self, message: str, context: str = "") -> Optional[ChatProcessingResult]:
        """Process with Gemini structured output"""
        try:
            if not self.structured_primary_llm:
                return None
                
            system_prompt = self._get_system_prompt()
            if context:
                system_prompt += f"\n\nCURRENT TASK CONTEXT:\n{context}"
                
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f'Analyze and process: "{message}"')
            ]
            
            response = self.structured_primary_llm.invoke(messages)
            
            if hasattr(response, 'model_dump'):
                result_dict = response.model_dump()
            elif hasattr(response, 'dict'):
                result_dict = response.dict()
            else:
                result_dict = response.__dict__
            
            validated_result = ChatProcessingResult(**result_dict)
    
            
            return validated_result
            
        except Exception as e:

            return None

    def _process_with_json_deepseek(self, message: str, context: str = "") -> Optional[ChatProcessingResult]:
        """Process with DeepSeek using pure prompt engineering (no response_format)"""
        try:
            if not self.structured_fallback_llm:
                return None
                
            system_prompt = self._get_json_system_prompt()
            if context:
                system_prompt += f"\n\nCURRENT TASK CONTEXT:\n{context}"
                
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f'Analyze and process: "{message}"')
            ]
            
            response = self.structured_fallback_llm.invoke(messages)
            response_text = response.content.strip()
            
            json_text = self._extract_json_from_text(response_text)
            if not json_text:
                return None
                
            parsed_dict = json.loads(json_text)
            
            validated_result = ChatProcessingResult(**parsed_dict)

            return validated_result
            
        except json.JSONDecodeError as e:
            return None
        except Exception as e:
            return None

    def _extract_task_title_from_message(self, message: str) -> str:
        """Improved task title extraction using multiple patterns"""
        message = message.strip()
        message_lower = message.lower()
        
        patterns = [
            r'create\s+(?:a\s+)?task\s+to\s+(.+?)(?:\s+(?:today|tomorrow|this week|next week))?$',
            r'create\s+(?:a\s+)?task\s+for\s+(.+?)(?:\s+(?:today|tomorrow|this week|next week))?$',
            r'add\s+(?:a\s+)?task\s+to\s+(.+?)(?:\s+(?:today|tomorrow|this week|next week))?$',
            r'add\s+(?:a\s+)?task\s+for\s+(.+?)(?:\s+(?:today|tomorrow|this week|next week))?$',
            r'add\s+task\s+(.+?)(?:\s+(?:today|tomorrow|this week|next week))?$',
            r'new\s+task:?\s+(.+?)(?:\s+(?:today|tomorrow|this week|next week))?$',
            r'create\s+(.+?)\s+task$',
            r'add\s+(.+?)\s+task$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'^(a|an|the)\s+', '', title)
                return title
        
        cleaned = message_lower
        prefixes_to_remove = [
            'create a task to ', 'create task to ', 'create a task for ', 'create task for ',
            'add a task to ', 'add task to ', 'add a task for ', 'add task for ',
            'add task ', 'new task ', 'create ', 'add '
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break
        
        return cleaned.strip()

    def _create_fallback_result(self, message: str) -> ChatProcessingResult:
        """Create fallback result using improved rule-based logic"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['create', 'add', 'new']):
           
            title = self._extract_task_title_from_message(message)
            
            return ChatProcessingResult(
                intent="task_management",
                confidence=0.8,
                user_message_analysis=f"User wants to create a task: {title}",
                operations=[TaskOperation(operation="create", parameters={"title": title})],
                response_template=f"✓ Created task '{title}'",
                requires_task_data=False
            )
            
        elif any(word in message_lower for word in ['mark', 'complete', 'done', 'finish']):
        
            numbers = re.findall(r'\d+', message)
            if numbers:
                task_id = int(numbers[0])
                return ChatProcessingResult(
                    intent="task_management",
                    confidence=0.8,
                    user_message_analysis=f"User wants to mark task {task_id} as completed",
                    operations=[TaskOperation(operation="update", parameters={"task_id": task_id, "status": "completed"})],
                    response_template=f"✓ Marked task #{task_id} as completed",
                    requires_task_data=False
                )
            else:
                title_search = message_lower.replace("mark", "").replace("complete", "").replace("done", "").replace("finish", "").replace("as", "").replace("task", "").strip()
                return ChatProcessingResult(
                    intent="task_management",
                    confidence=0.7,
                    user_message_analysis=f"User wants to mark task '{title_search}' as completed",
                    operations=[TaskOperation(operation="update", parameters={"title": title_search, "status": "completed"})],
                    response_template=f"✓ Marked task '{title_search}' as completed",
                    requires_task_data=True
                )
            
        elif any(word in message_lower for word in ['show', 'list', 'get']):
            if any(word in message_lower for word in ['completed', 'done']):
                return ChatProcessingResult(
                    intent="task_management",
                    confidence=0.8,
                    user_message_analysis="User wants to see completed tasks",
                    operations=[TaskOperation(operation="filter", parameters={"status": "completed"})],
                    response_template="{result}",
                    requires_task_data=False
                )
            else:
                return ChatProcessingResult(
                    intent="task_management",
                    confidence=0.8,
                    user_message_analysis="User wants to see all tasks",
                    operations=[TaskOperation(operation="list", parameters={})],
                    response_template="{result}",
                    requires_task_data=False
                )
                
        elif any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return ChatProcessingResult(
                intent="general",
                confidence=0.9,
                user_message_analysis="User is greeting",
                operations=[],
                response_template="👋 Hello! I'm here to help you manage your tasks. What would you like to do today?",
                requires_task_data=False
            )
            
        else:
            return ChatProcessingResult(
                intent="general",
                confidence=0.5,
                user_message_analysis="Unclear request",
                operations=[],
                response_template="🤔 I didn't understand that request. I can help you create, list, update, or delete tasks. What would you like to do?",
                requires_task_data=False
            )

    def _get_current_task_context(self) -> str:
        result = list_task(skip=0, limit=20)
        tasks = result.get("tasks", [])

        if not tasks:
            return "No existing tasks found."

        lines = [f"Current tasks ({len(tasks)} total):"]
        for entry in tasks[:10]:
            if isinstance(entry, dict):
                status = entry["status"]
                priority = entry["priority"]
                due_text = f" (due: {entry['due_date']})" if entry.get("due_date") else ""
                lines.append(f"- #{entry['id']}: {entry['title']} [{status}] [{priority}]{due_text}")
            else:
                status = entry.status.value
                priority = entry.priority.value
                due_text = f" (due: {entry.due_date:%Y-%m-%d})" if entry.due_date else ""
                lines.append(f"- #{entry.id}: {entry.title} [{status}] [{priority}]{due_text}")

        return "\n".join(lines)


    def _execute_operations(self, operations: List[TaskOperation]) -> List[Dict[str, Any]]:
        """Execute all operations and return results"""
        results = []
        
        for op in operations:
            try:
                operation = op.operation
                params = op.parameters
                
                if operation == "create":
                    due_date = None
                    if params.get('due_date'):
                        try:
                            due_date = datetime.strptime(params['due_date'], '%Y-%m-%d')
                        except:
                            pass
                    
                    result = create_task(
                        title=params.get('title', 'New Task'),
                        description=params.get('description', ''),
                        due_date=due_date,
                        priority=params.get('priority', 'medium')
                    )
                    results.append({"operation": operation, "success": True, "result": result, "message": f"Created task: {params.get('title')}"})
                    
                elif operation == "update":
                    due_date = None
                    if params.get("due_date"):
                        try:
                            due_date = datetime.strptime(params["due_date"], "%Y-%m-%d")
                        except:
                            pass

                    search_title = (
                        params.get("title")
                        or params.get("titl")
                        or params.get("tite")
                        or params.get("tile")
                    )
                    if search_title:
                        params["title"] = search_title

                    task_to_update = None
                    if params.get("task_id") is not None:
                      
                        task_to_update = {"id": params["task_id"]}
                    else:
                        all_tasks = list_task(skip=0, limit=100).get("tasks", [])
                        for t in all_tasks:
                            t_id    = t["id"]    if isinstance(t, dict) else t.id
                            t_title = (t["title"] if isinstance(t, dict) else t.title).lower()
                            t_due   = (
                                t.get("due_date") 
                                or (t.due_date.strftime("%Y-%m-%d") if hasattr(t, "due_date") and t.due_date else None)
                            )

                            matches_title = params.get("title") and (t_title == params["title"].lower())
                            matches_date  = params.get("due_date") and (t_due == params["due_date"])
                            
                       
                            if matches_title and (not params.get("due_date") or matches_date):
                                task_to_update = t
                                break

                    if not task_to_update:
                        results.append({
                            "operation": operation,
                            "success": False,
                            "error": "Task ID or matching title (and due date) must be provided"
                        })
                        continue

                    real_id = task_to_update["id"] if isinstance(task_to_update, dict) else task_to_update.id
                    result = update_task(
                        task_id=real_id,
                        title=params.get("new_title") or None,  
                        description=params.get("description"),
                        due_date=due_date,
                        priority=params.get("priority"),
                        status=params.get("status"),
                    )

                    if isinstance(result, dict) and result.get("error"):
                        results.append({"operation": operation, "success": False, "error": result["error"]})
                    else:
                        display_id_or_title = f"#{real_id}" if params.get("task_id") else f"'{params['title']}'"
                        results.append({
                            "operation": operation,
                            "success": True,
                            "message": f"Updated task {display_id_or_title}"
                        })

                elif operation == "delete":
                    if params.get('task_id'):
                        result = delete_task(task_id=params['task_id'])
                        identifier = f"#{params['task_id']}"
                    elif params.get('title'):
                     
                        all_tasks = list_task(skip=0, limit=100)
                        tasks = all_tasks.get('tasks', [])
                        
                        task_to_delete = None
                        for task in tasks:
                            t_title = task["title"] if isinstance(task, dict) else task.title
                            if t_title.lower() == params["title"].lower() or t_title.lower() == params["titl"].lower() or t_title.lower() == params["tite"].lower() or t_title.lower() == params["tile"].lower(): 
                                task_to_delete = task
                                break

                        
                        if not task_to_delete:
                            results.append({
                                "operation": operation,
                                "success": False,
                                "error": f"Task '{params['title']}' not found"
                            })
                            continue
                        task_id = task_to_delete["id"] if isinstance(task_to_delete, dict) else task_to_delete.id
                        delete_res = delete_task(task_id=task_id)

                        if delete_res.get("error"):
                            results.append({"operation": operation, "success": False, "error": delete_res["error"]})
                        else:
                            results.append({
                                "operation": operation,
                                "success": True,
                                "message": f"Deleted task '{params['title']}'"
                            })
                    else:
                        results.append({"operation": operation, "success": False, "error": "No task identifier provided"})
                        continue
                    
                    if 'error' in result:
                        results.append({"operation": operation, "success": False, "error": result['error']})
                    else:
                        results.append({"operation": operation, "success": True, "result": result, "message": f"Deleted task {identifier}"})
                    
                elif operation == "list":
                    limit = params.get('limit', 100)
                    result = list_task(skip=0, limit=limit)
                    tasks = result.get('tasks', [])
                    
                    if not tasks:
                        formatted_result = "📋 No tasks found"
                    else:
                        formatted_result = f"📋 You have {len(tasks)} task{'s' if len(tasks) != 1 else ''}:\n\n"
                        for i, task in enumerate(tasks, 1):
                            if isinstance(task, dict):
                                status = task["status"]
                                priority = task["priority"] 
                                title = task["title"]
                                due_date = task.get("due_date")
                                task_id = task["id"]
                            else:
                                status = task.status.value if hasattr(task.status, 'value') else task.status
                                priority = task.priority.value if hasattr(task.priority, 'value') else task.priority
                                title = task.title
                                due_date = task.due_date
                                task_id = task.id

                    
                    results.append({"operation": operation, "success": True, "result": tasks, "formatted": formatted_result})
                    
                elif operation == "filter":
                
                    due_date = None
                    if params.get('due_date'):
                        try:
                            due_date = datetime.strptime(params['due_date'], '%Y-%m-%d')
                        except:
                            pass
                    
                    result = filter_tasks(
                        status=params.get('status'),
                        priority=params.get('priority'),
                        due_date=due_date
                    )
                    
                    tasks = result.get('tasks', [])
                    
                    filter_desc = []
                    if params.get('status'):
                        filter_desc.append(f"status: {params['status']}")
                    if params.get('priority'):
                        filter_desc.append(f"priority: {params['priority']}")
                    if params.get('due_date'):
                        filter_desc.append(f"due: {params['due_date']}")
                    
                    filter_text = ", ".join(filter_desc) if filter_desc else "no filters"
                    
                    if not tasks:
                        formatted_result = f"📋 No tasks found with {filter_text}"
                    else:
                        formatted_result = f"📋 Found {len(tasks)} task{'s' if len(tasks) != 1 else ''} with {filter_text}:\n\n"
                        for i, task in enumerate(tasks, 1):
                            status = task.status.value if hasattr(task.status, 'value') else task.status
                            priority = task.priority.value if hasattr(task.priority, 'value') else task.priority
                            status_emoji = "✅" if status == "completed" else "🔄" if status == "in_progress" else "⏳"
                            priority_text = f"[{priority.upper()}]" if priority != "medium" else ""
                            due_text = f" (Due: {task.due_date.strftime('%m/%d')})" if task.due_date else ""
                            formatted_result += f"{status_emoji} {i}. {task.title} {priority_text}{due_text}\n"
                    
                    results.append({"operation": operation, "success": True, "result": tasks, "formatted": formatted_result, "filter": filter_text})
                    
            except Exception as e:
                results.append({"operation": operation, "success": False, "error": str(e)})
        
        return results

    def _format_final_response(self, processing_result: ChatProcessingResult, operation_results: List[Dict[str, Any]]) -> str:
        """Format the final response using the template and results"""
        template = processing_result.response_template
        
        if not operation_results:
            return template
        
        if "{result}" in template:
            formatted_results = []
            for result in operation_results:
                if result.get("success"):
                    if "formatted" in result:
                        formatted_results.append(result["formatted"])
                    elif "message" in result:
                        formatted_results.append(result["message"])
                else:
                    formatted_results.append(f"❌ {result.get('error', 'Operation failed')}")
            
            combined_result = "\n\n".join(formatted_results) if formatted_results else "Operation completed"
            return template.replace("{result}", combined_result)
        
        additional_info = []
        for result in operation_results:
            if result.get("success") and "formatted" in result:
                additional_info.append(result["formatted"])
            elif not result.get("success"):
                additional_info.append(f"❌ {result.get('error', 'Operation failed')}")
        
        if additional_info:
            return template + "\n\n" + "\n\n".join(additional_info)
        
        return template

    def process_chat(self, message: str, user_id: str) -> Tuple[str, List[str]]:
        """Main chat processing function using LLM-driven structured approach"""
    
        try:
            context = ""
            if any(word in message.lower() for word in ['update', 'delete', 'mark', 'remove', 'modify']):
                context = self._get_current_task_context()
           
            processing_result = None
            llm_used = "none"

            if self.structured_primary_llm:
                processing_result = self._process_with_structured_gemini(message, context)
                if processing_result:
                    llm_used = "gemini_structured"
            
            if not processing_result and self.structured_fallback_llm:
                processing_result = self._process_with_json_deepseek(message, context)
                if processing_result:
                    llm_used = "deepseek_json"
            
            
            operation_results = []
            task_actions = []
            
            if processing_result.operations:
                operation_results = self._execute_operations(processing_result.operations)
                
                for result in operation_results:
                    if result.get("success") and result.get("message"):
                        task_actions.append(result["message"])
            
            final_response = self._format_final_response(processing_result, operation_results)
     
            memory_manager.add_user_conversation(user_id, message, final_response, task_actions)
            
            return final_response, task_actions
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            return " I'm having trouble processing that request. Please try rephrasing.", []