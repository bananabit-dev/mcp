from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
from app.services.scraper import scrape_service, ScrapingContext
from datetime import datetime

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/scrape")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            context = ScrapingContext(**json.loads(data))
            
            try:
                # Send start message
                await websocket.send_json({
                    "type": "status",
                    "status": "started",
                    "timestamp": str(datetime.utcnow())
                })
                
                # Perform search
                results = await scrape_service.search(context)
                
                # For each result, get detailed content
                detailed_results = []
                for result in results:
                    content = await scrape_service.extract_content(result["url"])
                    sentiment = await scrape_service.analyze_sentiment(content["text"])
                    summary = await scrape_service.summarize(content["text"])
                    
                    detailed_results.append({
                        **result,
                        "content": content,
                        "sentiment": sentiment,
                        "summary": summary
                    })
                
                # Send results
                await websocket.send_json({
                    "type": "result",
                    "status": "completed",
                    "results": detailed_results,
                    "timestamp": str(datetime.utcnow())
                })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                    "timestamp": str(datetime.utcnow())
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast({
            "type": "system",
            "message": "Client disconnected",
            "timestamp": str(datetime.utcnow())
        })
