"""
KRONOS - Smart Working Config
"""
from pydantic_settings import BaseSettings

class SmartWorkingConfig(BaseSettings):
    service_name: str = "smart-working-service"
    debug: bool = True
    
    # Database (uses shared env vars usually, but can be specific)
    # The BaseSettings will pick up env vars automatically.

    class Config:
        env_file = ".env"

config = SmartWorkingConfig()
