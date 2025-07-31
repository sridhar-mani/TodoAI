import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./db.db')
        self.debug: bool = os.getenv('DEBUG', 'False').lower() == 'true'
        self.google_api_key: Optional[str] = os.getenv('GOOGLE_API_KEY')
        self.lmstudio_base_url: str = os.getenv('LMSTUDIO_BASE_URL', 'http://127.0.0.1:11434/v1')
        self.deepseek_model_name: str = os.getenv('DEEPSEEK_MODEL_NAME', 'deepseek-r1-distill-qwen-7b')

settings = Settings()