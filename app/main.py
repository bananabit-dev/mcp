from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import images, websockets, scrape
from app.core.config import settings
from fastapi.staticfiles import StaticFiles
from typing import Dict, List
import os

def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
    )

    # Set CORS middleware
    if isinstance(settings.BACKEND_CORS_ORIGINS, str):
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Create static directory if it doesn't exist
    os.makedirs("static/images", exist_ok=True)
    
    # Mount static files directory
    application.mount("/static", StaticFiles(directory="static"), name="static")

    # Include routers
    application.include_router(
        images.router,
        prefix="/api/v1",
        tags=["images"]
    )
    
    # Include WebSocket router
    application.include_router(
        websockets.router,
        prefix="/api/v1/ws",
        tags=["websockets"]
    )
    
    # Include scraping router
    application.include_router(
        scrape.router,
        prefix="/api/v1/scrape",
        tags=["scraping"]
    )

    @application.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "services": {
                "images": "up",
                "websockets": "up",
                "scraping": "up"
            }
        }

    @application.get("/mcp/tools")
    async def get_mcp_tools() -> Dict[str, List[Dict]]:
        """Return available MCP tools for Windsurf to discover"""
        return {
            "tools": [
                {
                    "name": "generate",
                    "description": "Generate images using text prompts",
                    "command": "/generate",
                    "args": ["prompt", "negative_prompt", "width", "height"]
                },
                {
                    "name": "img2img",
                    "description": "Modify existing images using text prompts",
                    "command": "/img2img",
                    "args": ["image", "prompt", "strength"]
                },
                {
                    "name": "inpaint",
                    "description": "Edit specific parts of images",
                    "command": "/inpaint",
                    "args": ["image", "mask", "prompt"]
                },
                {
                    "name": "enhance-face",
                    "description": "Improve facial features",
                    "command": "/enhance-face",
                    "args": ["image"]
                },
                {
                    "name": "extract_webpage_content",
                    "description": "Extract content from a specific URL",
                    "command": "/api/v1/scrape/extract",
                    "args": ["url"]
                },
                {
                    "name": "scrape_webpage",
                    "description": "Scrape content from a webpage using ScrapeGraph",
                    "command": "/api/v1/scrape/extract",
                    "args": ["url"]
                },
                {
                    "name": "markdownify",
                    "description": "Convert webpage content to clean markdown format",
                    "command": "/api/v1/scrape/markdownify",
                    "args": ["url", "clean_level"]
                }
            ]
        }

    return application

app = create_application()
