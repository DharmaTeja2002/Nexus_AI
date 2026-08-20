from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# This calculates the root directory of your project
# It goes up 3 levels from this file: config.py -> core -> src -> NexusAI
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """
    Central Configuration for NexusAI.
    All environment variables are loaded here.
    """
    # Project Settings
    PROJECT_NAME: str = "NexusAI"
    VERSION: str = "0.1.0"
    
    # Paths - These ensure the code always finds the data folders
    INPUT_DIR: Path = BASE_DIR / "data" / "input"
    OUTPUT_DIR: Path = BASE_DIR / "data" / "output"
    TEMP_DIR: Path = BASE_DIR / "data" / "temp"

    # API Keys & LLM Settings
    LLM_PROVIDER: str = "local" # 'local', 'openai', or 'groq'
    OPENAI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    LOCAL_LLM_URL: str = "http://172.30.64.1:11434/v1" # Windows Host IP for WSL
    LOCAL_LLM_MODEL: str = "qwen2.5:3b" # The specific local model to use
    
    # This tells Pydantic to look for a file named .env in the root folder
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Concurrency Limit: Only process 5 files at a time to save RAM
    MAX_CONCURRENT_FILES: int = 5

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "nexus_db"
    DB_USER: str = "nexus_user"
    DB_PASS: str = "nexus_pass"
    DATABASE_URL: str | None = None
    
# We create one single instance of settings to be used across the whole app
settings = Settings()