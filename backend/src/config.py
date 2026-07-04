from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "DAMA"
    APP_ENV: str = "development"
    APP_PORT: int = 8000


settings = Settings()