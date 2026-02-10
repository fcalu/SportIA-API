from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: str = "dev"
    OPENAI_API_KEY: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
