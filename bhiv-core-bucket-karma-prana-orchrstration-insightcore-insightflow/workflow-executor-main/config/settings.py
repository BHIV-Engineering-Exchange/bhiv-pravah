from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "workflow-executor"
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
