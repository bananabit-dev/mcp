from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from app.core.config import settings
import uuid
from datetime import datetime
from scrapegraph_py import Client
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ScrapingContext(BaseModel):
    """Context for scraping operations"""
    query: str = Field(description="Search query or scraping instruction")
    max_results: Optional[int] = Field(default=10, description="Maximum number of results to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters for the search")

class ScrapingResult(BaseModel):
    """Result from scraping operation"""
    title: str = Field(description="Title of the content")
    url: str = Field(description="URL of the content")
    content: str = Field(description="Extracted content")
    metadata: Dict[str, Any] = Field(description="Additional metadata")

class ScrapeGraphService:
    """Service for scraping operations using ScrapeGraph"""
    def __init__(self, api_key: str = settings.SGAI_API_KEY):
        logger.info("Initializing ScrapeGraphService with API key: %s...", api_key[:8] if api_key else "None")
        try:
            if not api_key:
                raise ValueError("SGAI_API_KEY is not set or is empty")
            logger.info("Creating ScrapeGraph client...")
            self.client = Client(api_key=api_key)
            logger.info("ScrapeGraph client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize ScrapeGraph client: %s", str(e))
            raise ValueError(f"Invalid SGAI_API_KEY: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search(self, context: ScrapingContext) -> List[Dict[str, Any]]:
        """Search using ScrapeGraph with retry logic"""
        try:
            response = self.client.searchscraper(
                user_prompt=context.query,
                max_results=context.max_results,
                filters=context.filters or {}
            )
            
            results = []
            if response.get("status") == "completed":
                result = ScrapingResult(
                    title=response.get("user_prompt", ""),
                    url="",  # No specific URL for search results
                    content=str(response.get("result", {})),
                    metadata={
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "scrapegraph",
                        "type": "search_result",
                        "request_id": response.get("request_id"),
                        "reference_urls": response.get("reference_urls", [])
                    }
                )
                results.append(result.dict())
            return results
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise Exception(f"Search failed: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def extract_content(self, url: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Extract content from URL using ScrapeGraph with improved parameters"""
        try:
            try:
                # Simplified parameters according to docs
                response = self.client.smartscraper(
                    website_url=url,
                    user_prompt=custom_prompt or "Extract main content, including headings, text, and relevant structured data"
                )
            except Exception as scrape_error:
                logger.warning(f"Primary scraping method failed: {str(scrape_error)}, attempting fallback...")
                return {
                    "title": url,
                    "url": url,
                    "content": "",
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "fallback",
                        "type": "content_extraction",
                        "status": "partial",
                        "error": str(scrape_error)
                    }
                }
            
            if isinstance(response, dict) and response.get("status") == "completed":
                result = ScrapingResult(
                    title=response.get("metadata", {}).get("title", url),
                    url=url,
                    content=str(response.get("result", {})),
                    metadata={
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "scrapegraph",
                        "type": "content_extraction",
                        "request_id": response.get("request_id"),
                        "status": response.get("status"),
                        "metadata": response.get("metadata", {}),
                        "user_prompt": response.get("user_prompt")
                    }
                )
                return result.dict()
            else:
                # Handle case where response might be a Pydantic model
                if hasattr(response, "dict"):
                    content = response.dict()
                else:
                    content = str(response)
                    
                return {
                    "title": url,
                    "url": url,
                    "content": content,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "scrapegraph",
                        "type": "content_extraction",
                        "status": "completed"
                    }
                }
        except Exception as e:
            logger.error(f"Content extraction failed: {str(e)}")
            return {
                "title": url,
                "url": url,
                "content": "",
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "error",
                    "type": "content_extraction",
                    "status": "failed",
                    "error": str(e)
                }
            }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def markdownify(self, url: str, clean_level: str = "medium") -> Dict[str, Any]:
        """Convert webpage content to clean markdown format
        
        Args:
            url: The webpage URL to convert
            clean_level: Level of cleaning to apply ('light', 'medium', 'aggressive')
        """
        try:
            try:
                # Simplified parameters according to docs
                response = self.client.markdownify(
                    website_url=url
                )
            except Exception as markdown_error:
                logger.warning(f"Markdownify failed: {str(markdown_error)}, attempting fallback...")
                try:
                    content_response = await self.extract_content(url)
                    return {
                        "title": content_response.get("title", url),
                        "url": url,
                        "content": content_response.get("content", ""),
                        "metadata": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "fallback",
                            "type": "markdownify",
                            "status": "fallback",
                            "clean_level": clean_level,
                            "error": str(markdown_error)
                        }
                    }
                except:
                    return {
                        "title": url,
                        "url": url,
                        "content": "",
                        "metadata": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "error",
                            "type": "markdownify",
                            "status": "failed",
                            "clean_level": clean_level,
                            "error": str(markdown_error)
                        }
                    }
            
            if isinstance(response, dict) and response.get("status") == "completed":
                result = ScrapingResult(
                    title=response.get("metadata", {}).get("title", url),
                    url=url,
                    content=response.get("markdown", ""),
                    metadata={
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "scrapegraph",
                        "type": "markdownify",
                        "request_id": response.get("request_id"),
                        "status": response.get("status"),
                        "metadata": response.get("metadata", {}),
                        "clean_level": clean_level
                    }
                )
                return result.dict()
            else:
                # Handle case where response might be direct markdown
                content = str(response) if response else ""
                return {
                    "title": url,
                    "url": url,
                    "content": content,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "scrapegraph",
                        "type": "markdownify",
                        "status": "completed",
                        "clean_level": clean_level
                    }
                }
        except Exception as e:
            logger.error(f"Markdownify failed: {str(e)}")
            return {
                "title": url,
                "url": url,
                "content": "",
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "error",
                    "type": "markdownify",
                    "status": "failed",
                    "clean_level": clean_level,
                    "error": str(e)
                }
            }

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using ScrapeGraph"""
        try:
            response = self.client.analyzesentiment(text=text)
            return response
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            raise Exception(f"Sentiment analysis failed: {str(e)}")

    async def summarize(self, text: str, max_length: int = 100) -> str:
        """Summarize text using ScrapeGraph"""
        try:
            response = self.client.summarize(
                text=text,
                max_length=max_length,
                preserve_key_points=True
            )
            
            return response.get("summary", "")
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            raise Exception(f"Summarization failed: {str(e)}")

# Create a single instance to be used across the application
try:
    scrape_service = ScrapeGraphService()
    logger.info("Successfully initialized ScrapeGraphService")
except Exception as e:
    logger.error(f"Failed to initialize ScrapeGraphService: {str(e)}")
    scrape_service = None  # Allow the application to start without scraping capability
