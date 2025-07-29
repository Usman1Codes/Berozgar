"""
config/settings.py

Defines application settings loaded from environment variables with validation.
"""
from pathlib import Path
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    # Environment: development or production
    ENVIRONMENT: str = Field('development', env='ENVIRONMENT')
    # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL: str = Field('INFO', env='LOG_LEVEL')
    # Google API Key for Gemini AI (optional)
    GOOGLE_API_KEY: str = Field('', env='GOOGLE_API_KEY')

    @validator('ENVIRONMENT')
    def validate_env(cls, v):
        if v not in ('development', 'production'):
            raise ValueError(f"Invalid ENVIRONMENT: {v}")
        return v

    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        if v.upper() not in levels:
            raise ValueError(f"Invalid LOG_LEVEL: {v}")
        return v.upper()

    class Config:
        env_file = Path(__file__).resolve().parent.parent / '.env'
        env_file_encoding = 'utf-8'


# Instantiate settings (will validate on import)
settings = Settings()
