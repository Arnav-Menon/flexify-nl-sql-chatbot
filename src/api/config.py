from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

load_dotenv()

class Settings(BaseSettings):
    # Data Paths
    MOCK_DIR: str = ""
    DB_PATH: str = ""
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""
    
    # API Security
    CHATBOT_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        # env_file_encoding = 'utf-8'
        # case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings object.
    Using lru_cache to avoid reading .env file on every request.
    """
    return Settings()

# Create a settings instance
settings = get_settings()