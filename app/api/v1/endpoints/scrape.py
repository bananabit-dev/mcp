from fastapi import APIRouter, HTTPException
from app.services.scraper import scrape_service, ScrapingContext
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()

class ExtractRequest(BaseModel):
    url: str

class TextRequest(BaseModel):
    text: str

class SummarizeRequest(BaseModel):
    text: str
    max_length: int = 100

@router.post("/search", response_model=List[Dict[str, Any]])
async def search(context: ScrapingContext) -> List[Dict[str, Any]]:
    """Search using ScrapeGraph"""
    try:
        return await scrape_service.search(context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract", response_model=Dict[str, Any])
async def extract_content(request: ExtractRequest) -> Dict[str, Any]:
    """Extract content from URL using ScrapeGraph"""
    try:
        return await scrape_service.extract_content(request.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-sentiment", response_model=Dict[str, Any])
async def analyze_sentiment(request: TextRequest) -> Dict[str, Any]:
    """Analyze sentiment using ScrapeGraph"""
    try:
        return await scrape_service.analyze_sentiment(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize")
async def summarize(request: SummarizeRequest) -> str:
    """Summarize text using ScrapeGraph"""
    try:
        return await scrape_service.summarize(request.text, request.max_length)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
