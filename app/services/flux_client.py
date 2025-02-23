import httpx
from typing import List, Optional
from PIL import Image
import io
import base64
from app.core.config import settings

class FluxClient:
    def __init__(self):
        self.api_url = "https://api.aimlapi.com"
        self.headers = {
            "Authorization": f"Bearer {settings.AIMLAPI_KEY}",
            "Content-Type": "application/json"
        }
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        scheduler: str = "euler",
        style_preset: Optional[str] = None,
        num_images: int = 1,
        seed: Optional[int] = None,
    ) -> List[Image.Image]:
        """Generate images using AIMLAPI"""
        # Convert dimensions to AIMLAPI format
        size = f"{width}x{height}"
        
        # Prepare the request payload
        payload = {
            "prompt": prompt,
            "n": num_images,
            "model": "flux-pro/v1.1",
            "size": size,
            "quality": "hd"  # Use HD quality for better results
        }
        
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        if seed is not None:
            payload["seed"] = seed
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/images/generations",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Image generation failed: {response.text}")
            
            # Parse response and download images
            result = response.json()
            images = []
            
            # Handle both possible response formats
            image_list = result.get("images", [])
            
            for image_data in image_list:
                image_url = image_data.get("url")
                if image_url:
                    # Download the image
                    img_response = await client.get(image_url)
                    if img_response.status_code == 200:
                        img = Image.open(io.BytesIO(img_response.content))
                        images.append(img)
            
            return images
    
    async def enhance_faces(self, image: Image.Image) -> Image.Image:
        """Enhance faces in the image using AIMLAPI"""
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Prepare the request payload
        payload = {
            "image": image_base64,
            "model": "face-enhance"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/images/face-enhance",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Face enhancement failed: {response.text}")
            
            # Parse response and return enhanced image
            result = response.json()
            enhanced_url = result.get("url")
            
            if enhanced_url:
                img_response = await client.get(enhanced_url)
                if img_response.status_code == 200:
                    return Image.open(io.BytesIO(img_response.content))
            
            raise Exception("Failed to get enhanced image URL")
    
    async def upscale_image(self, image: Image.Image, factor: float = 2.0) -> Image.Image:
        """Upscale the image using AIMLAPI"""
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Prepare the request payload
        payload = {
            "image": image_base64,
            "scale_factor": factor,
            "model": "upscale"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/images/upscale",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Image upscaling failed: {response.text}")
            
            # Parse response and return upscaled image
            result = response.json()
            upscaled_url = result.get("url")
            
            if upscaled_url:
                img_response = await client.get(upscaled_url)
                if img_response.status_code == 200:
                    return Image.open(io.BytesIO(img_response.content))
            
            raise Exception("Failed to get upscaled image URL")

flux_client = FluxClient()
