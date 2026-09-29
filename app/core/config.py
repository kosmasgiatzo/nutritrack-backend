from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NutriTrack API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    SECRET_KEY: str = "supersecretjwtkeyfornutritrackapplicationchangethisinproduction"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()