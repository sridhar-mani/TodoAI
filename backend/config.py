from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: Optional[str] = None
    debug: bool = False
    google_api_key: Optional[str] = None

    class Config:
        env_file = '.env'

settings = Settings()