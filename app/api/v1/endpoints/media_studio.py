"""
Creative Media Studio API - Module 8 (UPDATED WITH MAGIC HOUR API)
File: app/api/v1/endpoints/media_studio.py

REPLACE: Synthesia + Ideogram → Magic Hour API
- Text-to-Video: Magic Hour /v1/text-to-video
- Image-to-Video: Magic Hour /v1/image-to-video  
- Text-to-Animation: Magic Hour /v1/animation
- Image-to-Animation: Magic Hour /v1/animation (with image)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
from fastapi import Query, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import pymysql
import json
import requests
import base64
import os
import uuid
import hashlib
from openai import OpenAI
import hashlib
import secrets
import pymysql.cursors

import jwt
from jwt import PyJWTError
from fastapi.responses import RedirectResponse, HTMLResponse
from urllib.parse import urlencode
import secrets

from app.core.config import settings
from app.core.security import require_admin_or_employee, get_current_user
from app.core.security import get_db_connection
from app.api.v1.endpoints.brand_kit import get_brand_kit_by_client, apply_brand_to_prompt

router = APIRouter()

oauth_states = {}
# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Media storage directory
MEDIA_STORAGE_DIR = os.path.join(settings.UPLOAD_DIR, "media_assets")

# Ensure directory exists
os.makedirs(MEDIA_STORAGE_DIR, exist_ok=True)


# ========== MAGIC HOUR API BASE URL ==========
MAGIC_HOUR_API_BASE = "https://api.magichour.ai"


# ========== MAGIC HOUR FILE UPLOAD ==========
async def upload_file_to_magic_hour(file_path: str, file_type: str = "image") -> str:
    """
    Upload file to Magic Hour and return the asset path
    ✅ FIXED: Correct API payload format with "items" array
    """
    
    try:
        print(f"[MAGIC HOUR] Uploading file: {file_path}")
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File not found: {file_path}"
            )
        
        # Check file size
        file_size = os.path.getsize(file_path)
        print(f"[MAGIC HOUR] File size: {file_size / 1024 / 1024:.2f} MB")
        
        if file_size > 10 * 1024 * 1024:  # 10 MB limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit"
            )
        
        # Step 1: Get upload URL
        upload_url_api = f"{MAGIC_HOUR_API_BASE}/v1/files/upload-urls"
        
        headers = {
            "Authorization": f"Bearer {settings.MAGIC_HOUR_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Determine file extension
        file_ext = file_path.split('.')[-1].lower()
        
        # ✅ CORRECT FORMAT: Magic Hour expects "items" array
        payload = {
            "items": [
                {
                    "extension": file_ext,  # e.g., "png", "jpg"
                    "type": file_type       # e.g., "image"
                }
            ]
        }
        
        print(f"[MAGIC HOUR] Upload URL request payload:")
        print(json.dumps(payload, indent=2))
        
        # Request upload URL with increased timeout
        response = requests.post(
            upload_url_api, 
            headers=headers, 
            json=payload, 
            timeout=60
        )
        
        print(f"[MAGIC HOUR] Upload URL response status: {response.status_code}")
        
        if response.status_code not in [200, 201]:
            print(f"[MAGIC HOUR] Upload URL response: {response.text}")
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("message", "Unknown error")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get upload URL: {error_msg}"
            )
        
        result = response.json()
        print(f"[MAGIC HOUR] Upload URL response: {json.dumps(result, indent=2)}")
        
        # Extract upload info from items array
        if "items" not in result or len(result["items"]) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response from Magic Hour: missing items"
            )
        
        upload_info = result["items"][0]
        upload_url = upload_info.get("upload_url")
        file_path_magic = upload_info.get("file_path")
        
        if not upload_url or not file_path_magic:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response from Magic Hour: missing upload_url or file_path"
            )
        
        print(f"[MAGIC HOUR] Got upload URL: {upload_url[:50]}...")
        print(f"[MAGIC HOUR] Magic Hour path: {file_path_magic}")
        
        # Step 2: Upload file to the signed URL
        print(f"[MAGIC HOUR] Reading file content...")
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        print(f"[MAGIC HOUR] Uploading to signed URL...")
        upload_response = requests.put(
            upload_url,
            data=file_data,
            headers={"Content-Type": f"{file_type}/{file_ext}"},
            timeout=120  # 2 minutes for upload
        )
        
        print(f"[MAGIC HOUR] File upload response status: {upload_response.status_code}")
        
        if upload_response.status_code not in [200, 201, 204]:
            print(f"[MAGIC HOUR] File upload error: {upload_response.text}")
            raise HTTPException(
                status_code=upload_response.status_code,
                detail=f"Failed to upload file to Magic Hour: {upload_response.status_code}"
            )
        
        print(f"[MAGIC HOUR] ✅ File uploaded successfully!")
        print(f"[MAGIC HOUR] Magic Hour file path: {file_path_magic}")
        
        return file_path_magic
        
    except HTTPException:
        raise
    except requests.Timeout:
        print(f"[MAGIC HOUR] Upload timeout error")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="File upload to Magic Hour timed out. Please try again."
        )
    except Exception as e:
        print(f"[MAGIC HOUR] Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to Magic Hour: {str(e)}"
        )

        
def generate_code_verifier():
    """Generate a cryptographically random code verifier"""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

def generate_code_challenge(verifier):
    """Generate code challenge from verifier using SHA-256"""
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')



# ========== UTILITY FUNCTIONS ==========

def download_and_save_file(url: str, asset_type: str, file_extension: str = None) -> Dict[str, str]:
    """
    Download file from URL and save to local storage.
    Returns local file path and URL.
    
    ✅ FIXED: Animations from Magic Hour are MP4, not GIF
    """
    try:
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine file extension
        if not file_extension:
            if asset_type == 'image':
                file_extension = 'png'
            elif asset_type == 'video':
                file_extension = 'mp4'
            elif asset_type == 'animation':
                file_extension = 'mp4'  # ✅ FIXED: Was 'gif', now 'mp4'
            else:
                file_extension = 'bin'
        
        filename = f"{asset_type}_{timestamp}_{unique_id}.{file_extension}"
        
        # Create subdirectory for asset type
        type_dir = os.path.join(MEDIA_STORAGE_DIR, asset_type + "s")
        os.makedirs(type_dir, exist_ok=True)
        
        file_path = os.path.join(type_dir, filename)
        
        # Download from URL
        print(f"[STORAGE] Downloading file from: {url}")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Save to disk
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Generate relative URL for serving
        relative_path = f"/static/uploads/media_assets/{asset_type}s/{filename}"
        
        print(f"[STORAGE] File downloaded and saved: {file_path}")
        print(f"[STORAGE] Accessible at: {relative_path}")
        
        return {
            "file_path": file_path,
            "file_url": relative_path,
            "filename": filename
        }
        
    except Exception as e:
        print(f"[STORAGE] Error downloading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download and save file: {str(e)}"
        )


def save_base64_file(base64_data: str, asset_type: str, file_extension: str = None) -> Dict[str, str]:
    """
    Save base64-encoded file to local storage.
    Returns local file path and URL.
    """
    try:
        # Remove data URL prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # Decode base64
        file_data = base64.b64decode(base64_data)
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not file_extension:
            file_extension = 'png' if asset_type == 'image' else 'bin'
        
        filename = f"{asset_type}_{timestamp}_{unique_id}.{file_extension}"
        
        # Create subdirectory for asset type
        type_dir = os.path.join(MEDIA_STORAGE_DIR, asset_type + "s")
        os.makedirs(type_dir, exist_ok=True)
        
        file_path = os.path.join(type_dir, filename)
        
        # Save to disk
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Generate relative URL for serving
        relative_path = f"/static/uploads/media_assets/{asset_type}s/{filename}"
        
        print(f"[STORAGE] Base64 file saved: {file_path}")
        
        return {
            "file_path": file_path,
            "file_url": relative_path,
            "filename": filename
        }
        
    except Exception as e:
        print(f"[STORAGE] Error saving base64 file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


# ========== PYDANTIC MODELS ==========

class ImageGenerateRequest(BaseModel):
    """Request model for DALL-E image generation"""
    prompt: str = Field(..., description="Image description prompt")
    client_id: int
    size: str = Field("1024x1024", description="Image size: 1024x1024, 1024x1792, 1792x1024")
    quality: str = Field("standard", description="Quality: standard or hd")
    style: str = Field("vivid", description="Style: vivid or natural")
    n: int = Field(1, description="Number of images (1-4)")


class VideoGenerateRequest(BaseModel):
    """Request model for Magic Hour text-to-video generation"""
    script: str = Field(..., description="Video description/prompt")
    client_id: int
    duration: Optional[int] = Field(5, description="Video duration in seconds")
    title: Optional[str] = Field(None, description="Video title")
    resolution: Optional[str] = Field("720p", description="Video resolution: 480p, 720p, 1080p")


class AnimationGenerateRequest(BaseModel):
    """Request model for text-to-animation"""
    prompt: str = Field(..., description="Animation description")
    client_id: int
    style: str = Field("modern", description="Animation style")
    title: str = Field("Animation", description="Animation title")
    duration: Optional[int] = Field(5, description="Animation duration in seconds")


class ImageToVideoRequest(BaseModel):
    """Request model for image-to-video conversion"""
    image_data: str = Field(..., description="Base64-encoded image data")
    client_id: int
    motion_prompt: str = Field(..., description="Description of desired motion")
    duration: int = Field(5, description="Video duration in seconds")


class ImageToAnimationRequest(BaseModel):
    """Request model for image-to-animation"""
    image_data: str = Field(..., description="Base64-encoded image data")
    client_id: int
    animation_effect: str = Field(..., description="Animation effect description")
    animation_type: str = Field("modern", description="Animation style")


class CanvaDesignRequest(BaseModel):
    """Request model for Canva design creation"""
    design_type: str = Field(..., description="Type of design: post, story, presentation")
    content: str = Field(..., description="Content for the design")
    client_id: int


# ========== DALL-E IMAGE GENERATION ==========

async def generate_dalle_images(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid",
    n: int = 1
) -> Dict[str, Any]:
    """Generate images using DALL-E 3"""
    
    try:
        print(f"[DALL-E] Generating {n} images with prompt: {prompt[:50]}...")
        
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1  # DALL-E 3 only supports n=1
        )
        
        images = []
        for image_data in response.data:
            # Download and save the image locally
            saved_file = download_and_save_file(
                url=image_data.url,
                asset_type='image',
                file_extension='png'
            )
            
            images.append({
                "url": saved_file["file_url"],
                "revised_prompt": image_data.revised_prompt if hasattr(image_data, 'revised_prompt') else prompt,
                "file_path": saved_file["file_path"]
            })
        
        return {
            "success": True,
            "images": images,
            "model": "dall-e-3"
        }
        
    except Exception as e:
        print(f"[DALL-E] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DALL-E generation failed: {str(e)}"
        )



# ========== MAGIC HOUR VIDEO GENERATION ==========

async def generate_magic_hour_video(
    prompt: str,
    duration: int = 5,
    resolution: str = "720p",
    title: Optional[str] = None
) -> Dict[str, Any]:
    """Generate video using Magic Hour Text-to-Video API"""
    
    try:
        print(f"[MAGIC HOUR] Generating text-to-video: {prompt[:50]}...")
        
        # Check API key
        if not settings.MAGIC_HOUR_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MAGIC_HOUR_API_KEY is not configured in environment variables"
            )
        
        api_url = f"{MAGIC_HOUR_API_BASE}/v1/text-to-video"
        
        headers = {
            "Authorization": f"Bearer {settings.MAGIC_HOUR_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": title or "Text-to-Video",
            "end_seconds": float(duration),
            "orientation": "landscape",
            "style": {"prompt": prompt},
            "resolution": resolution
        }
        
        print(f"[MAGIC HOUR] Request URL: {api_url}")
        print(f"[MAGIC HOUR] Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        print(f"[MAGIC HOUR] Response Status: {response.status_code}")
        print(f"[MAGIC HOUR] Response: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            video_id = result.get("id")
            
            print(f"[MAGIC HOUR] Video created with ID: {video_id}")
            
            return {
                "success": True,
                "video_id": video_id,
                "status": "queued",
                "message": "Video is being generated. Check status for updates."
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("message") or error_data.get("error") or "Unknown error"
            
            print(f"[MAGIC HOUR] Error: {error_msg}")
            
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Magic Hour API error: {error_msg}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[MAGIC HOUR] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Magic Hour video generation failed: {str(e)}"
        )


# ========== MAGIC HOUR IMAGE-TO-VIDEO ==========

async def generate_magic_hour_image_to_video(
    image_path: str,
    duration: int = 5,
    resolution: str = "720p",
    title: Optional[str] = None
) -> Dict[str, Any]:
    """Generate video from image using Magic Hour Image-to-Video API"""
    
    try:
        print(f"[MAGIC HOUR] Generating image-to-video from: {image_path}")
        
        if not settings.MAGIC_HOUR_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MAGIC_HOUR_API_KEY is not configured"
            )
        
        # ✅ Upload file to Magic Hour first
        magic_hour_path = await upload_file_to_magic_hour(image_path, "image")
        
        api_url = f"{MAGIC_HOUR_API_BASE}/v1/image-to-video"
        
        headers = {
            "Authorization": f"Bearer {settings.MAGIC_HOUR_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": title or "Image-to-Video",
            "end_seconds": float(duration),
            "assets": {
                "image_file_path": magic_hour_path  # ✅ Use Magic Hour path
            },
            "resolution": resolution
        }
        
        print(f"[MAGIC HOUR] Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        print(f"[MAGIC HOUR] Response Status: {response.status_code}")
        print(f"[MAGIC HOUR] Response: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            video_id = result.get("id")
            
            print(f"[MAGIC HOUR] Image-to-Video created with ID: {video_id}")
            
            return {
                "success": True,
                "video_id": video_id,
                "status": "queued"
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("message") or "Unknown error"
            
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Magic Hour image-to-video error: {error_msg}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[MAGIC HOUR] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Magic Hour image-to-video failed: {str(e)}"
        )


# ========== MAGIC HOUR ANIMATION GENERATION ==========

async def generate_magic_hour_animation(
    prompt: str,
    duration: int = 5,
    style: str = "modern",
    image_path: Optional[str] = None,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """Generate animation using Magic Hour Animation API"""
    
    try:
        print(f"[MAGIC HOUR] Generating animation: {prompt[:50]}...")
        
        if not settings.MAGIC_HOUR_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MAGIC_HOUR_API_KEY is not configured"
            )
        
        # Map style to Magic Hour art styles
        art_style_map = {
            "modern": "Painterly Illustration",
            "realistic": "Realistic",
            "3d": "3D Render",
            "anime": "Anime",
            "watercolor": "Watercolor"
        }
        
        art_style = art_style_map.get(style, "Painterly Illustration")
        
        # ✅ Upload image to Magic Hour if provided
        magic_hour_path = None
        if image_path:
            magic_hour_path = await upload_file_to_magic_hour(image_path, "image")
        
        api_url = f"{MAGIC_HOUR_API_BASE}/v1/animation"
        
        headers = {
            "Authorization": f"Bearer {settings.MAGIC_HOUR_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": title or "Animation",
            "fps": 12,
            "end_seconds": duration,
            "height": 960,
            "width": 512,
            "style": {
                "art_style": art_style,
                "camera_effect": "Simple Zoom Out",
                "prompt_type": "custom",
                "prompt": prompt,
                "transition_speed": 5
            },
            "assets": {
                "audio_source": "none"  # ✅ REQUIRED: none, file, or youtube
            }
        }
        
        # Add image if provided (for image-to-animation)
        if magic_hour_path:
            payload["assets"]["image_file_path"] = magic_hour_path
        
        print(f"[MAGIC HOUR] Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        print(f"[MAGIC HOUR] Response Status: {response.status_code}")
        print(f"[MAGIC HOUR] Response: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            video_id = result.get("id")
            
            print(f"[MAGIC HOUR] Animation created with ID: {video_id}")
            
            return {
                "success": True,
                "video_id": video_id,
                "status": "queued"
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("message") or "Unknown error"
            
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Magic Hour animation error: {error_msg}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[MAGIC HOUR] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Magic Hour animation failed: {str(e)}"
        )


# ========== MAGIC HOUR STATUS CHECK ==========

async def check_magic_hour_status(video_id: str) -> Dict[str, Any]:
    """Check Magic Hour video/animation status"""
    
    try:
        api_url = f"{MAGIC_HOUR_API_BASE}/v1/video-projects/{video_id}"
        
        headers = {
            "Authorization": f"Bearer {settings.MAGIC_HOUR_API_KEY}",
            "Accept": "application/json"
        }
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            status_value = result.get("status", "unknown")
            downloads = result.get("downloads", [])
            
            print(f"[MAGIC HOUR] Status for {video_id}: {status_value}")
            
            return {
                "status": status_value,
                "downloads": downloads,
                "error": result.get("error")
            }
        else:
            print(f"[MAGIC HOUR] Status check failed: {response.status_code}")
            return {
                "status": "unknown",
                "downloads": [],
                "error": "Failed to check status"
            }
            
    except Exception as e:
        print(f"[MAGIC HOUR] Status check error: {str(e)}")
        return {
            "status": "unknown",
            "downloads": [],
            "error": str(e)
        }


# ========== API ENDPOINTS ==========

@router.post("/generate/image")
async def generate_image(
    request: ImageGenerateRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Generate image using DALL-E with automatic brand kit application"""
    
    connection = None
    cursor = None
    
    try:
        # Get brand kit and apply to prompt
        brand_kit = get_brand_kit_by_client(request.client_id)
        enhanced_prompt = apply_brand_to_prompt(request.prompt, brand_kit) if brand_kit else request.prompt
        
        print(f"[BRAND KIT] Original prompt: {request.prompt}")
        print(f"[BRAND KIT] Enhanced prompt: {enhanced_prompt}")
        
        result = await generate_dalle_images(
            prompt=enhanced_prompt,
            size=request.size,
            quality=request.quality,
            style=request.style,
            n=request.n
        )
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        saved_assets = []
        
        for idx, image in enumerate(result["images"]):
            cursor.execute("""
                INSERT INTO media_assets (
                    client_id, created_by, asset_type, asset_name,
                    file_url, ai_generated, generation_type, prompt_used
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.client_id,
                current_user['user_id'],
                'image',
                f"DALL-E Image {idx + 1}",
                image["url"],
                True,
                "dall-e-3",
                json.dumps({
                    "original_prompt": request.prompt,
                    "revised_prompt": image.get("revised_prompt", request.prompt),
                    "file_path": image.get("file_path", "")
                })
            ))
            
            saved_assets.append({
                "asset_id": cursor.lastrowid,
                "url": image["url"],
                "revised_prompt": image.get("revised_prompt", request.prompt)
            })
        
        connection.commit()
        
        return {
            "success": True,
            "assets": saved_assets,
            "model": "dall-e-3"
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate image: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.post("/generate/video")
async def generate_video(
    request: VideoGenerateRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Generate video using Magic Hour with automatic brand kit application"""
    
    connection = None
    cursor = None
    
    try:
        # Get brand kit and apply to prompt
        brand_kit = get_brand_kit_by_client(request.client_id)
        
        enhanced_script = request.script
        if brand_kit and brand_kit.get('brand_voice'):
            enhanced_script = f"[Brand Voice: {brand_kit['brand_voice']}]\n\n{request.script}"
        
        print(f"[BRAND KIT] Video generation with brand voice: {brand_kit.get('brand_voice') if brand_kit else 'None'}")
        
        result = await generate_magic_hour_video(
            prompt=enhanced_script,
            duration=request.duration,
            resolution=request.resolution,
            title=request.title
        )
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO media_assets (
                client_id, created_by, asset_type, asset_name,
                file_url, ai_generated, generation_type, prompt_used
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.client_id,
            current_user['user_id'],
            'video',
            request.title or "Magic Hour Video",
            "",  # Empty until video is ready
            True,
            "magic-hour",
            json.dumps({
                "script": request.script,
                "video_id": result["video_id"],
                "status": "processing",
                "brand_applied": brand_kit is not None
            })
        ))
        
        asset_id = cursor.lastrowid
        connection.commit()
        
        return {
            "success": True,
            "asset_id": asset_id,
            "video_id": result["video_id"],
            "status": "processing",
            "message": "Video is being generated. Check status for updates.",
            "brand_applied": brand_kit is not None,
            "brand_voice": brand_kit.get('brand_voice') if brand_kit else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[ERROR] Failed to generate video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate video: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.post("/generate/animation")
async def generate_animation(
    request: AnimationGenerateRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Generate animation using Magic Hour with automatic brand kit application"""
    
    connection = None
    cursor = None
    
    try:
        # Get brand kit and apply to prompt
        brand_kit = get_brand_kit_by_client(request.client_id)
        enhanced_prompt = apply_brand_to_prompt(request.prompt, brand_kit) if brand_kit else request.prompt
        
        print(f"[BRAND KIT] Animation - Original prompt: {request.prompt}")
        print(f"[BRAND KIT] Animation - Enhanced prompt: {enhanced_prompt}")
        
        result = await generate_magic_hour_animation(
            prompt=enhanced_prompt,
            duration=request.duration,
            style=request.style,
            title=request.title
        )
        
        connection = get_db_connection()
        cursor = connection.cursor()
      
        cursor.execute("""
            INSERT INTO media_assets (
                client_id, created_by, asset_type, asset_name,
                file_url, ai_generated, generation_type, prompt_used
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.client_id,
            current_user['user_id'],
            'animation',
            request.title,
            "",  # Empty until animation is ready
            True,
            "magic-hour",
            json.dumps({
                "original_prompt": request.prompt,
                "enhanced_prompt": enhanced_prompt,
                "video_id": result["video_id"],
                "status": "processing",
                "brand_applied": brand_kit is not None,
                "style": request.style
            })
        ))
        
        asset_id = cursor.lastrowid
        connection.commit()
        
        return {
            "success": True,
            "asset_id": asset_id,
            "video_id": result["video_id"],
            "status": "processing",
            "message": "Animation is being generated. Check status for updates."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[ERROR] Failed to generate animation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate animation: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@router.post("/image-to-video")
async def image_to_video(
    request: ImageToVideoRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Convert image to video using Magic Hour
    ✅ OPTIMIZED: Better timeout handling and error messages
    """
    
    connection = None
    cursor = None
    
    try:
        print(f"[IMAGE-TO-VIDEO] Starting conversion...")
        
        # Validate base64 data
        if not request.image_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image data is required"
            )
        
        # Save the uploaded image locally
        print(f"[IMAGE-TO-VIDEO] Saving image locally...")
        saved_image = save_base64_file(
            base64_data=request.image_data,
            asset_type='image',
            file_extension='png'
        )
        
        print(f"[IMAGE-TO-VIDEO] Image saved: {saved_image['file_path']}")
        
        # Generate video with Magic Hour (this includes upload)
        print(f"[IMAGE-TO-VIDEO] Calling Magic Hour API...")
        result = await generate_magic_hour_image_to_video(
            image_path=saved_image["file_path"],
            duration=request.duration,
            title=f"Image-to-Video-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        print(f"[IMAGE-TO-VIDEO] Magic Hour video_id: {result['video_id']}")
        
        # Save to database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO media_assets (
                client_id, created_by, asset_type, asset_name,
                file_url, ai_generated, generation_type, prompt_used
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.client_id,
            current_user['user_id'],
            'video',
            "Image-to-Video",
            "",  # Empty until video is ready
            True,
            "magic-hour",
            json.dumps({
                "motion_prompt": request.motion_prompt,
                "video_id": result["video_id"],
                "status": "processing",
                "source_image": saved_image["file_url"],
                "duration": request.duration
            })
        ))
        
        asset_id = cursor.lastrowid
        connection.commit()
        
        print(f"[IMAGE-TO-VIDEO] Asset created: {asset_id}")
        
        return {
            "success": True,
            "asset_id": asset_id,
            "video_id": result["video_id"],
            "status": "processing",
            "message": "Video generation started. This will take 5-15 minutes."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[IMAGE-TO-VIDEO] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert image to video: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@router.post("/image-to-animation")
async def image_to_animation(
    request: ImageToAnimationRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Convert image to animation using Magic Hour
    ✅ OPTIMIZED: Better timeout handling
    """
    
    connection = None
    cursor = None
    
    try:
        print(f"[IMAGE-TO-ANIMATION] Starting conversion...")
        
        # Save the uploaded image locally
        saved_image = save_base64_file(
            base64_data=request.image_data,
            asset_type='image',
            file_extension='png'
        )
        
        print(f"[IMAGE-TO-ANIMATION] Image saved: {saved_image['file_path']}")
        
        # Generate animation with Magic Hour
        print(f"[IMAGE-TO-ANIMATION] Calling Magic Hour API...")
        result = await generate_magic_hour_animation(
            prompt=request.animation_effect,
            style=request.animation_type,
            image_path=saved_image["file_path"],
            title=f"Image-to-Animation-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO media_assets (
                client_id, created_by, asset_type, asset_name,
                file_url, ai_generated, generation_type, prompt_used
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.client_id,
            current_user['user_id'],
            'animation',
            "Image-to-Animation",
            "",
            True,
            "magic-hour",
            json.dumps({
                "animation_effect": request.animation_effect,
                "video_id": result["video_id"],
                "status": "processing",
                "source_image": saved_image["file_url"]
            })
        ))
        
        asset_id = cursor.lastrowid
        connection.commit()
        
        return {
            "success": True,
            "asset_id": asset_id,
            "video_id": result["video_id"],
            "status": "processing",
            "message": "Animation generation started. This will take 5-15 minutes."
        }
        
    except HTTPException:
        raise
    except requests.Timeout:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Request timed out while uploading image. Please try with a smaller image."
        )
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[IMAGE-TO-ANIMATION] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert image to animation: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/video/status/{video_id}")
async def get_video_status(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Check Magic Hour video/animation generation status and download if ready"""
    
    connection = None
    cursor = None
    
    try:
        print(f"[STATUS CHECK] Checking status for video_id: {video_id}")
        
        status_result = await check_magic_hour_status(video_id)
        
        status_value = status_result["status"]
        downloads = status_result["downloads"]
        
        print(f"[STATUS CHECK] Status: {status_value}, Downloads available: {len(downloads) > 0}")
        
        # If video is complete, download and save locally
        if status_value == "complete" and downloads:
            download_url = downloads[0].get("url")
            
            if download_url:
                print(f"[STATUS CHECK] Download URL found: {download_url}")
                
                # Find the asset in database by video_id
                connection = get_db_connection()
                cursor = connection.cursor(pymysql.cursors.DictCursor)
                
                cursor.execute("""
                    SELECT asset_id, asset_type, asset_name, file_url
                    FROM media_assets 
                    WHERE prompt_used LIKE %s
                    AND (file_url IS NULL OR file_url = '')
                    LIMIT 1
                """, (f'%{video_id}%',))
                
                asset = cursor.fetchone()
                
                if asset:
                    print(f"[STATUS CHECK] Found asset: {asset['asset_id']}")
                    
                    # Download and save the file - will use MP4 extension
                    saved_file = download_and_save_file(
                        url=download_url,
                        asset_type=asset['asset_type'],
                        file_extension='mp4'  # ✅ Force MP4 for animations
                    )
                    
                    # Update database with file info
                    cursor.execute("""
                        UPDATE media_assets 
                        SET file_url = %s, file_path = %s
                        WHERE asset_id = %s
                    """, (saved_file['file_url'], saved_file['file_path'], asset['asset_id']))
                    
                    connection.commit()
                    
                    print(f"[STATUS CHECK] Asset updated: {asset['asset_id']}")
                    
                    return {
                        "status": "complete",
                        "file_url": saved_file['file_url'],
                        "message": "Animation ready for download"
                    }
        
        return {
            "status": status_value,
            "error": status_result.get("error")
        }
        
    except Exception as e:
        print(f"[STATUS CHECK] Error: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/library")
async def get_media_library(
    client_id: Optional[int] = Query(None),
    asset_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get media assets library"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT ma.*, u.name as creator_name
            FROM media_assets ma
            LEFT JOIN users u ON ma.created_by = u.user_id
            WHERE 1=1
        """
        params = []
        
        if client_id:
            query += " AND ma.client_id = %s"
            params.append(client_id)
        
        if asset_type:
            query += " AND ma.asset_type = %s"
            params.append(asset_type)
        
        query += " ORDER BY ma.created_at DESC"
        
        cursor.execute(query, params)
        assets = cursor.fetchall()
        
        return {
            "success": True,
            "assets": assets
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch media library: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== CANVA DESIGN CREATION ==========
async def create_canva_design(
    client_id: int,
    design_type: str,
    title: str,
    content_elements: Optional[Dict] = None
) -> Dict[str, Any]:
    """Create design using Canva API with OAuth token"""
    
    connection = None
    cursor = None
    
    try:
        # Get client's Canva access token from database
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT canva_access_token, canva_token_expires_at
            FROM client_profiles
            WHERE client_id = %s
        """, (client_id,))
        
        client_data = cursor.fetchone()
        
        if not client_data or not client_data.get('canva_access_token'):
            raise HTTPException(
                status_code=400,
                detail="Canva not connected. Please connect your Canva account first."
            )
        
        access_token = client_data['canva_access_token']
        
        print(f"[CANVA] Creating design: {title}")
        
        api_url = "https://api.canva.com/rest/v1/designs"
        
        headers = {
            "Authorization": f"Bearer {access_token}",  # ✅ CORRECT - Using OAuth token
            "Content-Type": "application/json"
        }
        
        # Map design types to Canva asset types
        design_types_map = {
            "InstagramPost": "DAFVtKJq-Yc",
            "InstagramStory": "DAFVtFZq8Ss",
            "Presentation": "DAFVtOqq6Qo",
            "Logo": "DAFVtL8q5qY",
            "Flyer": "DAFVtMpqSIE",
            "Poster": "DAFVtNxqoI0",
            "Banner": "DAFVtPBqEwY",
            "FacebookPost": "DAFVtRJqiAA",
            "TwitterPost": "DAFVtSlqlZY",
            "LinkedInPost": "DAFVtT1qXsU"
        }
        
        asset_id = design_types_map.get(design_type, "DAFVtKJq-Yc")
        
        payload = {
            "asset_id": asset_id,
            "title": title
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            result = response.json()
            design_id = result.get("design", {}).get("id")
            edit_url = result.get("design", {}).get("urls", {}).get("edit_url")
            
            return {
                "success": True,
                "design_id": design_id,
                "edit_url": edit_url
            }
        else:
            error_msg = response.json().get("error", {}).get("message", "Unknown error")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Canva API error: {error_msg}"
            )
            
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Canva API timeout"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CANVA] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Canva design creation failed: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

            
@router.post("/create-design")
async def create_design(
    request: CanvaDesignRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Create design using Canva"""
    
    connection = None
    cursor = None
    
    try:
        result = await create_canva_design(
            client_id=request.client_id,  # ✅ ADD THIS
            design_type=request.design_type,
            title=request.title,
            content_elements=request.content_elements
        )
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO media_assets (
                client_id, created_by, asset_type, asset_name,
                file_url, ai_generated, generation_type,
                metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.client_id,
            current_user['user_id'],
            'presentation',
            request.title,
            result.get("edit_url", ""),
            True,
            "canva",
            json.dumps({"design_id": result["design_id"]})
        ))
        
        asset_id = cursor.lastrowid
        connection.commit()
        
        return {
            "success": True,
            "asset_id": asset_id,
            "design_id": result["design_id"],
            "edit_url": result["edit_url"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create design: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



# ========== CANVA OAUTH FLOW ==========
@router.get("/canva/connect", summary="Initiate Canva OAuth with PKCE")
async def connect_canva(
    client_id: int = Query(...),
    token: Optional[str] = Query(None),
    request: Request = None
):
    """Start Canva OAuth authorization flow with PKCE"""
    
    from urllib.parse import urlencode
    import jwt
    from jwt import PyJWTError
    
    # Get token from parameter or cookie
    access_token = token or request.cookies.get('access_token')
    
    if not access_token:
        return HTMLResponse("""
            <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h2>❌ Authentication Required</h2>
                    <p>Please login to continue</p>
                    <button onclick="window.close()">Close</button>
                </body>
            </html>
        """, status_code=401)
    
    try:
        # Decode and verify JWT token
        payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id = payload.get('user_id')
        role = payload.get('role')
        
        # Verify user has admin or employee role
        if role not in ['admin', 'employee']:
            raise Exception("Insufficient permissions")
        
        # ✅ Generate PKCE parameters
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state and code_verifier temporarily
        oauth_states[state] = {
            'client_id': client_id,
            'user_id': user_id,
            'code_verifier': code_verifier,  # ✅ Store for later use
            'timestamp': datetime.now()
        }
        
        print(f"🔐 Canva OAuth initiated - Client: {client_id}, User: {user_id}")
        print(f"📍 Code Verifier: {code_verifier[:20]}...")
        print(f"📍 Code Challenge: {code_challenge[:20]}...")
        
        # Use the configured redirect URI
        redirect_uri = settings.CANVA_REDIRECT_URI
        
        print(f"📍 Redirect URI: {redirect_uri}")
        
        # ✅ Build authorization URL with PKCE
        auth_params = {
            'response_type': 'code',
            'client_id': settings.CANVA_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'scope': 'design:content:read design:content:write design:meta:read asset:read',
            'state': state,
            'code_challenge': code_challenge,  # ✅ REQUIRED
            'code_challenge_method': 's256'     # ✅ REQUIRED
        }
        
        auth_url = f"https://www.canva.com/api/oauth/authorize?{urlencode(auth_params)}"
        
        print(f"🔄 Full OAuth URL: {auth_url[:150]}...")
        
        return RedirectResponse(url=auth_url)
        
    except PyJWTError as e:
        print(f"❌ JWT verification failed: {str(e)}")
        return HTMLResponse(f"""
            <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h2>❌ Authentication Failed</h2>
                    <p>Invalid or expired token</p>
                    <button onclick="window.close()">Close</button>
                </body>
            </html>
        """, status_code=401)
    except Exception as e:
        print(f"❌ Canva OAuth error: {str(e)}")
        return HTMLResponse(f"""
            <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h2>❌ Authentication Failed</h2>
                    <p>{str(e)}</p>
                    <button onclick="window.close()">Close</button>
                </body>
            </html>
        """, status_code=401)



@router.get("/canva/callback", summary="Handle Canva OAuth callback with PKCE")
async def canva_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    """Handle OAuth callback from Canva and exchange code for tokens"""
    
    if error:
        return HTMLResponse(f"""
            <html>
                <body style="text-align: center; padding: 50px;">
                    <h2>❌ Authorization Failed</h2>
                    <p>{error}</p>
                    <button onclick="window.close()">Close</button>
                </body>
            </html>
        """, status_code=400)
    
    if not code or not state:
        return HTMLResponse("""
            <html>
                <body style="text-align: center; padding: 50px;">
                    <h2>❌ Invalid Request</h2>
                    <p>Missing authorization code or state</p>
                    <button onclick="window.close()">Close</button>
                </body>
            </html>
        """, status_code=400)
    
    if state not in oauth_states:
        return HTMLResponse("""
            <html>
                <body style="text-align: center; padding: 50px;">
                    <h2>❌ Invalid State</h2>
                    <p>Security validation failed</p>
                    <button onclick="window.close()">Close</button>
                </body>
            </html>
        """, status_code=400)
    
    oauth_data = oauth_states[state]
    connection = None
    cursor = None
    
    try:
        # ✅ Exchange code for access token with PKCE
        token_response = requests.post(
            'https://api.canva.com/rest/v1/oauth/token',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data={
                'grant_type': 'authorization_code',
                'code_verifier': oauth_data['code_verifier'],  # ✅ REQUIRED for PKCE
                'code': code,
                'redirect_uri': settings.CANVA_REDIRECT_URI,
                'client_id': settings.CANVA_CLIENT_ID,
                'client_secret': settings.CANVA_CLIENT_SECRET
            },
            timeout=30
        )
        
        print(f"[CANVA] Token exchange status: {token_response.status_code}")
        
        if not token_response.ok:
            error_text = token_response.text
            print(f"[CANVA] Token exchange failed: {error_text}")
            raise Exception(f"Token exchange failed: {error_text}")
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in', 14400)  # 4 hours default
        
        # Calculate expiration
        from datetime import timedelta
        token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        # Store in database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO client_profiles (
                client_id, canva_access_token, canva_refresh_token, 
                canva_token_expires_at, updated_at
            ) VALUES (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                canva_access_token = VALUES(canva_access_token),
                canva_refresh_token = VALUES(canva_refresh_token),
                canva_token_expires_at = VALUES(canva_token_expires_at),
                updated_at = NOW()
        """, (oauth_data['client_id'], access_token, refresh_token, token_expires_at))
        
        connection.commit()
        
        # Clean up state
        del oauth_states[state]
        
        print(f"✅ Canva connected successfully for client {oauth_data['client_id']}")
        
        return HTMLResponse("""
            <html>
                <head>
                    <style>
                        body { font-family: 'Segoe UI', Arial; text-align: center; padding: 50px; background: #f8fafc; }
                        .success-box { background: white; padding: 40px; border-radius: 16px; max-width: 500px; margin: 0 auto; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
                        h2 { color: #10b981; margin-bottom: 1rem; }
                        button { padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; margin-top: 20px; }
                    </style>
                </head>
                <body>
                    <div class="success-box">
                        <h2>✅ Canva Connected!</h2>
                        <p>Your Canva account has been successfully connected.</p>
                        <p>You can now create designs using Canva API.</p>
                        <button onclick="closeWindow()">Close & Continue</button>
                    </div>
                    <script>
                        function closeWindow() {
                            if (window.opener) {
                                window.opener.postMessage({ type: 'canva_connected' }, '*');
                            }
                            window.close();
                        }
                        setTimeout(closeWindow, 3000);
                    </script>
                </body>
            </html>
        """)
        
    except Exception as e:
        print(f"❌ Canva OAuth callback error: {str(e)}")
        return HTMLResponse(f"""
            <html>
                <body style="text-align: center; padding: 50px;">
                    <h2>❌ Connection Failed</h2>
                    <p>{str(e)}</p>
                    <button onclick="window.close()">Close</button>
                </body>
            </html>
        """, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== ASSET MANAGEMENT ENDPOINTS ==========

@router.get("/assets")
async def get_assets(
    client_id: Optional[int] = None,
    asset_type: Optional[str] = None,
    generation_type: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get all media assets with optional filters"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                ma.*,
                u.full_name as creator_name,
                c.full_name as client_name
            FROM media_assets ma
            LEFT JOIN users u ON ma.created_by = u.user_id
            LEFT JOIN users c ON ma.client_id = c.user_id
            WHERE 1=1
        """
        params = []
        
        if current_user['role'] == 'client':
            query += " AND ma.client_id = %s"
            params.append(current_user['user_id'])
        elif client_id:
            query += " AND ma.client_id = %s"
            params.append(client_id)
        
        if asset_type:
            query += " AND ma.asset_type = %s"
            params.append(asset_type)
        
        if generation_type:
            query += " AND ma.generation_type = %s"
            params.append(generation_type)
        
        query += " ORDER BY ma.created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        assets = cursor.fetchall()
        
        return {
            "success": True,
            "data": assets
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch assets: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get specific asset by ID"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT 
                ma.*,
                u.full_name as creator_name,
                c.full_name as client_name
            FROM media_assets ma
            LEFT JOIN users u ON ma.created_by = u.user_id
            LEFT JOIN users c ON ma.client_id = c.user_id
            WHERE ma.asset_id = %s
        """, (asset_id,))
        
        asset = cursor.fetchone()
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        return {
            "success": True,
            "data": asset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch asset: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@router.get("/assets/{asset_id}/download")
async def download_asset(
    asset_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Download asset file - FIXED for MP4 animations"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT asset_id, asset_name, file_url, file_path, asset_type
            FROM media_assets 
            WHERE asset_id = %s
        """, (asset_id,))
        
        asset = cursor.fetchone()
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        # Check if file is still processing
        if not asset.get('file_url') or asset['file_url'] == '':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset is still processing. Please wait."
            )
        
        # Check if local file exists
        file_path = asset.get('file_path')
        if file_path and os.path.exists(file_path):
            # Determine media type - FIXED for animations
            media_types = {
                'image': 'image/png',
                'video': 'video/mp4',
                'animation': 'video/mp4',  # ✅ FIXED: Was 'image/gif', now 'video/mp4'
                'presentation': 'application/pdf'
            }
            media_type = media_types.get(asset['asset_type'], 'application/octet-stream')
            
            print(f"[DOWNLOAD] Serving local file: {file_path}")
            
            return FileResponse(
                path=file_path,
                filename=asset['asset_name'] or f"asset_{asset_id}",
                media_type=media_type
            )
        
        # Fallback: redirect to file_url
        file_url = asset.get('file_url')
        if file_url:
            print(f"[DOWNLOAD] Redirecting to URL: {file_url}")
            return {"redirect_url": file_url}
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset file not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DOWNLOAD] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download asset: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Delete media asset and its file"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get file path before deleting
        cursor.execute("""
            SELECT file_path FROM media_assets WHERE asset_id = %s
        """, (asset_id,))
        
        asset = cursor.fetchone()
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        # Delete from database
        cursor.execute("""
            DELETE FROM media_assets 
            WHERE asset_id = %s
        """, (asset_id,))
        
        connection.commit()
        
        # Delete file from disk if exists
        file_path = asset.get('file_path')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[STORAGE] Deleted file: {file_path}")
            except Exception as e:
                print(f"[STORAGE] Warning: Could not delete file {file_path}: {e}")
        
        return {
            "success": True,
            "message": "Asset deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete asset: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()