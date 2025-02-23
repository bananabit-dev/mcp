from typing import Dict, Optional, List
from app.core.config import Settings
from app.schemas.image import MCPImageModel, ModelCapability
import json
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_exponential

class ModelRegistry:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.models: Dict[str, MCPImageModel] = {}
        self._load_default_models()

    def _load_default_models(self):
        """Load default models into registry"""
        default_model = MCPImageModel(
            model_id="sd-v1-5",
            name="Stable Diffusion v1.5",
            version="1.5",
            capabilities=[
                ModelCapability.TEXT_TO_IMAGE,
                ModelCapability.IMAGE_TO_IMAGE
            ],
            context_schema={},
            metadata={
                "provider": "StabilityAI",
                "description": "Stable Diffusion v1.5 text-to-image model"
            }
        )
        self.register_model(default_model)

        # Add Flux Pro model
        flux_pro_model = MCPImageModel(
            model_id="flux-pro-1.1",
            name="Flux Pro",
            version="1.1",
            capabilities=[
                ModelCapability.TEXT_TO_IMAGE,
                ModelCapability.IMAGE_TO_IMAGE,
                ModelCapability.INPAINTING,
                ModelCapability.CONTROLNET,
                ModelCapability.UPSCALING,
                ModelCapability.FACE_ENHANCE,
                ModelCapability.STYLE_TRANSFER
            ],
            context_schema={},
            metadata={
                "provider": "AIMLAPI",
                "description": "Advanced image generation and manipulation model"
            }
        )
        self.register_model(flux_pro_model)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def register_model(self, model: MCPImageModel) -> None:
        """Register a new model with retry logic"""
        if model.model_id in self.models:
            raise HTTPException(
                status_code=400,
                detail=f"Model {model.model_id} already registered"
            )
        self.models[model.model_id] = model

    def get_model(self, model_id: str) -> Optional[MCPImageModel]:
        """Get a model by ID"""
        return self.models.get(model_id)

    def list_models(self) -> List[MCPImageModel]:
        """List all registered models"""
        return list(self.models.values())

    def unregister_model(self, model_id: str) -> None:
        """Unregister a model"""
        if model_id not in self.models:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_id} not found"
            )
        del self.models[model_id]
