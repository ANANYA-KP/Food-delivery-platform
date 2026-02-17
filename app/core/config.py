from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    APP_NAME: str = "Food Delivery Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./food_delivery.db"
    SECRET_KEY: str = "food-delivery-secret-key-2024-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TAX_PERCENTAGE: float = 5.0
    PLATFORM_FEE_PERCENTAGE: float = 2.0
    MIN_DELIVERY_CHARGE: float = 30.0
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
os.makedirs("uploads", exist_ok=True)
os.makedirs("logs", exist_ok=True)
