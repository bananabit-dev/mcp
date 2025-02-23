from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from app.core.config import settings
import uuid
from datetime import datetime
from scrapegraph_py import Client

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
        self.client = Client(api_key=api_key)

    async def search(self, context: ScrapingContext) -> List[Dict[str, Any]]:
        """Search using ScrapeGraph"""
        try:
            response = self.client.searchscraper(
                user_prompt=context.query
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
            raise Exception(f"Search failed: {str(e)}")

    async def extract_content(self, url: str) -> Dict[str, Any]:
        """Extract content from URL using ScrapeGraph"""
        try:
            response = self.client.smartscraper(
                website_url=url,
                user_prompt="Extract all relevant content and information from this webpage"
            )
            
            if response.get("status") == "completed":
                result = ScrapingResult(
                    title=url,  # Using URL as title since it's not provided in response
                    url=url,
                    content=str(response.get("result", {})),
                    metadata={
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "scrapegraph",
                        "type": "content_extraction",
                        "request_id": response.get("request_id"),
                        "status": response.get("status"),
                        "user_prompt": response.get("user_prompt")
                    }
                )
                return result.dict()
            else:
                raise Exception(f"Content extraction failed: {response.get('error', 'Unknown error')}")
        except Exception as e:
            raise Exception(f"Content extraction failed: {str(e)}")

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using ScrapeGraph"""
        try:
            response = self.client.analyzesentiment(text=text)
            
            return {
                "sentiment": response.get("sentiment", "neutral"),
                "score": response.get("score", 0.0),
                "confidence": response.get("confidence", 0.0),
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "scrapegraph",
                    **response.get("metadata", {})
                }
            }
        except Exception as e:
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
            raise Exception(f"Summarization failed: {str(e)}")

# Create a single instance to be used across the application
scrape_service = ScrapeGraphService()
