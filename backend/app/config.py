from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Main database for business data
    database_url: str = "sqlite:///./smartstock.db"
    
    # Credentials database for user authentication
    credentials_db_url: str = "sqlite:///./credentials.db"
    
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "dev-secret-key-change-in-production-min-32-characters-long"
    algorithm: str = "HS256"

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""

    # Email Settings
    # Email Settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@smartstock360.com"

    resend_api_key: str | None = None
    gemini_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    return Settings()