# pydantic-settings: HOST_URL, PLAYER_USERNAME, PLAYER_PASSWORD
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host_url: str = "http://localhost:8000"   
    api_key: str = "secret-api-key"           # must match the host's API_KEY exactly

    class Config:
        env_file = ".env"


settings = Settings()
