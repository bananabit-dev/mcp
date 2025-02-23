from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Flux Pro MCP"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    AIMLAPI_KEY: str
    SCRAPEGRAPH_API_KEY: str
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8000"]
    WS_MESSAGE_QUEUE_SIZE: int = 100
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_TIMEOUT_SECONDS: int = 300

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
