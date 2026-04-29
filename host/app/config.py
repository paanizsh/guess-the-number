from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str = "secret-api-key"   # default for local dev; in prod override via environment variable

    class Config:
        env_file = ".env"


settings = Settings()