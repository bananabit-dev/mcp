from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from datetime import datetime

class ModelCapability(str, Enum):
    TEXT_TO_IMAGE = "text-to-image"
    IMAGE_TO_IMAGE = "image-to-image"
    INPAINTING = "inpainting"
    CONTROLNET = "controlnet"
    UPSCALING = "upscaling"
    FACE_ENHANCE = "face-enhance"
    STYLE_TRANSFER = "style-transfer"

class FluxScheduler(str, Enum):
    EULER = "euler"
    EULER_ANCESTRAL = "euler_ancestral"
    HEUN = "heun"
    DPM_2 = "dpm_2"
    DPM_2_ANCESTRAL = "dpm_2_ancestral"
    LMS = "lms"
    DDIM = "ddim"

class FluxStyle(str, Enum):
    ANIME = "anime"
    REALISTIC = "realistic"
    ARTISTIC = "artistic"
    CINEMATIC = "cinematic"
    FANTASY = "fantasy"
    ABSTRACT = "abstract"
    CYBERPUNK = "cyberpunk"
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    CONCEPT_ART = "concept_art"

class ControlNetType(str, Enum):
    CANNY = "canny"
    DEPTH = "depth"
    POSE = "pose"
    SEGMENTATION = "segmentation"
    NORMAL = "normal"
    LINE_ART = "line_art"
    SCRIBBLE = "scribble"
    SOFT_EDGE = "soft_edge"

class ImageGenerationContext(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    # Basic parameters
    prompt: str = Field(..., description="Text description of the desired image")
    negative_prompt: Optional[str] = Field(None, description="Text description of what to avoid")
    width: int = Field(768, ge=384, le=1536, description="Image width")
    height: int = Field(768, ge=384, le=1536, description="Image height")
    num_inference_steps: int = Field(30, ge=1, le=150, description="Number of denoising steps")
    guidance_scale: float = Field(7.5, ge=1.0, le=20.0, description="How closely to follow the prompt")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    batch_size: int = Field(1, ge=1, le=4, description="Number of images to generate")
    
    # Flux Pro specific parameters
    scheduler: FluxScheduler = Field(FluxScheduler.EULER_ANCESTRAL, description="Scheduler type")
    style_preset: Optional[FluxStyle] = Field(None, description="Predefined style to apply")
    clip_skip: int = Field(2, ge=1, le=4, description="Number of CLIP layers to skip")
    style_strength: float = Field(0.7, ge=0.0, le=1.0, description="Strength of style application")
    
    # Advanced features
    control_image: Optional[str] = Field(None, description="Base64 encoded image for ControlNet")
    control_type: Optional[ControlNetType] = Field(None, description="Type of ControlNet to use")
    control_strength: Optional[float] = Field(0.8, ge=0.0, le=2.0, description="Strength of control signal")
    reference_image: Optional[str] = Field(None, description="Base64 encoded reference image for style transfer or img2img")
    reference_strength: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Strength of reference image influence")
    
    # Post-processing
    upscale_factor: Optional[float] = Field(None, ge=1.0, le=4.0, description="Upscaling factor")
    face_enhance: bool = Field(False, description="Enable face enhancement")
    tiling: bool = Field(False, description="Generate tileable images")
    image_format: str = Field("png", description="Output image format")
    quality: int = Field(100, ge=1, le=100, description="Image quality for JPEG")

    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()

class ImageGenerationResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
    images: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class MCPImageModel(BaseModel):
    model_id: str
    name: str
    version: str
    capabilities: List[ModelCapability]
    context_schema: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "flux-pro-1.1",
                "name": "Flux Pro",
                "version": "1.1",
                "capabilities": [
                    "text-to-image",
                    "image-to-image",
                    "controlnet",
                    "face-enhance",
                    "style-transfer"
                ],
                "context_schema": {},
                "metadata": {
                    "provider": "Flux AI",
                    "description": "Flux Pro 1.1 with advanced image generation capabilities"
                }
            }
        }
