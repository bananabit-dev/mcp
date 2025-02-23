from typing import Optional, Dict, Any, List
import httpx
import asyncio
from PIL import Image
import io
import base64
from app.core.config import settings

class FluxClient:
    def __init__(self):
        self.api_key = settings.AIMLAPI_KEY
        self.base_url = "https://api.aiml.services/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 768,
        height: int = 768,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        control_image: Optional[str] = None,
        control_type: Optional[str] = None,
        control_strength: float = 0.8,
        reference_image: Optional[str] = None,
        reference_strength: float = 0.8,
        style_preset: Optional[str] = None,
        seed: Optional[int] = None,
        scheduler: str = "euler",
        num_images: int = 1
    ) -> List[Image.Image]:
        """Generate images using AIMLAPI's Flux Pro 1.1"""
        
        payload = {
            "model": "flux-pro-1.1",
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "scheduler": scheduler,
            "num_images": num_images
        }
        
        if seed is not None:
            payload["seed"] = seed
            
        if style_preset:
            payload["style_preset"] = style_preset
            
        if control_image and control_type:
            payload["control"] = {
                "image": control_image,
                "type": control_type,
                "strength": control_strength
            }
            
        if reference_image:
            payload["reference"] = {
                "image": reference_image,
                "strength": reference_strength
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/flux/generate",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"AIMLAPI error: {response.text}")
            
            result = response.json()
            images = []
            
            for img_data in result["images"]:
                # Convert base64 to PIL Image
                img_bytes = base64.b64decode(img_data)
                img = Image.open(io.BytesIO(img_bytes))
                images.append(img)
            
            return images
    
    async def enhance_faces(self, image: Image.Image) -> Image.Image:
        """Enhance faces in the image using AIMLAPI"""
        # Convert PIL Image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        payload = {
            "model": "flux-pro-1.1",
            "image": img_str,
            "face_enhance": True,
            "face_enhance_strength": 0.8
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/flux/enhance",
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"AIMLAPI error: {response.text}")
            
            result = response.json()
            img_bytes = base64.b64decode(result["image"])
            return Image.open(io.BytesIO(img_bytes))
    
    async def upscale_image(
        self,
        image: Image.Image,
        scale_factor: float = 2.0
    ) -> Image.Image:
        """Upscale image using AIMLAPI"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        payload = {
            "model": "flux-pro-1.1",
            "image": img_str,
            "scale_factor": scale_factor
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/flux/upscale",
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"AIMLAPI error: {response.text}")
            
            result = response.json()
            img_bytes = base64.b64decode(result["image"])
            return Image.open(io.BytesIO(img_bytes))

flux_client = FluxClient()
