from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import AnyHttpUrl, validator
from dotenv import load_dotenv
import os
import logging
import json
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load MCP config from Windsurf's config location
home = str(Path.home())
MCP_CONFIG_PATH = os.path.join(home, ".codeium/windsurf/mcp_config.json")
logger.info(f"Looking for config at: {MCP_CONFIG_PATH}")
mcp_env_vars = {}

if os.path.exists(MCP_CONFIG_PATH):
    try:
        with open(MCP_CONFIG_PATH, 'r') as f:
            config_data = json.load(f)
            logger.info("Loaded config data structure:")
            logger.info(f"- Has mcpServers: {'mcpServers' in config_data}")
            if "mcpServers" in config_data:
                logger.info(f"- Server names: {list(config_data['mcpServers'].keys())}")
                logger.info(f"- First server has env: {'env' in next(iter(config_data['mcpServers'].values()))}")
            # Extract env variables from the first server config found
            if "mcpServers" in config_data and len(config_data["mcpServers"]) > 0:
                first_server = next(iter(config_data["mcpServers"].values()))
                if "env" in first_server:
                    mcp_env_vars = first_server["env"]
                    logger.info("Environment variables loaded:")
                    for key in mcp_env_vars:
                        if "KEY" in key or "SECRET" in key:
                            logger.info(f"- {key}: {'*' * 10}")
                        else:
                            logger.info(f"- {key}: {mcp_env_vars[key]}")
    except Exception as e:
        logger.error(f"Error loading {MCP_CONFIG_PATH}: {e}")

# Load environment variables from .env file if it exists
if os.path.exists(".env"):
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
else:
    logger.info("No .env file found, using environment variables")

class Settings(BaseSettings):
    PROJECT_NAME: str = mcp_env_vars.get("PROJECT_NAME") or os.getenv("PROJECT_NAME", "Flux Pro MCP")
    SGAI_API_KEY: str = mcp_env_vars.get("SGAI_API_KEY") or os.getenv("SGAI_API_KEY", "")
    AIMLAPI_KEY: str = mcp_env_vars.get("AIMLAPI_KEY") or os.getenv("AIMLAPI_KEY", "")
    HOST: str = mcp_env_vars.get("HOST") or os.getenv("HOST", "0.0.0.0")
    PORT: int = int(mcp_env_vars.get("PORT") or os.getenv("PORT", "8000"))
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = mcp_env_vars.get("BACKEND_CORS_ORIGINS") or os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:8000")
    WS_MESSAGE_QUEUE_SIZE: int = int(mcp_env_vars.get("WS_MESSAGE_QUEUE_SIZE") or os.getenv("WS_MESSAGE_QUEUE_SIZE", "100"))
    MAX_CONCURRENT_REQUESTS: int = int(mcp_env_vars.get("MAX_CONCURRENT_REQUESTS") or os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    REQUEST_TIMEOUT_SECONDS: int = int(mcp_env_vars.get("REQUEST_TIMEOUT_SECONDS") or os.getenv("REQUEST_TIMEOUT_SECONDS", "300"))
    MCP_LOG_FILE: str = mcp_env_vars.get("MCP_LOG_FILE") or os.getenv("MCP_LOG_FILE", "")

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True

    def check_required_settings(self):
        if not self.AIMLAPI_KEY:
            logger.warning("AIMLAPI_KEY is not set")
        if not self.SGAI_API_KEY:
            logger.warning("SGAI_API_KEY is not set")

settings = Settings()
settings.check_required_settings()
