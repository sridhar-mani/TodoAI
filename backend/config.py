import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./db.db')
        self.debug: bool = os.getenv('DEBUG', 'False').lower() == 'true'
        self.ollama_base_url: str = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model_name: str = os.getenv('OLLAMA_MODEL_NAME', 'gemma3n:e2b')

settings = Settings()