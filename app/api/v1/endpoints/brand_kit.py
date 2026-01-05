"""
Brand Kit Integration API Endpoints
Module 8: Creative Media Studio - Brand Kit Management
Automatically applies brand colors and fonts to AI-generated content
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.core.security import get_db_connection, require_admin_or_employee, get_current_user
import json

router = APIRouter(prefix="/api/v1/brand-kit", tags=["Brand Kit"])


# ========== PYDANTIC MODELS ==========

class BrandKitCreate(BaseModel):
    """Request model for creating/updating brand kit"""
    client_id: int
    primary_color: str = Field(..., description="Primary brand color in HEX format (e.g., #9926F3)")
    secondary_color: Optional[str] = Field(None, description="Secondary brand color in HEX")
    accent_color: Optional[str] = Field(None, description="Accent color in HEX")
    primary_font: str = Field("Gilroy", description="Primary font family")
    secondary_font: Optional[str] = Field("Arial", description="Secondary font family")
    logo_url: Optional[str] = Field(None, description="Primary logo URL")
    secondary_logo_url: Optional[str] = Field(None, description="Secondary/alternate logo URL")
    brand_voice: Optional[str] = Field("professional", description="Brand voice tone")
    usage_guidelines: Optional[Dict[str, Any]] = Field({}, description="Additional brand usage rules")


class BrandKitResponse(BaseModel):
    """Response model for brand kit"""
    brand_kit_id: int
    client_id: int
    primary_color: str
    secondary_color: Optional[str]
    accent_color: Optional[str]
    primary_font: str
    secondary_font: Optional[str]
    logo_url: Optional[str]
    secondary_logo_url: Optional[str]
    brand_voice: Optional[str]
    usage_guidelines: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str


# ========== HELPER FUNCTIONS ==========

def get_brand_kit_by_client(client_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve brand kit for a client"""
    connection = get_db_connection()
    cursor = connection.cursor()  # ✅ FIXED - No need for dictionary parameter
    
    try:
        cursor.execute("""
            SELECT * FROM brand_kits 
            WHERE client_id = %s
            ORDER BY updated_at DESC
            LIMIT 1
        """, (client_id,))
        
        brand_kit = cursor.fetchone()
        
        if brand_kit and brand_kit.get('usage_guidelines'):
            try:
                brand_kit['usage_guidelines'] = json.loads(brand_kit['usage_guidelines'])
            except:
                brand_kit['usage_guidelines'] = {}
        
        return brand_kit
        
    finally:
        cursor.close()
        connection.close()


def apply_brand_to_prompt(prompt: str, brand_kit: Dict[str, Any]) -> str:
    """
    Enhance AI generation prompt with brand guidelines
    Adds brand colors and style instructions to the prompt
    """
    if not brand_kit:
        return prompt
    
    brand_instructions = []
    
    # Add color palette
    if brand_kit.get('primary_color'):
        brand_instructions.append(f"Primary brand color: {brand_kit['primary_color']}")
    
    if brand_kit.get('secondary_color'):
        brand_instructions.append(f"Secondary color: {brand_kit['secondary_color']}")
    
    if brand_kit.get('accent_color'):
        brand_instructions.append(f"Accent color: {brand_kit['accent_color']}")
    
    # Add brand voice
    if brand_kit.get('brand_voice'):
        brand_instructions.append(f"Brand tone: {brand_kit['brand_voice']}")
    
    # Combine with original prompt
    if brand_instructions:
        enhanced_prompt = (
            f"{prompt}\n\nBrand Guidelines:\n" + 
            "\n".join([f"- {instruction}" for instruction in brand_instructions]) +
            "\n\nEnsure the design incorporates these brand colors and maintains brand consistency."
        )
        return enhanced_prompt
    
    return prompt


# ========== API ENDPOINTS ==========

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_brand_kit(
    request: BrandKitCreate,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Create or update brand kit for a client"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if brand kit already exists
        cursor.execute("""
            SELECT brand_kit_id FROM brand_kits 
            WHERE client_id = %s
        """, (request.client_id,))
        
        existing = cursor.fetchone()
        
        usage_guidelines_json = json.dumps(request.usage_guidelines or {})
        
        if existing:
            # Update existing brand kit
            cursor.execute("""
                UPDATE brand_kits SET
                    primary_color = %s,
                    secondary_color = %s,
                    accent_color = %s,
                    primary_font = %s,
                    secondary_font = %s,
                    logo_url = %s,
                    secondary_logo_url = %s,
                    brand_voice = %s,
                    usage_guidelines = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE client_id = %s
            """, (
                request.primary_color,
                request.secondary_color,
                request.accent_color,
                request.primary_font,
                request.secondary_font,
                request.logo_url,
                request.secondary_logo_url,
                request.brand_voice,
                usage_guidelines_json,
                request.client_id
            ))
            
            brand_kit_id = existing[0]
            message = "Brand kit updated successfully"
        else:
            # Create new brand kit
            cursor.execute("""
                INSERT INTO brand_kits (
                    client_id, primary_color, secondary_color, accent_color,
                    primary_font, secondary_font, logo_url, secondary_logo_url,
                    brand_voice, usage_guidelines
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.client_id,
                request.primary_color,
                request.secondary_color,
                request.accent_color,
                request.primary_font,
                request.secondary_font,
                request.logo_url,
                request.secondary_logo_url,
                request.brand_voice,
                usage_guidelines_json
            ))
            
            brand_kit_id = cursor.lastrowid
            message = "Brand kit created successfully"
        
        connection.commit()
        
        return {
            "success": True,
            "message": message,
            "brand_kit_id": brand_kit_id
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save brand kit: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/client/{client_id}")
async def get_client_brand_kit(
    client_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get brand kit for a specific client"""
    
    try:
        brand_kit = get_brand_kit_by_client(client_id)
        
        if not brand_kit:
            return {
                "success": False,
                "message": "No brand kit found for this client",
                "brand_kit": None
            }
        
        return {
            "success": True,
            "brand_kit": brand_kit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve brand kit: {str(e)}"
        )


@router.delete("/client/{client_id}")
async def delete_brand_kit(
    client_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Delete brand kit for a client"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            DELETE FROM brand_kits WHERE client_id = %s
        """, (client_id,))
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Brand kit deleted successfully"
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete brand kit: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.post("/apply-to-prompt")
async def apply_brand_to_prompt_endpoint(
    client_id: int,
    prompt: str,
    current_user: dict = Depends(get_current_user)
):
    """Apply brand guidelines to an AI generation prompt"""
    
    try:
        brand_kit = get_brand_kit_by_client(client_id)
        
        if not brand_kit:
            return {
                "success": True,
                "enhanced_prompt": prompt,
                "brand_applied": False,
                "message": "No brand kit found, using original prompt"
            }
        
        enhanced_prompt = apply_brand_to_prompt(prompt, brand_kit)
        
        return {
            "success": True,
            "enhanced_prompt": enhanced_prompt,
            "brand_applied": True,
            "brand_colors": {
                "primary": brand_kit.get('primary_color'),
                "secondary": brand_kit.get('secondary_color'),
                "accent": brand_kit.get('accent_color')
            },
            "brand_fonts": {
                "primary": brand_kit.get('primary_font'),
                "secondary": brand_kit.get('secondary_font')
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply brand guidelines: {str(e)}"
        )


# Export functions for use in media_studio.py
__all__ = ['get_brand_kit_by_client', 'apply_brand_to_prompt']