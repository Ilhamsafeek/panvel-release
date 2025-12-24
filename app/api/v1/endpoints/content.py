"""
Content Intelligence Hub API - Module 5
File: app/api/v1/endpoints/content.py

AI-powered content creation and optimization
"""
import os
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import pymysql
import json
import re
from openai import OpenAI
import base64
from fastapi import Body
import requests

from app.core.config import settings
from app.core.security import require_admin_or_employee, get_current_user
from app.core.security import get_db_connection

router = APIRouter()

# Initialize OpenAI client
openai_client = None
try:
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
except Exception as e:
    print(f"OpenAI client initialization failed: {e}")


# Google Cloud Vision API - Support both service account and API key
vision_client = None
vision_available = False
use_rest_api = False  # Flag to determine which method to use

try:
    from google.cloud import vision
    from google.oauth2 import service_account
    
    # Try to use service account credentials first
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if credentials_path and os.path.exists(credentials_path):
        # Use service account with Python library
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        vision_client = vision.ImageAnnotatorClient(credentials=credentials)
        vision_available = True
        use_rest_api = False
        print("✅ Google Cloud Vision API initialized with service account")
    else:
        # Check for API key
        api_key = os.getenv('GOOGLE_VISION_API_KEY') or getattr(settings, 'GOOGLE_VISION_API_KEY', None)
        
        if api_key:
            # Use REST API approach (library doesn't support API key directly)
            vision_available = True
            use_rest_api = True
            vision_client = None  # Not using the library
            print("✅ Google Cloud Vision API configured with API key (REST mode)")
        else:
            vision_available = False
            vision_client = None
            print("⚠️ No Google Vision credentials found (need service account JSON or API key)")
            
except ImportError:
    # google-cloud-vision not installed, try API key only
    api_key = os.getenv('GOOGLE_VISION_API_KEY') or getattr(settings, 'GOOGLE_VISION_API_KEY', None)
    
    if api_key:
        vision_available = True
        use_rest_api = True
        vision_client = None
        print("✅ Google Cloud Vision API configured with API key (REST mode)")
    else:
        vision_available = False
        use_rest_api = False
        vision_client = None
        print("⚠️ Google Cloud Vision not available")
except Exception as e:
    vision_available = False
    use_rest_api = False
    vision_client = None
    print(f"❌ Google Cloud Vision initialization error: {e}")




# ========== PYDANTIC MODELS ==========

class ContentGenerateRequest(BaseModel):
    """Request model for AI content generation"""
    platform: str = Field(..., description="Social media platform")
    content_type: str = Field(..., description="Type of content")
    topic: str = Field(..., description="Content topic/brief")
    tone: Optional[str] = Field("professional", description="Content tone")
    target_audience: Optional[str] = Field(None, description="Target audience")
    keywords: Optional[List[str]] = Field([], description="Keywords to include")
    client_id: Optional[int] = Field(None, description="Client ID")


class MultiPlatformContentRequest(BaseModel):
    """Request model for multi-platform AI content generation"""
    client_id: int = Field(..., description="Client ID")
    platforms: List[str] = Field(..., description="List of social media platforms")
    content_type: str = Field(..., description="Type of content")
    topic: str = Field(..., description="Content topic/brief")
    tone: Optional[str] = Field("professional", description="Content tone")
    target_audience: Optional[str] = Field(None, description="Target audience")
    keywords: Optional[List[str]] = Field([], description="Keywords to include")
    generate_audience_insights: Optional[bool] = Field(True, description="Generate AI audience insights")


class ContentSaveRequest(BaseModel):
    """Request model for saving content"""
    client_id: int
    platform: str
    content_type: str
    title: Optional[str] = None
    content_text: str
    hashtags: Optional[List[str]] = []
    cta_text: Optional[str] = None
    optimization_score: Optional[float] = None
    status: str = "draft"


class ContentUpdateRequest(BaseModel):
    """Request model for updating content"""
    title: Optional[str] = None
    content_text: Optional[str] = None
    hashtags: Optional[List[str]] = None
    cta_text: Optional[str] = None
    optimization_score: Optional[float] = None
    status: Optional[str] = None


# ========== HELPER FUNCTIONS ==========

def get_platform_guidelines(platform: str) -> Dict[str, Any]:
    """Get platform-specific content guidelines"""
    guidelines = {
        "instagram": {
            "max_chars": 2200,
            "optimal_chars": 150,
            "hashtag_limit": 30,
            "optimal_hashtags": "8-15",
            "best_practices": [
                "Use emojis to increase engagement",
                "Ask questions to encourage comments",
                "Include call-to-action in first line",
                "Use line breaks for readability"
            ]
        },
        "facebook": {
            "max_chars": 63206,
            "optimal_chars": 250,
            "hashtag_limit": 10,
            "optimal_hashtags": "1-3",
            "best_practices": [
                "Keep posts concise and scannable",
                "Use native video when possible",
                "Tag relevant pages and people",
                "Post when audience is most active"
            ]
        },
        "linkedin": {
            "max_chars": 3000,
            "optimal_chars": 150,
            "hashtag_limit": 30,
            "optimal_hashtags": "3-5",
            "best_practices": [
                "Lead with value or insight",
                "Use professional tone",
                "Include industry-specific hashtags",
                "Tag relevant professionals"
            ]
        },
        "twitter": {
            "max_chars": 280,
            "optimal_chars": 240,
            "hashtag_limit": 10,
            "optimal_hashtags": "1-2",
            "best_practices": [
                "Be concise and impactful",
                "Use trending hashtags strategically",
                "Include media for higher engagement",
                "Engage with replies quickly"
            ]
        },
        "pinterest": {
            "max_chars": 500,
            "optimal_chars": 200,
            "hashtag_limit": 20,
            "optimal_hashtags": "5-10",
            "best_practices": [
                "Use keyword-rich descriptions",
                "Include compelling calls-to-action",
                "Add relevant hashtags",
                "Describe image content clearly"
            ]
        },
        "youtube": {
            "max_chars": 5000,
            "optimal_chars": 300,
            "hashtag_limit": 15,
            "optimal_hashtags": "3-5",
            "best_practices": [
                "Include keywords in first 100 characters",
                "Add timestamps for longer videos",
                "Include clear call-to-action",
                "Use relevant tags"
            ]
        }
    }
    
    return guidelines.get(platform.lower(), {
        "max_chars": 2000,
        "optimal_chars": 200,
        "hashtag_limit": 10,
        "optimal_hashtags": "3-5",
        "best_practices": []
    })


def generate_ai_content(
    platform: str,
    content_type: str,
    topic: str,
    tone: str,
    target_audience: Optional[str] = None,
    keywords: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generate content using OpenAI"""
    
    if not openai_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available"
        )
    
    guidelines = get_platform_guidelines(platform)
    
    prompt = f"""Create engaging {platform} content for the following:

Topic: {topic}
Content Type: {content_type}
Tone: {tone}
Platform: {platform}
Target Audience: {target_audience or 'General audience'}
"""

    if keywords:
        prompt += f"\nKeywords to include: {', '.join(keywords)}"
    
    prompt += f"""

Platform Guidelines:
- Optimal length: {guidelines['optimal_chars']} characters
- Maximum length: {guidelines['max_chars']} characters
- Optimal hashtags: {guidelines['optimal_hashtags']}

Requirements:
1. Create {content_type} content optimized for {platform}
2. Use {tone} tone
3. Include engaging hook in the first line
4. Make it actionable and valuable
5. Keep within optimal character limit
6. DO NOT include hashtags in the main content

Provide the response in this JSON format:
{{
    "content": "The main content text without hashtags",
    "headline": "Attention-grabbing headline (if applicable)",
    "cta": "Clear call-to-action"
}}
"""

    try:
        response = openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert social media content creator specializing in platform-specific optimization. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        response_text = response.choices[0].message.content
        
        # Parse JSON from response
        try:
            content_data = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                content_data = json.loads(json_match.group(0))
            else:
                content_data = {
                    "content": response_text,
                    "headline": "",
                    "cta": ""
                }
        
        content_length = len(content_data.get('content', ''))
        
        return {
            "content": content_data.get('content', ''),
            "headline": content_data.get('headline', ''),
            "cta": content_data.get('cta', ''),
            "caption": content_data.get('content', ''),
            "guidelines": guidelines,
            "character_count": content_length
        }
        
    except Exception as e:
        print(f"Error generating content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )


def generate_hashtags(platform: str, topic: str, keywords: Optional[List[str]] = None, count: int = 10) -> List[str]:
    """Generate relevant hashtags using AI"""
    
    if not openai_client:
        return []
    
    guidelines = get_platform_guidelines(platform)
    
    prompt = f"""Generate {count} relevant hashtags for {platform} content about: {topic}

Requirements:
- Mix of popular and niche hashtags
- Relevant to {platform} audience
- Include trending hashtags when applicable
- Format: Return only a JSON array of hashtag strings (without # symbol)

Example: ["socialmedia", "marketing", "digitalstrategy"]
"""
    
    if keywords:
        prompt += f"\nInclude variations of these keywords: {', '.join(keywords)}"
    
    try:
        response = openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a hashtag optimization expert. Return only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        content = response.choices[0].message.content
        
        try:
            hashtags = json.loads(content)
            return hashtags if isinstance(hashtags, list) else []
        except:
            return re.findall(r'#?(\w+)', content)[:count]
            
    except Exception as e:
        print(f"Hashtag generation error: {e}")
        return []


async def calculate_performance_score(
    content_text: str,
    platform: str,
    target_audience: Optional[str] = None,
    keywords: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Calculate content performance score (1-100)"""
    
    guidelines = get_platform_guidelines(platform)
    content_length = len(content_text)
    
    # Length score (40% weight)
    optimal_length = guidelines['optimal_chars']
    max_length = guidelines['max_chars']
    
    if content_length <= optimal_length:
        length_score = (content_length / optimal_length) * 100
    elif content_length <= max_length:
        length_score = 100 - ((content_length - optimal_length) / (max_length - optimal_length)) * 30
    else:
        length_score = 40
    
    # Engagement indicators (30% weight)
    engagement_score = 50
    if '?' in content_text:
        engagement_score += 15
    if any(word in content_text.lower() for word in ['you', 'your', "you're"]):
        engagement_score += 10
    if any(cta in content_text.lower() for cta in ['click', 'learn', 'discover', 'get', 'try', 'join', 'start']):
        engagement_score += 15
    if content_text.strip() and content_text[0].isupper():
        engagement_score += 10
    
    engagement_score = min(100, engagement_score)
    
    # Keyword integration (30% weight)
    keyword_score = 70
    if keywords:
        keywords_found = sum(1 for kw in keywords if kw.lower() in content_text.lower())
        keyword_score = (keywords_found / len(keywords)) * 100 if keywords else 70
    
    overall_score = (length_score * 0.4) + (engagement_score * 0.3) + (keyword_score * 0.3)
    overall_score = min(100, max(0, overall_score))
    
    return {
        "overall_score": round(overall_score, 1),
        "length_score": round(length_score, 1),
        "engagement_score": round(engagement_score, 1),
        "keyword_score": round(keyword_score, 1),
        "optimization_status": "Optimized" if overall_score >= 70 else "Needs Improvement",
        "character_count": content_length,
        "optimal_length": optimal_length,
        "max_length": max_length
    }
async def generate_audience_and_keywords(
    client_id: int,
    topic: str,
    platform: str,
    industry: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate target audience and keywords based on client profile
    FIXED VERSION with proper error handling
    """
    
    # Check if OpenAI client is available
    if not openai_client:
        print("❌ [AUDIENCE INSIGHTS] OpenAI client not initialized!")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available. OpenAI client not initialized."
        )
    
    connection = None
    cursor = None
    
    try:
        print(f"✅ [AUDIENCE INSIGHTS] Starting for client_id={client_id}, topic={topic}, platform={platform}")
        
        # Get client data from database
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # FIXED: Use correct table names - client_profiles instead of clients
        cursor.execute("""
            SELECT 
                u.full_name, 
                u.email,
                cp.business_name as company_name,
                cp.business_type,
                cp.website_url,
                pp.target_audience as existing_audience,
                pp.business_type as proposal_business_type
            FROM users u
            LEFT JOIN client_profiles cp ON u.user_id = cp.client_id
            LEFT JOIN project_proposals pp ON u.user_id = pp.client_id
            WHERE u.user_id = %s
            ORDER BY pp.created_at DESC
            LIMIT 1
        """, (client_id,))
        
        client_data = cursor.fetchone()
        
        if not client_data:
            print(f"⚠️ [AUDIENCE INSIGHTS] Client {client_id} not found in database")
            # Continue with minimal context
            client_context = f"""
Client Profile:
- Client ID: {client_id}
- Industry: {industry or 'General'}
- Note: Limited client information available
"""
        else:
            print(f"✅ [AUDIENCE INSIGHTS] Found client: {client_data.get('full_name', 'N/A')}")
            # Use the correct field names from our query
            company_name = client_data.get('company_name') or client_data.get('business_name') or 'N/A'
            business_type = client_data.get('business_type') or client_data.get('proposal_business_type') or 'N/A'
            
            client_context = f"""
Client Profile:
- Name: {client_data.get('full_name', 'N/A')}
- Company: {company_name}
- Business Type: {business_type}
- Industry: {industry or 'General'}
- Existing Target Audience: {client_data.get('existing_audience', 'Not specified')}
- Website: {client_data.get('website_url', 'N/A')}
"""
        
        # Create comprehensive prompt for OpenAI
        prompt = f"""Based on the following client profile and content topic, generate comprehensive target audience and keywords for {platform} content.

{client_context}

Topic: {topic}
Platform: {platform}

IMPORTANT: Provide a detailed, specific response in this EXACT JSON format (no markdown, no code blocks):
{{
    "target_audience": {{
        "description": "Detailed 2-3 sentence description of the ideal target audience for this content",
        "demographics": ["age range", "gender", "location", "income level", "education"],
        "interests": ["specific interest 1", "specific interest 2", "specific interest 3", "specific interest 4"],
        "behaviors": ["online behavior 1", "purchasing behavior 2", "content consumption behavior 3"],
        "pain_points": ["specific pain point 1", "pain point 2", "pain point 3"],
        "goals": ["audience goal 1", "goal 2", "goal 3"]
    }},
    "keywords": {{
        "primary": ["highly relevant keyword 1", "keyword 2", "keyword 3", "keyword 4", "keyword 5"],
        "secondary": ["supporting keyword 1", "keyword 2", "keyword 3", "keyword 4", "keyword 5"]
    }},
    "content_recommendations": {{
        "best_time_to_post": "Specific day and time recommendation with reasoning",
        "content_angle": "Specific content angle that will resonate with this audience",
        "cta_suggestion": "Specific call-to-action that matches audience intent"
    }}
}}

Requirements:
- Be SPECIFIC, not generic
- Base recommendations on the client's industry and business type
- Use actual behavioral data for {platform}
- Include demographic details relevant to {topic}
- Provide actionable keywords, not just topic words
- Make it ready to use immediately

Respond with ONLY the JSON object, no additional text or markdown formatting."""
        
        print(f"📤 [AUDIENCE INSIGHTS] Sending request to OpenAI GPT-4...")
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 for better quality
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert digital marketing strategist with deep knowledge of audience targeting, keyword research, and platform-specific content optimization. Always respond with valid, well-structured JSON without any markdown formatting."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1200  # Increased for more detailed responses
        )
        
        response_text = response.choices[0].message.content.strip()
        print(f"📥 [AUDIENCE INSIGHTS] Received response from OpenAI ({len(response_text)} chars)")
        
        # Clean response - remove markdown code blocks if present
        if response_text.startswith('```'):
            print("⚠️ [AUDIENCE INSIGHTS] Response has markdown formatting, cleaning...")
            # Remove ```json and ``` markers
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
            print(f"✅ [AUDIENCE INSIGHTS] Successfully parsed JSON response")
            
            # Validate response structure
            if 'target_audience' not in result:
                print("⚠️ [AUDIENCE INSIGHTS] Missing 'target_audience' key, adding default")
                result['target_audience'] = {"description": "General audience"}
            
            if 'keywords' not in result:
                print("⚠️ [AUDIENCE INSIGHTS] Missing 'keywords' key, adding default")
                result['keywords'] = {"primary": [], "secondary": []}
            
            if 'content_recommendations' not in result:
                print("⚠️ [AUDIENCE INSIGHTS] Missing 'content_recommendations' key, adding default")
                result['content_recommendations'] = {}
            
            # Log what we're returning
            audience_desc = result.get('target_audience', {}).get('description', '')
            primary_keywords = result.get('keywords', {}).get('primary', [])
            print(f"✅ [AUDIENCE INSIGHTS] Returning: audience='{audience_desc[:50]}...', keywords={len(primary_keywords)}")
            
            return result
            
        except json.JSONDecodeError as json_err:
            print(f"❌ [AUDIENCE INSIGHTS] JSON decode error: {str(json_err)}")
            print(f"📄 [AUDIENCE INSIGHTS] Raw response: {response_text[:500]}")
            
            # Try to extract JSON using regex
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                print("🔍 [AUDIENCE INSIGHTS] Trying regex extraction...")
                try:
                    result = json.loads(json_match.group(0))
                    print(f"✅ [AUDIENCE INSIGHTS] Regex extraction successful")
                    return result
                except:
                    pass
            
            # If all parsing fails, raise an error instead of returning fallback
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse AI response. Please try again. Error: {str(json_err)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"❌ [AUDIENCE INSIGHTS] Unexpected error: {error_msg}")
        import traceback
        print(f"📄 [AUDIENCE INSIGHTS] Traceback: {traceback.format_exc()}")
        
        # Don't return fallback data - raise error so frontend knows something went wrong
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate audience insights: {error_msg}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# Also update the endpoint to show errors properly
@router.post("/audience-insights")
async def get_audience_insights_endpoint(
    client_id: int = Body(...),
    topic: str = Body(...),
    platform: str = Body("instagram"),
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get AI-generated audience insights and keywords
    BRD REQUIREMENT: AI generate target audience & keywords based on client profile
    FIXED VERSION with proper error handling
    """
    try:
        print(f"\n{'='*60}")
        print(f"🚀 [ENDPOINT] Audience Insights Request")
        print(f"   Client ID: {client_id}")
        print(f"   Topic: {topic}")
        print(f"   Platform: {platform}")
        print(f"   User: {current_user.get('email', 'Unknown')}")
        print(f"{'='*60}\n")
        
        insights = await generate_audience_and_keywords(
            client_id=client_id,
            topic=topic,
            platform=platform
        )
        
        print(f"\n✅ [ENDPOINT] Successfully generated insights")
        print(f"   Audience: {insights.get('target_audience', {}).get('description', '')[:80]}...")
        print(f"   Primary Keywords: {len(insights.get('keywords', {}).get('primary', []))}")
        print(f"   Secondary Keywords: {len(insights.get('keywords', {}).get('secondary', []))}\n")
        
        return {
            "success": True,
            "data": insights
        }
        
    except HTTPException as http_err:
        print(f"\n❌ [ENDPOINT] HTTP Exception: {http_err.detail}\n")
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ [ENDPOINT] Unexpected error: {error_msg}\n")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating audience insights: {error_msg}"
        )

# Also update the endpoint to show errors properly
@router.post("/audience-insights")
async def get_audience_insights_endpoint(
    client_id: int = Body(...),
    topic: str = Body(...),
    platform: str = Body("instagram"),
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get AI-generated audience insights and keywords
    BRD REQUIREMENT: AI generate target audience & keywords based on client profile
    FIXED VERSION with proper error handling
    """
    try:
        print(f"\n{'='*60}")
        print(f"🚀 [ENDPOINT] Audience Insights Request")
        print(f"   Client ID: {client_id}")
        print(f"   Topic: {topic}")
        print(f"   Platform: {platform}")
        print(f"   User: {current_user.get('email', 'Unknown')}")
        print(f"{'='*60}\n")
        
        insights = await generate_audience_and_keywords(
            client_id=client_id,
            topic=topic,
            platform=platform
        )
        
        print(f"\n✅ [ENDPOINT] Successfully generated insights")
        print(f"   Audience: {insights.get('target_audience', {}).get('description', '')[:80]}...")
        print(f"   Primary Keywords: {len(insights.get('keywords', {}).get('primary', []))}")
        print(f"   Secondary Keywords: {len(insights.get('keywords', {}).get('secondary', []))}\n")
        
        return {
            "success": True,
            "data": insights
        }
        
    except HTTPException as http_err:
        print(f"\n❌ [ENDPOINT] HTTP Exception: {http_err.detail}\n")
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ [ENDPOINT] Unexpected error: {error_msg}\n")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating audience insights: {error_msg}"
        )


# ========== API ENDPOINTS ==========

@router.post("/generate")
async def generate_content(
    request: ContentGenerateRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Generate AI-powered content for social media"""
    
    try:
        result = generate_ai_content(
            platform=request.platform,
            content_type=request.content_type,
            topic=request.topic,
            tone=request.tone,
            target_audience=request.target_audience,
            keywords=request.keywords
        )
        
        hashtags = generate_hashtags(
            platform=request.platform,
            topic=request.topic,
            keywords=request.keywords
        )
        
        performance = await calculate_performance_score(
            content_text=result.get('content', ''),
            platform=request.platform,
            target_audience=request.target_audience,
            keywords=request.keywords
        )
        
        return {
            "success": True,
            "data": {
                **result,
                "hashtags": hashtags,
                "performance_score": performance.get('overall_score', 0),
                "optimization_status": performance.get('optimization_status', 'Unknown'),
                "performance_analysis": performance
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in generate_content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/intelligence/generate")
async def generate_multi_platform_content(
    request: MultiPlatformContentRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Generate AI-powered content for multiple platforms simultaneously
    BRD REQUIREMENT: Content Intelligence Hub - Multi-platform content generation
    """
    try:
        if not openai_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service not available"
            )
        
        # Generate audience insights if requested
        audience_insights = None
        suggested_keywords = None
        
        if request.generate_audience_insights and request.client_id:
            try:
                ai_data = await generate_audience_and_keywords(
                    client_id=request.client_id,
                    topic=request.topic,
                    platform=request.platforms[0] if request.platforms else "instagram",
                    industry=None
                )
                audience_insights = ai_data.get('target_audience', {})
                suggested_keywords = ai_data.get('keywords', {})
            except Exception as e:
                print(f"Warning: Could not generate audience insights: {e}")
        
        # Use AI-generated audience if not provided
        target_audience = request.target_audience
        if not target_audience and audience_insights:
            if isinstance(audience_insights, dict):
                target_audience = audience_insights.get('description', '')
            else:
                target_audience = str(audience_insights)
        
        # Merge keywords
        keywords = request.keywords or []
        if suggested_keywords:
            if isinstance(suggested_keywords, dict):
                ai_keywords = suggested_keywords.get('primary', []) + suggested_keywords.get('secondary', [])
                keywords = list(set(keywords + ai_keywords))
            elif isinstance(suggested_keywords, list):
                keywords = list(set(keywords + suggested_keywords))
        
        # Generate content for each platform
        variants = []
        
        for platform in request.platforms:
            try:
                result = generate_ai_content(
                    platform=platform,
                    content_type=request.content_type,
                    topic=request.topic,
                    tone=request.tone,
                    target_audience=target_audience,
                    keywords=keywords
                )
                
                hashtags = generate_hashtags(
                    platform=platform,
                    topic=request.topic,
                    keywords=keywords
                )
                
                performance = await calculate_performance_score(
                    content_text=result.get('content', ''),
                    platform=platform,
                    target_audience=target_audience,
                    keywords=keywords
                )
                
                guidelines = get_platform_guidelines(platform)
                
                variants.append({
                    "platform": platform,
                    "content": result.get('content', ''),
                    "caption": result.get('caption', result.get('content', '')),
                    "headline": result.get('headline', ''),
                    "hashtags": hashtags,
                    "cta": result.get('cta', ''),
                    "performance_score": performance.get('overall_score', 0),
                    "optimization_status": performance.get('optimization_status', 'Unknown'),
                    "is_optimized": performance.get('overall_score', 0) >= 70,
                    "guidelines": guidelines,
                    "character_count": len(result.get('content', '')),
                    "optimal_length": guidelines.get('optimal_chars', 150)
                })
                
            except Exception as e:
                print(f"Error generating content for {platform}: {e}")
                variants.append({
                    "platform": platform,
                    "error": str(e),
                    "content": "",
                    "caption": "",
                    "hashtags": [],
                    "performance_score": 0,
                    "is_optimized": False
                })
        
        return {
            "success": True,
            "data": {
                "variants": variants,
                "audience_insights": audience_insights,
                "suggested_keywords": suggested_keywords,
                "topic": request.topic,
                "content_type": request.content_type,
                "tone": request.tone
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in generate_multi_platform_content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/save")
async def save_content(
    request: ContentSaveRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Save content to library"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO content_library (
                client_id, created_by, platform, content_type,
                title, content_text, hashtags, cta_text,
                ai_generated, optimization_score, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.client_id,
            current_user['user_id'],
            request.platform,
            request.content_type,
            request.title,
            request.content_text,
            json.dumps(request.hashtags),
            request.cta_text,
            True,
            request.optimization_score,
            request.status
        ))
        
        connection.commit()
        content_id = cursor.lastrowid
        
        return {
            "success": True,
            "message": "Content saved successfully",
            "content_id": content_id
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error saving content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save content: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/list")
async def list_content(
    client_id: Optional[int] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get list of content from library"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                cl.*,
                u.full_name as creator_name,
                c.full_name as client_name
            FROM content_library cl
            LEFT JOIN users u ON cl.created_by = u.user_id
            LEFT JOIN users c ON cl.client_id = c.user_id
            WHERE 1=1
        """
        params = []
        
        if current_user['role'] == 'client':
            query += " AND cl.client_id = %s"
            params.append(current_user['user_id'])
        elif client_id:
            query += " AND cl.client_id = %s"
            params.append(client_id)
        
        if platform:
            query += " AND cl.platform = %s"
            params.append(platform)
        
        if status:
            query += " AND cl.status = %s"
            params.append(status)
        
        query += " ORDER BY cl.created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        content_list = cursor.fetchall()
        
        for content in content_list:
            if content.get('hashtags'):
                try:
                    content['hashtags'] = json.loads(content['hashtags'])
                except:
                    content['hashtags'] = []
        
        return {
            "success": True,
            "data": content_list
        }
        
    except Exception as e:
        print(f"Error fetching content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch content: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/{content_id}")
async def get_content(
    content_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get specific content by ID"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT 
                cl.*,
                u.full_name as creator_name,
                c.full_name as client_name
            FROM content_library cl
            LEFT JOIN users u ON cl.created_by = u.user_id
            LEFT JOIN users c ON cl.client_id = c.user_id
            WHERE cl.content_id = %s
        """, (content_id,))
        
        content = cursor.fetchone()
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        if content.get('hashtags'):
            try:
                content['hashtags'] = json.loads(content['hashtags'])
            except:
                content['hashtags'] = []
        
        return {
            "success": True,
            "data": content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch content: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.put("/{content_id}")
async def update_content(
    content_id: int,
    request: ContentUpdateRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Update existing content"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        update_fields = []
        params = []
        
        if request.title is not None:
            update_fields.append("title = %s")
            params.append(request.title)
        
        if request.content_text is not None:
            update_fields.append("content_text = %s")
            params.append(request.content_text)
        
        if request.hashtags is not None:
            update_fields.append("hashtags = %s")
            params.append(json.dumps(request.hashtags))
        
        if request.cta_text is not None:
            update_fields.append("cta_text = %s")
            params.append(request.cta_text)
        
        if request.optimization_score is not None:
            update_fields.append("optimization_score = %s")
            params.append(request.optimization_score)
        
        if request.status is not None:
            update_fields.append("status = %s")
            params.append(request.status)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        params.append(content_id)
        
        query = f"""
            UPDATE content_library 
            SET {', '.join(update_fields)}
            WHERE content_id = %s
        """
        
        cursor.execute(query, tuple(params))
        connection.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        return {
            "success": True,
            "message": "Content updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error updating content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update content: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@router.delete("/{content_id}")
async def delete_content(
    content_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Delete content from library"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # First, check if content exists
        cursor.execute("SELECT content_id FROM content_library WHERE content_id = %s", (content_id,))
        content = cursor.fetchone()
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        # Check if content is being used in social media posts
        cursor.execute("""
            SELECT COUNT(*) as post_count 
            FROM social_media_posts 
            WHERE content_id = %s
        """, (content_id,))
        
        result = cursor.fetchone()
        
        if result['post_count'] > 0:
            # Set content_id to NULL in social_media_posts to preserve posts
            cursor.execute("""
                UPDATE social_media_posts 
                SET content_id = NULL 
                WHERE content_id = %s
            """, (content_id,))
        
        # Now delete the content
        cursor.execute("DELETE FROM content_library WHERE content_id = %s", (content_id,))
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Content deleted successfully",
            "posts_updated": result['post_count']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error deleting content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete content: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@router.get("/platforms/guidelines")
async def get_all_platform_guidelines():
    """Get content guidelines for all platforms"""
    
    platforms = ["instagram", "facebook", "linkedin", "twitter", "pinterest", "youtube"]
    
    return {
        "success": True,
        "data": {platform: get_platform_guidelines(platform) for platform in platforms}
    }

@router.post("/analyze-visual")
async def analyze_visual(
    image_base64: str = Body(...),
    platform: str = Body("instagram"),
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Analyze visual content using Google Cloud Vision API
    BRD REQUIREMENT: Visual Analysis (CV for composition, contrast, face detection)
    Supports both service account (Python library) and API key (REST API)
    """
    
    if not vision_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Cloud Vision API is not available. Please configure GOOGLE_VISION_API_KEY or GOOGLE_APPLICATION_CREDENTIALS"
        )
    
    try:
        print("[Google Vision] Starting image analysis...")
        
        # METHOD 1: Use REST API (when using API key)
        if use_rest_api:
            api_key = os.getenv('GOOGLE_VISION_API_KEY') or settings.GOOGLE_VISION_API_KEY
            vision_url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
            
            request_payload = {
                "requests": [
                    {
                        "image": {"content": image_base64},
                        "features": [
                            {"type": "LABEL_DETECTION", "maxResults": 10},
                            {"type": "FACE_DETECTION", "maxResults": 10},
                            {"type": "IMAGE_PROPERTIES"},
                            {"type": "TEXT_DETECTION"},
                            {"type": "SAFE_SEARCH_DETECTION"}
                        ]
                    }
                ]
            }
            
            response = requests.post(vision_url, json=request_payload)
            
            if response.status_code != 200:
                print(f"[Google Vision] API Error: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Google Vision API error: {response.text}"
                )
            
            result = response.json()
            vision_response = result["responses"][0]
            
            # Extract data from REST API response
            labels = [label["description"] for label in vision_response.get("labelAnnotations", [])[:10]]
            
            faces_detected = len(vision_response.get("faceAnnotations", []))
            face_emotions = []
            for face in vision_response.get("faceAnnotations", []):
                face_emotions.append({
                    "joy": face.get("joyLikelihood", "UNKNOWN"),
                    "sorrow": face.get("sorrowLikelihood", "UNKNOWN"),
                    "anger": face.get("angerLikelihood", "UNKNOWN"),
                    "surprise": face.get("surpriseLikelihood", "UNKNOWN")
                })
            
            dominant_colors = []
            if "imagePropertiesAnnotation" in vision_response:
                color_info = vision_response["imagePropertiesAnnotation"].get("dominantColors", {})
                for color in color_info.get("colors", [])[:5]:
                    rgb = color.get("color", {})
                    r = int(rgb.get("red", 0))
                    g = int(rgb.get("green", 0))
                    b = int(rgb.get("blue", 0))
                    dominant_colors.append({
                        "rgb": f"rgb({r}, {g}, {b})",
                        "hex": f"#{r:02x}{g:02x}{b:02x}",
                        "score": round(color.get("score", 0), 2),
                        "pixel_fraction": round(color.get("pixelFraction", 0), 3)
                    })
            
            text_detected = ""
            if "textAnnotations" in vision_response and vision_response["textAnnotations"]:
                text_detected = vision_response["textAnnotations"][0].get("description", "")[:100]
            
            safe_search = vision_response.get("safeSearchAnnotation", {})
            
        # METHOD 2: Use Python library (when using service account)
        else:
            from google.cloud import vision
            
            image_content = base64.b64decode(image_base64)
            image = vision.Image(content=image_content)
            
            # Label Detection
            response_labels = vision_client.label_detection(image=image)
            labels = [label.description for label in response_labels.label_annotations[:10]]
            
            # Face Detection
            response_faces = vision_client.face_detection(image=image)
            faces_detected = len(response_faces.face_annotations)
            face_emotions = []
            for face in response_faces.face_annotations:
                face_emotions.append({
                    "joy": face.joy_likelihood.name,
                    "sorrow": face.sorrow_likelihood.name,
                    "anger": face.anger_likelihood.name,
                    "surprise": face.surprise_likelihood.name
                })
            
            # Image Properties (colors)
            response_props = vision_client.image_properties(image=image)
            dominant_colors = []
            if response_props.image_properties_annotation.dominant_colors.colors:
                for color in response_props.image_properties_annotation.dominant_colors.colors[:5]:
                    r = int(color.color.red)
                    g = int(color.color.green)
                    b = int(color.color.blue)
                    dominant_colors.append({
                        "rgb": f"rgb({r}, {g}, {b})",
                        "hex": f"#{r:02x}{g:02x}{b:02x}",
                        "score": round(color.score, 2),
                        "pixel_fraction": round(color.pixel_fraction, 3)
                    })
            
            # Text Detection
            response_text = vision_client.text_detection(image=image)
            text_detected = ""
            if response_text.text_annotations:
                text_detected = response_text.text_annotations[0].description[:100]
            
            # Safe Search
            response_safe = vision_client.safe_search_detection(image=image)
            safe_search = response_safe.safe_search_annotation
        
        # Calculate composition score (same for both methods)
        composition_score = 50.0
        
        if faces_detected > 0:
            composition_score += min(faces_detected * 10, 20)
        
        if len(dominant_colors) >= 3:
            composition_score += 15
        elif len(dominant_colors) >= 2:
            composition_score += 10
        
        if len(labels) >= 5:
            composition_score += 15
        elif len(labels) >= 3:
            composition_score += 10
        
        composition_score = min(composition_score, 100)
        
        # Generate recommendations
        recommendations = []
        if composition_score < 70:
            if faces_detected == 0:
                recommendations.append("Consider adding human elements or faces to increase engagement (+15% engagement)")
            if len(dominant_colors) < 3:
                recommendations.append("Use more color variety to make the image pop (+10% visual appeal)")
            if not text_detected:
                recommendations.append("Add text overlay to communicate your message clearly (+20% message retention)")
        else:
            recommendations.append("Great composition! Image is optimized for social media")
        
        print(f"[Google Vision] Analysis complete. Score: {composition_score}")
        
        return {
            "success": True,
            "data": {
                "composition_score": round(composition_score, 1),
                "face_detected": faces_detected > 0,
                "faces_count": faces_detected,
                "face_emotions": face_emotions,
                "labels": labels,
                "dominant_colors": dominant_colors,
                "text_detected": text_detected,
                "recommendations": recommendations,
                "visual_analysis_status": "Optimized" if composition_score >= 70 else "Needs Improvement",
                "safe_search": {
                    "adult": safe_search.get("adult", "UNKNOWN") if use_rest_api else safe_search.adult.name,
                    "violence": safe_search.get("violence", "UNKNOWN") if use_rest_api else safe_search.violence.name,
                    "racy": safe_search.get("racy", "UNKNOWN") if use_rest_api else safe_search.racy.name
                } if safe_search else None
            }
        }
        
    except Exception as e:
        print(f"[Google Vision] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Visual analysis failed: {str(e)}"
        )

# Add this new endpoint for audience insights  
@router.post("/audience-insights")
async def get_audience_insights_endpoint(
    client_id: int = Body(...),
    topic: str = Body(...),
    platform: str = Body("instagram"),
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get AI-generated audience insights and keywords
    BRD REQUIREMENT: AI generate target audience & keywords based on client profile
    """
    try:
        insights = await generate_audience_and_keywords(
            client_id=client_id,
            topic=topic,
            platform=platform
        )
        
        return {
            "success": True,
            "data": insights
        }
        
    except Exception as e:
        print(f"Error generating audience insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
