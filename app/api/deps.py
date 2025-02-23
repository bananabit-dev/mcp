from typing import Generator
from fastapi import Depends, HTTPException, status
from app.core.config import settings
from app.services.model_registry import ModelRegistry
from app.schemas.image import MCPImageModel

def get_model_registry() -> ModelRegistry:
    """Get model registry instance"""
    return ModelRegistry(settings=settings)

def get_model(
    model_id: str,
    registry: ModelRegistry = Depends(get_model_registry)
) -> MCPImageModel:
    """Get model by ID"""
    model = registry.get_model(model_id)
    if not model:
        raise ValueError(f"Model {model_id} not found")
    return model
