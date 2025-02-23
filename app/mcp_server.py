from pathlib import Path
from typing import Dict, Any
import sys
import os
import json
import asyncio
import logging
import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from app.core.config import settings
from app.services.scraper import ScrapeGraphService

# Configure logging to write to stderr
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG level for more info
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Force output to stderr
)

logger = logging.getLogger(__name__)

# Print startup debug info
print("DEBUG: Starting MCP server...", file=sys.stderr)
print(f"DEBUG: Python path: {sys.path}", file=sys.stderr)
print(f"DEBUG: Current directory: {os.getcwd()}", file=sys.stderr)
print(f"DEBUG: Environment variables:", file=sys.stderr)
for key, value in os.environ.items():
    if "KEY" in key or "SECRET" in key:
        print(f"DEBUG: {key}=***", file=sys.stderr)
    else:
        print(f"DEBUG: {key}={value}", file=sys.stderr)

# Create an MCP server
try:
    logger.info("Starting MCP server initialization...")
    mcp = FastMCP("bananabit")
    logger.info("MCP server created successfully")
except Exception as e:
    logger.error("Failed to start MCP server: %s", str(e))
    import traceback
    traceback.print_exc(file=sys.stderr)
    raise e

# Add image generation tool
@mcp.tool(description="Generate an image using Flux Pro model")
async def generate_flux_image(
    prompt: str,
    negative_prompt: str = "",
    width: int = 768,
    height: int = 768,
    num_inference_steps: int = 30,
    guidance_scale: float = 7.5,
    scheduler: str = "euler_ancestral",
    style_preset: str = None,
    batch_size: int = 1,
    seed: int = None,
    clip_skip: int = 2,
    style_strength: float = 0.7,
    image_format: str = "png"
):
    """Generate an image using Flux Pro model with the given parameters."""
    try:
        from app.api.v1.endpoints.images import process_image_generation
        from app.schemas.image import ImageGenerationContext, FluxStyle, FluxScheduler
        from datetime import datetime
        import uuid

        # Create context with direct parameters
        context = ImageGenerationContext(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            scheduler=FluxScheduler(scheduler),
            style_preset=FluxStyle(style_preset) if style_preset else None,
            batch_size=batch_size,
            seed=seed,
            clip_skip=clip_skip,
            style_strength=style_strength,
            image_format=image_format
        )
        
        # Generate unique ID
        generation_id = str(uuid.uuid4())
        
        # Start generation process
        await process_image_generation(
            generation_id=generation_id,
            model_id="text2img",
            context=context
        )
        
        return {"generation_id": generation_id, "status": "processing"}
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise e

@mcp.tool(description="Get the status and results of an image generation")
async def get_generation_result(generation_id: str):
    """Get the status and results of a previous image generation."""
    try:
        from app.api.v1.endpoints.images import _GENERATION_RESPONSES
        
        if generation_id not in _GENERATION_RESPONSES:
            return {"status": "not_found", "error": "Generation not found"}
            
        result = _GENERATION_RESPONSES[generation_id]
        
        # Create a response with image URLs if available
        response = {
            "status": result.status,
            "metadata": result.metadata,
            "image_count": len(result.images),
            "image_urls": []
        }
        
        # Extract image URLs from metadata if available
        # Extract URLs from the stored response
        if result.status == "completed":
            response["image_urls"] = []
            for img in result.images:
                if isinstance(img, dict):
                    url = img.get("url")
                    if url:
                        response["image_urls"].append(url)
        
        # Include error information if present
        if result.status == "error":
            response["error"] = result.metadata.get("error")
            
        return response
    except Exception as e:
        logger.error(f"Failed to get generation status: {e}")
        raise e

@mcp.tool(description="Save a base64 encoded image to a file")
async def save_generated_image(image_data: str, save_path: str):
    """Save a base64 encoded image or URL to the specified path."""
    try:
        import base64
        from pathlib import Path
        import aiohttp
        import asyncio
        
        # Ensure directory exists
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        if image_data.startswith(('http://', 'https://')):
            # Handle URL
            async with aiohttp.ClientSession() as session:
                async with session.get(image_data) as response:
                    if response.status == 200:
                        image_bytes = await response.read()
                        # Save the image
                        with open(save_path, "wb") as f:
                            f.write(image_bytes)
                    else:
                        raise Exception(f"Failed to download image: HTTP {response.status}")
        else:
            # Handle base64 data
            if "base64," in image_data:
                image_data = image_data.split("base64,")[1]
                
            # Decode base64 data
            image_bytes = base64.b64decode(image_data)
            
            # Save the image
            with open(save_path, "wb") as f:
                f.write(image_bytes)
                
        return {"path": str(save_path), "status": "saved"}
    except Exception as e:
        logger.error(f"Failed to save image: {e}")
        raise e

@mcp.tool(description="Extract content from a specific URL")
async def extract_webpage_content(url: str):
    """Extract and structure content from a specific webpage."""
    try:
        from app.services.scraper import scrape_service
        result = await scrape_service.extract_content(url)
        return result
    except Exception as e:
        logger.error(f"Content extraction failed: {e}")
        raise e

@mcp.tool(description="Analyze sentiment of text")
async def analyze_text_sentiment(text: str):
    """Analyze the sentiment of provided text."""
    try:
        from app.services.scraper import scrape_service
        result = await scrape_service.analyze_sentiment(text)
        return result
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise e

@mcp.tool(description="Summarize text content")
async def summarize_text(text: str, max_length: int = 100):
    """Generate a concise summary of provided text."""
    try:
        from app.services.scraper import scrape_service
        result = await scrape_service.summarize(text, max_length)
        return result
    except Exception as e:
        logger.error(f"Text summarization failed: {e}")
        raise e

# Add web scraping tool
@mcp.tool(description="Scrape content from a webpage using ScrapeGraph")
async def scrape_webpage(url: str):
    """Scrape and extract content from a webpage."""
    try:
        scraper = ScrapeGraphService()
        result = await scraper.scrape(url)
        return result
    except Exception as e:
        logger.error(f"Web scraping failed: {e}")
        raise e

def run():
    """Run the Bananabit MCP server."""
    logger.info("Starting Bananabit MCP server...")
    mcp.run()

def inspector():
    """Inspector mode - same as mcp dev"""
    print("Starting Bananabit MCP server inspector")
    
    import importlib.util
    from mcp.cli.cli import dev
    
    # Get the package location
    spec = importlib.util.find_spec("app")
    if spec and spec.origin:
        package_dir = str(Path(spec.origin).parent)
        file_spec = str(Path(package_dir) / "mcp_server.py")
        print(f"Using file spec: {file_spec}")
        return dev(file_spec=file_spec)
    else:
        raise ImportError("Could not find app package")

if __name__ == "__main__":
    mcp.run(transport='stdio')
