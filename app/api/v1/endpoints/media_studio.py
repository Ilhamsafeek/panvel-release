"""
Creative Media Studio API - Module 8 (UPDATED WITH LOCAL FILE STORAGE)
File: app/api/v1/endpoints/media_studio.py
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
                file_extension = 'gif'
            else:
                file_extension = 'bin'
        
        filename = f"{asset_type}_{timestamp}_{unique_id}.{file_extension}"
        
        # Create subdirectory for asset type
        type_dir = os.path.join(MEDIA_STORAGE_DIR, asset_type + "s")
        os.makedirs(type_dir, exist_ok=True)
        
        file_path = os.path.join(type_dir, filename)
        
        # Download the file
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Save to disk
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Generate relative URL for serving
        relative_path = f"/static/uploads/media_assets/{asset_type}s/{filename}"
        
        print(f"[STORAGE] File saved: {file_path}")
        
        return {
            "file_path": file_path,
            "file_url": relative_path,
            "filename": filename
        }
        
    except Exception as e:
        print(f"[STORAGE] Error saving file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


def save_base64_file(base64_data: str, asset_type: str, file_extension: str = None) -> Dict[str, str]:
    """
    Save base64 encoded data to local storage.
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
    """Request model for Synthesia video generation"""
    script: str = Field(..., description="Video script/narration")
    client_id: int
    avatar_id: Optional[str] = Field(None, description="Synthesia avatar ID")
    voice_id: Optional[str] = Field(None, description="Voice ID")
    background: Optional[str] = Field("white", description="Background color")
    title: Optional[str] = Field(None, description="Video title")


class AnimationGenerateRequest(BaseModel):
    """Request model for text-to-animation"""
    prompt: str = Field(..., description="Animation description")
    client_id: int
    title: str
    style: str = Field("modern", description="Animation style")
    duration: int = Field(5, description="Duration in seconds")


class ImageToVideoRequest(BaseModel):
    """Request model for image-to-video conversion"""
    client_id: int
    image_data: str = Field(..., description="Base64 encoded image")
    motion_prompt: str = Field(..., description="Motion description")
    duration: int = Field(5, description="Video duration in seconds")


class ImageToAnimationRequest(BaseModel):
    """Request model for image-to-animation conversion"""
    client_id: int
    image_data: str = Field(..., description="Base64 encoded image")
    animation_effect: str = Field(..., description="Animation effect description")
    animation_type: str = Field("loop", description="Animation type")


class CanvaDesignRequest(BaseModel):
    """Request model for Canva design"""
    design_type: str = Field(..., description="Design type: social_post, story, etc.")
    client_id: int
    title: str
    content_elements: Optional[Dict[str, Any]] = Field({}, description="Design content")


# ========== DALL-E IMAGE GENERATION ==========

async def generate_dalle_image(prompt: str, size: str, quality: str, style: str, n: int) -> Dict[str, Any]:
    """Generate images using DALL-E 3"""
    
    try:
        print(f"[DALL-E] Generating image: {prompt[:50]}...")
        
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
                "url": saved_file["file_url"],  # Use local URL
                "original_url": image_data.url,  # Keep original for reference
                "file_path": saved_file["file_path"],
                "filename": saved_file["filename"],
                "revised_prompt": getattr(image_data, 'revised_prompt', prompt)
            })
        
        print(f"[DALL-E] Successfully generated and saved {len(images)} image(s)")
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


# ========== SYNTHESIA VIDEO GENERATION ==========

async def generate_synthesia_video(
    script: str,
    avatar_id: Optional[str] = None,
    voice_id: Optional[str] = None,
    background: str = "white",
    title: Optional[str] = None
) -> Dict[str, Any]:
    """Generate video using Synthesia API"""
    
    try:
        print(f"[SYNTHESIA] Generating video: {script[:50]}...")
        
        api_url = "https://api.synthesia.io/v2/videos"
        avatar = avatar_id or settings.SYNTHESIA_AVATAR_ID or "anna_costume1_cameraA"
        
        headers = {
         "Authorization": f"Bearer {settings.SYNTHESIA_API_KEY}",  # ✅ Add "Bearer " prefix
         "Content-Type": "application/json",
         "Accept": "application/json"
        }
        
        payload = {
            "test": True,  # Use test mode
            "title": title or "Generated Video",
            "input": [
                {
                    "scriptText": script,
                    "avatar": avatar,
                    "background": background
                }
            ]
        }
        
        print(f"[SYNTHESIA] Sending request to: {api_url}")
        print(f"[SYNTHESIA] Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        print(f"[SYNTHESIA] Response Status: {response.status_code}")
        print(f"[SYNTHESIA] Response: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            video_id = result.get("id")
            
            print(f"[SYNTHESIA] Video created with ID: {video_id}")
            
            return {
                "success": True,
                "video_id": video_id,
                "status": "processing",
                "message": "Video is being generated. Check status endpoint for updates."
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("message") or error_data.get("error") or "Unknown error"
            
            print(f"[SYNTHESIA] Error: {error_msg}")
            print(f"[SYNTHESIA] Full error response: {response.text}")
            
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Synthesia API error: {error_msg}"
            )
            
    except requests.exceptions.Timeout:
        print(f"[SYNTHESIA] Request timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Synthesia API timeout"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SYNTHESIA] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesia generation failed: {str(e)}"
        )


# ========== IDEOGRAM ANIMATION GENERATION ==========
# ========== IDEOGRAM ANIMATION GENERATION ==========

async def generate_ideogram_animation(
    prompt: str,
    style: str = "modern",
    aspect_ratio: str = "16:9"
) -> Dict[str, Any]:
    """Generate animation using Ideogram API"""
    
    try:
        print(f"[IDEOGRAM] Generating animation: {prompt[:50]}...")
        
        api_url = "https://api.ideogram.ai/generate"
        
        headers = {
            "Api-Key": settings.IDEOGRAM_API_KEY,
            "Content-Type": "application/json"
        }
        
        # ✅ Map aspect ratios to Ideogram format
        aspect_ratio_map = {
            "1:1": "ASPECT_1_1",
            "16:9": "ASPECT_16_9",
            "9:16": "ASPECT_9_16",
            "4:3": "ASPECT_4_3",
            "3:4": "ASPECT_3_4",
            "10:16": "ASPECT_10_16",
            "16:10": "ASPECT_16_10",
            "3:2": "ASPECT_3_2",
            "2:3": "ASPECT_2_3",
            "3:1": "ASPECT_3_1",
            "1:3": "ASPECT_1_3"
        }
        
        ideogram_aspect_ratio = aspect_ratio_map.get(aspect_ratio, "ASPECT_1_1")
        
        # ✅ Map styles to Ideogram style types
        style_type_map = {
            "modern": "DESIGN",
            "realistic": "REALISTIC",
            "3d": "RENDER_3D",
            "anime": "ANIME",
            "auto": "AUTO"
        }
        
        ideogram_style = style_type_map.get(style.lower(), "AUTO")
        
        payload = {
            "image_request": {
                "prompt": prompt,  # ✅ Don't modify the prompt
                "model": "V_2",
                "aspect_ratio": ideogram_aspect_ratio,  # ✅ Use correct format
                "magic_prompt_option": "AUTO",
                "style_type": ideogram_style  # ✅ Add style
            }
        }
        
        print(f"[IDEOGRAM] Request payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        
        print(f"[IDEOGRAM] Response Status: {response.status_code}")
        print(f"[IDEOGRAM] Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("data") and len(result["data"]) > 0:
                image_url = result["data"][0].get("url")
                
                if image_url:
                    # Download and save locally
                    saved_file = download_and_save_file(
                        url=image_url,
                        asset_type='animation',
                        file_extension='png'  # Ideogram returns PNG
                    )
                    
                    print(f"[IDEOGRAM] Animation saved: {saved_file['file_path']}")
                    
                    return {
                        "success": True,
                        "url": saved_file["file_url"],
                        "original_url": image_url,
                        "file_path": saved_file["file_path"],
                        "filename": saved_file["filename"]
                    }
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No animation generated"
            )
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("message") or error_data.get("error") or "Unknown error"
            
            print(f"[IDEOGRAM] Error: {error_msg}")
            print(f"[IDEOGRAM] Full error response: {response.text}")
            
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ideogram API error: {error_msg}"
            )
            
    except requests.exceptions.Timeout:
        print(f"[IDEOGRAM] Request timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Ideogram API timeout"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[IDEOGRAM] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ideogram generation failed: {str(e)}"
        )


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



# ========== API ENDPOINTS ==========
@router.post("/generate/image")
async def generate_image(
    request: ImageGenerateRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Generate images using DALL-E 3"""
    
    connection = None
    cursor = None
    
    try:
        # Generate image
        result = await generate_dalle_image(
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
            style=request.style,
            n=request.n
        )
        
        # Save to database - NO dictionary=True here!
        connection = get_db_connection()
        cursor = connection.cursor()  # ← This is correct
        
        saved_assets = []
        
        for idx, image in enumerate(result["images"]):
            cursor.execute("""
                INSERT INTO media_assets (
                    client_id, created_by, asset_type, asset_name,
                    file_url, file_path, ai_generated, generation_type, prompt_used
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.client_id,
                current_user['user_id'],
                'image',
                f"DALL-E Image {idx + 1}",
                image["url"],
                image.get("file_path", ""),
                True,
                "dall-e-3",
                request.prompt
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
    """Generate video using Synthesia with automatic brand kit application"""
    
    connection = None
    cursor = None
    
    try:
        # ✅ GET BRAND KIT FOR METADATA
        brand_kit = get_brand_kit_by_client(request.client_id)
        
        # For video, include brand voice in the script if available
        enhanced_script = request.script
        if brand_kit and brand_kit.get('brand_voice'):
            enhanced_script = f"[Brand Voice: {brand_kit['brand_voice']}]\n\n{request.script}"
        
        print(f"[BRAND KIT] Video generation with brand voice: {brand_kit.get('brand_voice') if brand_kit else 'None'}")
        
        result = await generate_synthesia_video(
            script=enhanced_script,  # ✅ Use enhanced script
            avatar_id=request.avatar_id,
            voice_id=request.voice_id,
            background=brand_kit.get('primary_color') if brand_kit and request.background == 'white' else request.background,
            title=request.title
        )
        
        connection = get_db_connection()
        cursor = connection.cursor()  # ✅ Standard cursor
        
        # Save video asset with processing status
        cursor.execute("""
            INSERT INTO media_assets (
                client_id, created_by, asset_type, asset_name,
                file_url, ai_generated, generation_type, prompt_used,
                metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.client_id,
            current_user['user_id'],
            'video',
            request.title or "Synthesia Video",
            "",
            True,
            "synthesia",
            request.script,
            json.dumps({
                "video_id": result["video_id"],
                "status": "processing",
                "brand_applied": brand_kit is not None,
                "brand_voice": brand_kit.get('brand_voice') if brand_kit else None,
                "background_color": brand_kit.get('primary_color') if brand_kit else None
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



@router.get("/video-status/{video_id}")
async def get_video_status(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Check Synthesia video generation status and download if ready"""
    
    connection = None
    cursor = None
    
    try:
        api_url = f"https://api.synthesia.io/v2/videos/{video_id}"
        
        # ✅ CORRECTED HEADERS
        headers = {
            "Authorization": f"Bearer {settings.SYNTHESIA_API_KEY}",
            "Accept": "application/json"  # Add Accept header
        }
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        print(f"[SYNTHESIA] Status check for video {video_id}: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            video_status = result.get("status", "unknown")
            
            # If video is complete, download and save locally
            if video_status == "complete":
                download_url = result.get("download")
                
                if download_url:
                    # Download and save the video
                    saved_file = download_and_save_file(
                        url=download_url,
                        asset_type='video',
                        file_extension='mp4'
                    )
                    
                    # Update the database with local file URL
                    connection = get_db_connection()
                    cursor = connection.cursor()
                    
                    cursor.execute("""
                        UPDATE media_assets 
                        SET file_url = %s, file_path = %s, 
                            metadata = JSON_SET(COALESCE(metadata, '{}'), '$.status', 'complete')
                        WHERE metadata->>'$.video_id' = %s
                    """, (saved_file["file_url"], saved_file["file_path"], video_id))
                    
                    connection.commit()
                    
                    return {
                        "success": True,
                        "video_id": video_id,
                        "status": "complete",
                        "url": saved_file["file_url"],
                        "download_url": saved_file["file_url"]
                    }
            
            return {
                "success": True,
                "video_id": video_id,
                "status": video_status
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to get video status"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video status: {str(e)}"
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
    """Generate animation using Ideogram with automatic brand kit application"""
    
    connection = None
    cursor = None
    
    try:
        # ✅ GET BRAND KIT AND APPLY TO PROMPT
        brand_kit = get_brand_kit_by_client(request.client_id)
        enhanced_prompt = apply_brand_to_prompt(request.prompt, brand_kit) if brand_kit else request.prompt
        
        print(f"[BRAND KIT] Animation - Original prompt: {request.prompt}")
        print(f"[BRAND KIT] Animation - Enhanced prompt: {enhanced_prompt}")
        
        result = await generate_ideogram_animation(
            prompt=enhanced_prompt,  # ✅ Use enhanced prompt
            style=request.style,
            aspect_ratio="16:9"
        )
        
        connection = get_db_connection()
        cursor = connection.cursor()  # ✅ Standard cursor
      
        cursor.execute("""
            INSERT INTO media_assets (
                client_id, created_by, asset_type, asset_name,
                file_url, file_path, ai_generated, generation_type, prompt_used,
                metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.client_id,
            current_user['user_id'],
            'animation',
            request.title,
            result["url"],
            result.get("file_path", ""),
            True,
            "ideogram",
            request.prompt,
            json.dumps({
                "original_prompt": request.prompt,
                "enhanced_prompt": enhanced_prompt,
                "brand_applied": brand_kit is not None,
                "brand_colors": {
                    "primary": brand_kit.get('primary_color') if brand_kit else None
                }
            })
        ))
        
        asset_id = cursor.lastrowid
        connection.commit()
        
        return {
            "success": True,
            "asset_id": asset_id,
            "url": result["url"],
            "brand_applied": brand_kit is not None
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
    """Convert image to video using GPT-4 + Synthesia"""
    
    connection = None
    cursor = None
    
    try:
        # First save the uploaded image locally
        saved_image = save_base64_file(
            base64_data=request.image_data,
            asset_type='image',
            file_extension='png'
        )
        
        # Generate script using GPT-4
        script_response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative scriptwriter. Generate a short, engaging video narration based on the motion description provided."
                },
                {
                    "role": "user",
                    "content": f"Create a {request.duration} second video script for this motion: {request.motion_prompt}"
                }
            ],
            max_tokens=200
        )
        
        script = script_response.choices[0].message.content
        
        # Generate video with Synthesia
        video_result = await generate_synthesia_video(
            script=script,
            title=f"Image Video - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO media_assets (
                client_id, created_by, asset_type, asset_name,
                file_url, ai_generated, generation_type, prompt_used,
                metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.client_id,
            current_user['user_id'],
            'video',
            f"Image-to-Video",
            "",
            True,
            "synthesia",
            request.motion_prompt,
            json.dumps({
                "video_id": video_result["video_id"],
                "status": "processing",
                "source_image": saved_image["file_url"]
            })
        ))
        
        asset_id = cursor.lastrowid
        connection.commit()
        
        return {
            "success": True,
            "asset_id": asset_id,
            "video_id": video_result["video_id"],
            "status": "processing",
            "script": script
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
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
    """Convert image to animation using Ideogram"""
    
    connection = None
    cursor = None
    
    try:
        # Save the uploaded image locally first
        saved_image = save_base64_file(
            base64_data=request.image_data,
            asset_type='image',
            file_extension='png'
        )
        
        # Generate animation prompt based on the effect
        animation_prompt = f"Animate with {request.animation_effect} effect, {request.animation_type} style animation"
        
        result = await generate_ideogram_animation(
            prompt=animation_prompt,
            style=request.animation_type
        )
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO media_assets (
                client_id, created_by, asset_type, asset_name,
                file_url, file_path, ai_generated, generation_type, prompt_used,
                metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.client_id,
            current_user['user_id'],
            'animation',
            f"Image-to-Animation",
            result["url"],
            result.get("file_path", ""),
            True,
            "ideogram",
            request.animation_effect,
            json.dumps({"source_image": saved_image["file_url"]})
        ))
        
        asset_id = cursor.lastrowid
        connection.commit()
        
        return {
            "success": True,
            "asset_id": asset_id,
            "url": result["url"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert image to animation: {str(e)}"
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
    """Download asset file"""
    
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
        
        # Check if local file exists
        file_path = asset.get('file_path')
        if file_path and os.path.exists(file_path):
            # Determine media type
            media_types = {
                'image': 'image/png',
                'video': 'video/mp4',
                'animation': 'image/gif',
                'presentation': 'application/pdf'
            }
            media_type = media_types.get(asset['asset_type'], 'application/octet-stream')
            
            return FileResponse(
                path=file_path,
                filename=asset['asset_name'] or f"asset_{asset_id}",
                media_type=media_type
            )
        
        # Fallback: redirect to file_url
        file_url = asset.get('file_url')
        if file_url:
            return {"redirect_url": file_url}
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset file not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
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