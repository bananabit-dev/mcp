from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from app.schemas.image import (
    ImageGenerationContext,
    ImageGenerationResponse,
    MCPImageModel,
    ModelCapability,
    FluxScheduler,
    FluxStyle,
    ControlNetType
)
from app.api.deps import get_model_registry, get_model
from app.services.model_registry import ModelRegistry
from app.services.flux_client import FluxClient
from datetime import datetime
import base64
import io
from PIL import Image
import uuid
import json
import asyncio
import httpx

router = APIRouter()

# Update API endpoint URLs
AIMLAPI_BASE_URL = "https://api.aimlapi.com/v1"
GENERATE_IMAGE_URL = f"{AIMLAPI_BASE_URL}/image/generate"
UPSCALE_IMAGE_URL = f"{AIMLAPI_BASE_URL}/image/upscale"
ENHANCE_FACE_URL = f"{AIMLAPI_BASE_URL}/image/enhance-face"
STYLE_TRANSFER_URL = f"{AIMLAPI_BASE_URL}/image/style-transfer"
INPAINTING_URL = f"{AIMLAPI_BASE_URL}/image/inpainting"

_GENERATION_RESPONSES = {}

@router.get("/models", response_model=List[MCPImageModel])
async def list_models(
    registry: ModelRegistry = Depends(get_model_registry)
) -> List[MCPImageModel]:
    """List all available models and their capabilities"""
    return registry.list_models()

@router.get("/models/{model_id}", response_model=MCPImageModel)
async def get_model_info(
    model: MCPImageModel = Depends(get_model)
) -> MCPImageModel:
    """Get detailed information about a specific model"""
    return model

@router.post("/models/{model_id}/generate", response_model=ImageGenerationResponse)
async def generate_image(
    model_id: str,
    context: ImageGenerationContext,
    background_tasks: BackgroundTasks,
    model: MCPImageModel = Depends(get_model)
) -> ImageGenerationResponse:
    """Generate image using FastAPI"""
    
    # Create a unique ID for this generation request
    generation_id = str(uuid.uuid4())
    
    # Validate required capabilities based on context
    required_capabilities = ["text-to-image"]
    
    if context.control_image:
        required_capabilities.append("controlnet")
        if not context.control_type:
            raise HTTPException(
                status_code=400,
                detail="control_type must be specified when using control_image"
            )
    
    if context.face_enhance:
        required_capabilities.append("face-enhance")
    
    if context.reference_image:
        required_capabilities.append("style-transfer")
    
    if context.upscale_factor:
        required_capabilities.append("upscaling")
    
    missing_capabilities = [cap for cap in required_capabilities if cap not in model.capabilities]
    if missing_capabilities:
        raise HTTPException(
            status_code=400,
            detail=f"Model missing required capabilities: {', '.join(missing_capabilities)}"
        )
    
    # Create initial response
    response = ImageGenerationResponse(
        id=generation_id,
        status="processing",
        created_at=datetime.utcnow(),
        images=[],
        metadata={
            "model_id": model_id,
            "prompt": context.prompt,
            "seed": context.seed or "random",
            "style_preset": context.style_preset.value if context.style_preset else None,
            "control_type": context.control_type.value if context.control_type else None,
            "status": "queued"
        }
    )
    
    # Store initial response
    _GENERATION_RESPONSES[generation_id] = response
    
    # Add background task for processing
    background_tasks.add_task(
        process_image_generation,
        generation_id,
        model_id,
        context
    )
    
    return response

@router.get("/models/{model_id}/generations/{generation_id}", response_model=ImageGenerationResponse)
async def get_generation_status(
    model_id: str,
    generation_id: str,
    model: MCPImageModel = Depends(get_model)
) -> ImageGenerationResponse:
    """Get the status of an image generation request"""
    if generation_id not in _GENERATION_RESPONSES:
        raise HTTPException(
            status_code=404,
            detail=f"Generation {generation_id} not found"
        )
    
    return _GENERATION_RESPONSES[generation_id]

async def process_image_generation(
    generation_id: str,
    model_id: str,
    context: ImageGenerationContext
) -> None:
    """Process image generation using FastAPI"""
    try:
        # Initialize FluxClient
        flux_client = FluxClient()
        
        # Generate base images
        generated_images = await flux_client.generate_image(
            prompt=context.prompt,
            negative_prompt=context.negative_prompt,
            width=context.width,
            height=context.height,
            num_inference_steps=context.num_inference_steps,
            guidance_scale=context.guidance_scale,
            scheduler=context.scheduler.value if context.scheduler else "euler",
            style_preset=context.style_preset.value if context.style_preset else None,
            num_images=context.batch_size,
            seed=context.seed
        )
        
        # Post-process images based on context
        processed_images = []
        for img in generated_images:
            # Apply face enhancement if requested
            if context.face_enhance:
                img = await flux_client.enhance_faces(img)
            
            # Apply upscaling if requested
            if context.upscale_factor and context.upscale_factor > 1:
                img = await flux_client.upscale_image(img, context.upscale_factor)
            
            # Convert to base64
            buffered = io.BytesIO()
            img.save(buffered, format=context.image_format.upper())
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            processed_images.append({
                "image": img_str,
                "type": "base64",
                "format": context.image_format
            })
        
        # Update response with processed images
        response = ImageGenerationResponse(
            id=generation_id,
            status="completed",
            created_at=datetime.utcnow(),
            images=processed_images,
            metadata={
                "model_id": model_id,
                "prompt": context.prompt,
                "seed": context.seed or "random",
                "style_preset": context.style_preset.value if context.style_preset else None,
                "status": "completed"
            }
        )
        
        # Store response for later retrieval
        _GENERATION_RESPONSES[generation_id] = response
        
        print(f"Generation {generation_id} completed successfully")
        
    except Exception as e:
        error_str = str(e)
        # Check if this is actually a successful response
        if "Image generation failed:" in error_str and '"images":' in error_str:
            try:
                # Extract the JSON response
                json_str = error_str.split("Image generation failed: ", 1)[1]
                result = json.loads(json_str)
                
                # Process the images from the response
                processed_images = []
                for img_data in result.get("images", []):
                    img_url = img_data.get("url")
                    if img_url:
                        async with httpx.AsyncClient() as client:
                            img_response = await client.get(img_url)
                            if img_response.status_code == 200:
                                img = Image.open(io.BytesIO(img_response.content))
                                
                                # Apply face enhancement if requested
                                if context.face_enhance:
                                    img = await flux_client.enhance_faces(img)
                                
                                # Apply upscaling if requested
                                if context.upscale_factor and context.upscale_factor > 1:
                                    img = await flux_client.upscale_image(img, context.upscale_factor)
                                
                                # Convert to base64
                                buffered = io.BytesIO()
                                img.save(buffered, format=context.image_format.upper())
                                img_str = base64.b64encode(buffered.getvalue()).decode()
                                
                                processed_images.append({
                                    "image": img_str,
                                    "type": "base64",
                                    "format": context.image_format
                                })
                
                # Update response with processed images
                response = ImageGenerationResponse(
                    id=generation_id,
                    status="completed",
                    created_at=datetime.utcnow(),
                    images=processed_images,
                    metadata={
                        "model_id": model_id,
                        "prompt": context.prompt,
                        "seed": result.get("seed", "random"),
                        "style_preset": context.style_preset.value if context.style_preset else None,
                        "status": "completed"
                    }
                )
                
                # Store response for later retrieval
                _GENERATION_RESPONSES[generation_id] = response
                
                print(f"Generation {generation_id} completed successfully")
                return
            except Exception as parse_error:
                error_str = f"Failed to parse successful response: {str(parse_error)}"
        
        # If we get here, it's a real error
        print(f"Error processing generation {generation_id}: {error_str}")
        response = ImageGenerationResponse(
            id=generation_id,
            status="error",
            created_at=datetime.utcnow(),
            images=[],
            metadata={
                "model_id": model_id,
                "prompt": context.prompt,
                "seed": context.seed or "random",
                "style_preset": context.style_preset.value if context.style_preset else None,
                "status": "error",
                "error": error_str
            }
        )
        _GENERATION_RESPONSES[generation_id] = response

async def process_control_image(
    image_data: str,
    control_type: ControlNetType,
    strength: float
) -> Dict[str, Any]:
    """Process image for ControlNet"""
    try:
        # Decode base64 image
        img_data = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_data))
        
        # Prepare control signal based on type
        control_signal = {
            "image": img,
            "type": control_type,
            "strength": strength
        }
        
        return control_signal
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process control image: {str(e)}"
        )

async def process_reference_image(
    image_data: str,
    strength: float
) -> Dict[str, Any]:
    """Process reference image for style transfer"""
    try:
        # Decode base64 image
        img_data = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_data))
        
        # Prepare reference embedding
        reference = {
            "image": img,
            "strength": strength
        }
        
        return reference
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process reference image: {str(e)}"
        )

async def enhance_faces(img_str: str) -> str:
    """Enhance faces in the image using Flux Pro"""
    try:
        # Convert base64 to PIL Image
        img_bytes = base64.b64decode(img_str)
        img = Image.open(io.BytesIO(img_bytes))
        
        # Enhance faces
        enhanced_img = await flux_client.enhance_faces(img)
        
        # Convert back to base64
        buffered = io.BytesIO()
        enhanced_img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Face enhancement failed: {str(e)}"
        )

async def upscale_image(img_str: str, factor: int = 2) -> str:
    """Upscale the image using AIMLAPI"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                UPSCALE_IMAGE_URL,
                json={
                    "image": img_str,
                    "scale_factor": factor
                },
                headers={
                    "Authorization": f"Bearer {settings.api_key}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["image"]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Image upscaling failed: {str(e)}"
            )

async def make_tileable(img_str: str) -> str:
    """Make the image tileable using AIMLAPI"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AIMLAPI_BASE_URL}/image/make-tileable",
                json={"image": img_str},
                headers={
                    "Authorization": f"Bearer {settings.api_key}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["image"]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Making image tileable failed: {str(e)}"
            )

@router.post("/text2img/", response_model=ImageGenerationResponse)
async def text_to_image(
    context: ImageGenerationContext,
    background_tasks: BackgroundTasks
) -> ImageGenerationResponse:
    """Generate an image based on a text prompt"""
    generation_id = str(uuid.uuid4())
    
    try:
        return await process_image_generation(
            generation_id=generation_id,
            model_id="text2img",
            context=context
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Text to image generation failed: {str(e)}"
        )

@router.post("/img2img/", response_model=ImageGenerationResponse)
async def image_to_image(
    context: ImageGenerationContext,
    background_tasks: BackgroundTasks
) -> ImageGenerationResponse:
    """Generate a new image based on the input image and a text prompt"""
    if not context.control_image:
        raise HTTPException(
            status_code=400,
            detail="control_image is required for image-to-image generation"
        )
    
    generation_id = str(uuid.uuid4())
    
    try:
        return await process_image_generation(
            generation_id=generation_id,
            model_id="img2img",
            context=context
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Image to image generation failed: {str(e)}"
        )

@router.post("/inpainting/", response_model=ImageGenerationResponse)
async def inpainting(
    context: ImageGenerationContext,
    background_tasks: BackgroundTasks
) -> ImageGenerationResponse:
    """Perform inpainting on an input image based on a text prompt and a mask image"""
    if not context.control_image:
        raise HTTPException(
            status_code=400,
            detail="control_image is required for inpainting"
        )
    
    if not context.mask_image:
        raise HTTPException(
            status_code=400,
            detail="mask_image is required for inpainting"
        )
    
    generation_id = str(uuid.uuid4())
    
    try:
        # Set control type to mask for inpainting
        context.control_type = ControlNetType.SEGMENTATION
        
        return await process_image_generation(
            generation_id=generation_id,
            model_id="inpainting",
            context=context
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inpainting failed: {str(e)}"
        )

@router.post("/upscale/", response_model=ImageGenerationResponse)
async def upscale(
    context: ImageGenerationContext,
    background_tasks: BackgroundTasks
) -> ImageGenerationResponse:
    """Upscale an input image"""
    if not context.control_image:
        raise HTTPException(
            status_code=400,
            detail="control_image is required for upscaling"
        )
    
    if not context.upscale_factor or context.upscale_factor <= 1:
        raise HTTPException(
            status_code=400,
            detail="upscale_factor must be greater than 1"
        )
    
    generation_id = str(uuid.uuid4())
    
    try:
        return await process_image_generation(
            generation_id=generation_id,
            model_id="upscale",
            context=context
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upscaling failed: {str(e)}"
        )

@router.post("/enhance-face/", response_model=ImageGenerationResponse)
async def enhance_face(
    context: ImageGenerationContext,
    background_tasks: BackgroundTasks
) -> ImageGenerationResponse:
    """Enhance faces in an input image"""
    if not context.control_image:
        raise HTTPException(
            status_code=400,
            detail="control_image is required for face enhancement"
        )
    
    generation_id = str(uuid.uuid4())
    
    try:
        # Set face enhancement flag
        context.face_enhance = True
        
        return await process_image_generation(
            generation_id=generation_id,
            model_id="face-enhance",
            context=context
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Face enhancement failed: {str(e)}"
        )

@router.post("/style-transfer/", response_model=ImageGenerationResponse)
async def style_transfer(
    context: ImageGenerationContext,
    background_tasks: BackgroundTasks
) -> ImageGenerationResponse:
    """Apply style transfer using a reference image"""
    if not context.control_image:
        raise HTTPException(
            status_code=400,
            detail="control_image is required for style transfer"
        )
    
    if not context.reference_image:
        raise HTTPException(
            status_code=400,
            detail="reference_image is required for style transfer"
        )
    
    generation_id = str(uuid.uuid4())
    
    try:
        return await process_image_generation(
            generation_id=generation_id,
            model_id="style-transfer",
            context=context
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Style transfer failed: {str(e)}"
        )
