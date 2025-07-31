import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from databases.connection import get_db

class UserMemory:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.memory_file = f"memory_{user_id}.json"
        self.memory_data = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "preferences": {},
            "conversation_history": [],
            "task_patterns": {},
            "last_interaction": None
        }
    
    def _save_memory(self):
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory_data, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def update_preference(self, key: str, value: Any):
 
        self.memory_data["preferences"][key] = value
        self.memory_data["last_interaction"] = datetime.now().isoformat()
        self._save_memory()
    
    def get_preference(self, key: str, default: Any = None) -> Any:

        return self.memory_data["preferences"].get(key, default)
    
    def add_conversation(self, message: str, response: str, task_actions: List[str] = None):
      
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response": response,
            "task_actions": task_actions or []
        }
        self.memory_data["conversation_history"].append(conversation)
        
        if len(self.memory_data["conversation_history"]) > 50:
            self.memory_data["conversation_history"] = self.memory_data["conversation_history"][-50:]
        
        self._save_memory()
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
     
        return self.memory_data["conversation_history"][-limit:]
    
    def update_task_patterns(self, task_type: str, pattern: Dict[str, Any]):

        if task_type not in self.memory_data["task_patterns"]:
            self.memory_data["task_patterns"][task_type] = []
        
        self.memory_data["task_patterns"][task_type].append(pattern)
        
        if len(self.memory_data["task_patterns"][task_type]) > 20:
            self.memory_data["task_patterns"][task_type] = self.memory_data["task_patterns"][task_type][-20:]
        
        self._save_memory()
    
    def get_task_patterns(self, task_type: str) -> List[Dict]:

        return self.memory_data["task_patterns"].get(task_type, [])
    
    def get_memory_summary(self) -> str:
        preferences = self.memory_data["preferences"]
        recent_conversations = self.get_recent_conversations(5)
        task_patterns = self.memory_data["task_patterns"]
        
        summary = f"User Memory Summary for {self.user_id}:\n"
        summary += f"Last interaction: {self.memory_data.get('last_interaction', 'Never')}\n"
        
        if preferences:
            summary += f"Preferences: {json.dumps(preferences, indent=2)}\n"
        
        if recent_conversations:
            summary += f"Recent conversations: {len(recent_conversations)} conversations\n"
        
        if task_patterns:
            summary += f"Task patterns: {len(task_patterns)} types\n"
        
        return summary

class MemoryManager:
    def __init__(self):
        self.memories: Dict[str, UserMemory] = {}
    
    def get_user_memory(self, user_id: str) -> UserMemory:
      
        if user_id not in self.memories:
            self.memories[user_id] = UserMemory(user_id)
        return self.memories[user_id]
    
    def update_user_preference(self, user_id: str, key: str, value: Any):
    
        memory = self.get_user_memory(user_id)
        memory.update_preference(key, value)
    
    def get_user_preference(self, user_id: str, key: str, default: Any = None) -> Any:
   
        memory = self.get_user_memory(user_id)
        return memory.get_preference(key, default)
    
    def add_user_conversation(self, user_id: str, message: str, response: str, task_actions: List[str] = None):
     
        memory = self.get_user_memory(user_id)
        memory.add_conversation(message, response, task_actions)
    
    def get_user_memory_summary(self, user_id: str) -> str:

        memory = self.get_user_memory(user_id)
        return memory.get_memory_summary()
    
    def add_memory(self, user_id: str, note: str):
        memory = self.get_user_memory(user_id)
        memory.add_conversation(
            message=f"Action: {note}",
            response="Recorded",
            task_actions=[note]
        )

memory_manager = MemoryManager() 