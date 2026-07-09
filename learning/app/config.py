from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Service Configuration
    SERVICE_NAME: str = "learning-hub"
    SERVICE_DOMAIN: str = "learning.example.com"
    APP_PORT: int = 8000

    # Infrastructure Networks
    PROXY_NETWORK: str = "proxy-net"

    # Application Secrets (Turso)
    TURSO_DATABASE_URL: Optional[str] = None
    TURSO_AUTH_TOKEN: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

