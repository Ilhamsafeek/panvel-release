"""
Content Intelligence Hub API - Module 5 (COMPLETE)
File: app/api/v1/endpoints/content.py

IMPLEMENTS ALL BRD REQUIREMENTS:
1. AI-powered content generation
2. Performance Score 1-100 scale (≥70 = Optimized)  
3. AI-generated target audience & keywords
4. Platform-specific optimization
5. Hashtag & CTA optimization
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import pymysql
import json
import re
from openai import OpenAI

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


class ContentGenerateWithAIRequest(BaseModel):
    """Request for AI-powered content with auto-generated audience & keywords"""
    platform: str
    content_type: str
    topic: str
    tone: Optional[str] = "professional"
    client_id: Optional[int] = None
    auto_generate_audience: bool = True
    auto_generate_keywords: bool = True
    industry: Optional[str] = None


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
    status: Optional[str] = None


class ContentAnalyzeRequest(BaseModel):
    """Request to analyze content and get performance score"""
    content_text: str
    platform: str
    target_audience: Optional[str] = None
    keywords: Optional[List[str]] = None


class AudienceKeywordGenerateRequest(BaseModel):
    """Request to generate target audience and keywords from client profile"""
    client_id: int
    topic: Optional[str] = None
    platform: Optional[str] = None


# ========== PLATFORM GUIDELINES ==========

def get_platform_guidelines(platform: str) -> Dict[str, Any]:
    """Get platform-specific content guidelines"""
    guidelines = {
        "instagram": {
            "max_chars": 2200,
            "optimal_chars": 150,
            "hashtag_limit": 30,
            "optimal_hashtags": "5-10",
            "best_practices": [
                "Start with a hook in the first line",
                "Use line breaks for readability",
                "Include a clear call-to-action",
                "Mix popular and niche hashtags",
                "Use emojis strategically"
            ]
        },
        "facebook": {
            "max_chars": 63206,
            "optimal_chars": 80,
            "hashtag_limit": 10,
            "optimal_hashtags": "2-3",
            "best_practices": [
                "Keep posts concise and engaging",
                "Ask questions to drive engagement",
                "Use visuals whenever possible",
                "Include links strategically",
                "Post at optimal times"
            ]
        },
        "linkedin": {
            "max_chars": 3000,
            "optimal_chars": 150,
            "hashtag_limit": 5,
            "optimal_hashtags": "3-5",
            "best_practices": [
                "Lead with value or insight",
                "Use professional tone",
                "Share industry knowledge",
                "Include relevant statistics",
                "Engage with comments"
            ]
        },
        "twitter": {
            "max_chars": 280,
            "optimal_chars": 240,
            "hashtag_limit": 2,
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
        }
    }
    
    return guidelines.get(platform.lower(), {
        "max_chars": 2000,
        "optimal_chars": 200,
        "hashtag_limit": 10,
        "optimal_hashtags": "3-5",
        "best_practices": []
    })


# ========== AI-POWERED TARGET AUDIENCE & KEYWORDS GENERATION ==========

async def generate_audience_and_keywords(
    client_id: int,
    topic: str,
    platform: str,
    industry: Optional[str] = None
) -> Dict[str, Any]:
    """
    AI-powered generation of target audience and keywords based on client profile
    This is a KEY BRD requirement
    """
    connection = None
    cursor = None
    
    try:
        # Get client profile data
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT u.full_name, u.email,
                   c.company_name, c.industry, c.target_audience as existing_audience,
                   c.website_url, c.business_type
            FROM users u
            LEFT JOIN clients c ON u.user_id = c.client_id
            WHERE u.user_id = %s
        """, (client_id,))
        
        client_data = cursor.fetchone()
        
        # Get client's previous content for context
        cursor.execute("""
            SELECT content_text, platform, hashtags 
            FROM content_library 
            WHERE client_id = %s 
            ORDER BY created_at DESC 
            LIMIT 5
        """, (client_id,))
        
        previous_content = cursor.fetchall()
        
        # Build context for AI
        client_context = ""
        if client_data:
            client_context = f"""
Client Profile:
- Company: {client_data.get('company_name', 'N/A')}
- Industry: {client_data.get('industry', industry or 'General')}
- Business Type: {client_data.get('business_type', 'N/A')}
- Existing Target Audience: {client_data.get('existing_audience', 'Not specified')}
"""
        
        previous_context = ""
        if previous_content:
            previous_context = "\nPrevious Content Topics:\n"
            for pc in previous_content[:3]:
                previous_context += f"- {pc.get('content_text', '')[:100]}...\n"
        
        if not openai_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service not available"
            )
        
        prompt = f"""Based on the following client profile and content topic, generate comprehensive target audience and keywords for {platform} content.

{client_context}
{previous_context}

Content Topic: {topic}
Platform: {platform}
Industry: {industry or client_data.get('industry', 'General') if client_data else 'General'}

Generate a detailed JSON response with:
{{
    "target_audience": {{
        "primary_demographic": {{
            "age_range": "25-45",
            "gender": "All/Male/Female",
            "location": "Geographic focus",
            "income_level": "Income bracket",
            "education": "Education level"
        }},
        "psychographics": {{
            "interests": ["interest1", "interest2", "interest3"],
            "values": ["value1", "value2"],
            "pain_points": ["pain1", "pain2"],
            "goals": ["goal1", "goal2"]
        }},
        "behavior_patterns": {{
            "online_behavior": ["behavior1", "behavior2"],
            "purchasing_behavior": ["pattern1", "pattern2"],
            "content_preferences": ["preference1", "preference2"]
        }},
        "audience_personas": [
            {{
                "name": "Persona Name",
                "description": "Brief description",
                "key_motivators": ["motivator1", "motivator2"]
            }}
        ]
    }},
    "keywords": {{
        "primary_keywords": ["keyword1", "keyword2", "keyword3"],
        "secondary_keywords": ["keyword4", "keyword5", "keyword6"],
        "long_tail_keywords": ["long tail 1", "long tail 2"],
        "trending_keywords": ["trending1", "trending2"],
        "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5"]
    }},
    "content_recommendations": {{
        "optimal_posting_times": ["9:00 AM", "12:00 PM", "6:00 PM"],
        "content_formats": ["format1", "format2"],
        "tone_suggestions": ["suggestion1", "suggestion2"],
        "cta_recommendations": ["CTA1", "CTA2"]
    }}
}}

Return ONLY valid JSON."""

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert digital marketing strategist specializing in audience targeting and keyword research."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                raise ValueError("No JSON found in response")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Audience/Keyword generation error: {e}")
        # Return default structure
        return {
            "target_audience": {
                "primary_demographic": {
                    "age_range": "25-55",
                    "gender": "All",
                    "location": "India"
                },
                "psychographics": {
                    "interests": ["Digital Marketing", "Business Growth"],
                    "values": ["Quality", "Innovation"],
                    "pain_points": ["Time Management", "ROI Tracking"],
                    "goals": ["Increase Revenue", "Brand Awareness"]
                }
            },
            "keywords": {
                "primary_keywords": [topic],
                "secondary_keywords": [],
                "hashtags": []
            }
        }
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== PERFORMANCE SCORE CALCULATION (1-100) ==========

async def calculate_performance_score(
    content_text: str,
    platform: str,
    target_audience: Optional[str] = None,
    keywords: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Calculate content performance score (1-100)
    Score ≥70 = Optimized (BRD requirement)
    """
    try:
        if not openai_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service not available"
            )
        
        guidelines = get_platform_guidelines(platform)
        
        prompt = f"""Analyze this {platform} content and provide a detailed performance score.

Content: "{content_text}"

Platform: {platform}
Platform Guidelines:
- Optimal Length: {guidelines['optimal_chars']} characters
- Max Hashtags: {guidelines['hashtag_limit']}
- Current Length: {len(content_text)} characters

Target Audience: {target_audience or 'General'}
Keywords to Include: {', '.join(keywords) if keywords else 'None specified'}

Provide a comprehensive JSON analysis:
{{
    "overall_score": <1-100>,
    "optimization_status": "<Optimized/Needs Improvement/Poor>",
    "breakdown": {{
        "engagement_potential": <1-100>,
        "readability": <1-100>,
        "platform_fit": <1-100>,
        "keyword_optimization": <1-100>,
        "cta_effectiveness": <1-100>,
        "emotional_appeal": <1-100>
    }},
    "sentiment": "<positive/neutral/negative>",
    "strengths": ["strength1", "strength2", "strength3"],
    "improvements": [
        {{
            "issue": "Issue description",
            "suggestion": "How to fix it",
            "impact": "+X% estimated improvement"
        }}
    ],
    "predicted_metrics": {{
        "estimated_engagement_rate": "X%",
        "estimated_reach_multiplier": "Xv",
        "virality_potential": "<low/medium/high>"
    }},
    "optimized_version": "Rewritten optimized version of the content"
}}

IMPORTANT: Score ≥70 means "Optimized", 50-69 means "Needs Improvement", <50 means "Poor"

Return ONLY valid JSON."""

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert content analyst specializing in social media optimization. Be strict but fair in scoring."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                raise ValueError("No JSON found in response")
        
        # Ensure optimization status is set correctly based on score
        score = result.get('overall_score', 0)
        if score >= 70:
            result['optimization_status'] = "Optimized"
        elif score >= 50:
            result['optimization_status'] = "Needs Improvement"
        else:
            result['optimization_status'] = "Poor"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Performance score calculation error: {e}")
        return {
            "overall_score": 50,
            "optimization_status": "Needs Improvement",
            "breakdown": {},
            "strengths": [],
            "improvements": [{"issue": "Analysis failed", "suggestion": "Try again", "impact": "N/A"}]
        }


# ========== CONTENT GENERATION WITH AI ==========

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
            model=settings.OPENAI_MODEL if hasattr(settings, 'OPENAI_MODEL') else "gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert social media content creator specializing in platform-specific optimization."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = {"content": content, "headline": "", "cta": ""}
        
        return result
        
    except Exception as e:
        print(f"Content generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )


def generate_hashtags(
    platform: str,
    topic: str,
    keywords: List[str] = None,
    count: int = 10
) -> List[str]:
    """Generate platform-optimized hashtags"""
    
    if not openai_client:
        return []
    
    try:
        prompt = f"""Generate {count} optimized hashtags for {platform} about: {topic}
Keywords: {', '.join(keywords) if keywords else 'None'}

Return ONLY a JSON array of hashtags (with #):
["#hashtag1", "#hashtag2", ...]"""

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a hashtag optimization expert."},
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
            # Extract hashtags from text
            return re.findall(r'#\w+', content)[:count]
            
    except Exception as e:
        print(f"Hashtag generation error: {e}")
        return []


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
        
        # Generate hashtags
        hashtags = generate_hashtags(
            platform=request.platform,
            topic=request.topic,
            keywords=request.keywords
        )
        
        # Calculate performance score
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


@router.post("/generate-with-audience")
async def generate_content_with_auto_audience(
    request: ContentGenerateWithAIRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Generate content with AI-powered target audience & keywords
    BRD REQUIREMENT: Auto-generate audience and keywords from client profile
    """
    try:
        audience_keywords = None
        
        # Auto-generate audience and keywords if requested
        if request.auto_generate_audience or request.auto_generate_keywords:
            if request.client_id:
                audience_keywords = await generate_audience_and_keywords(
                    client_id=request.client_id,
                    topic=request.topic,
                    platform=request.platform,
                    industry=request.industry
                )
        
        # Extract keywords for content generation
        keywords = []
        target_audience_str = None
        
        if audience_keywords:
            kw_data = audience_keywords.get('keywords', {})
            keywords = kw_data.get('primary_keywords', []) + kw_data.get('secondary_keywords', [])[:3]
            
            aud_data = audience_keywords.get('target_audience', {})
            demo = aud_data.get('primary_demographic', {})
            target_audience_str = f"{demo.get('age_range', '25-45')}, {demo.get('location', 'India')}"
        
        # Generate content
        result = generate_ai_content(
            platform=request.platform,
            content_type=request.content_type,
            topic=request.topic,
            tone=request.tone,
            target_audience=target_audience_str,
            keywords=keywords[:5]  # Use top 5 keywords
        )
        
        # Generate hashtags from AI-suggested hashtags or generate new ones
        hashtags = []
        if audience_keywords:
            hashtags = audience_keywords.get('keywords', {}).get('hashtags', [])
        
        if len(hashtags) < 5:
            additional_hashtags = generate_hashtags(
                platform=request.platform,
                topic=request.topic,
                keywords=keywords
            )
            hashtags.extend(additional_hashtags)
            hashtags = list(set(hashtags))[:10]
        
        # Calculate performance score
        performance = await calculate_performance_score(
            content_text=result.get('content', ''),
            platform=request.platform,
            target_audience=target_audience_str,
            keywords=keywords
        )
        
        return {
            "success": True,
            "data": {
                **result,
                "hashtags": hashtags,
                "performance_score": performance.get('overall_score', 0),
                "optimization_status": performance.get('optimization_status', 'Unknown'),
                "performance_analysis": performance
            },
            "ai_generated_audience": audience_keywords.get('target_audience') if audience_keywords else None,
            "ai_generated_keywords": audience_keywords.get('keywords') if audience_keywords else None,
            "content_recommendations": audience_keywords.get('content_recommendations') if audience_keywords else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in generate_content_with_auto_audience: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/generate-audience-keywords")
async def generate_audience_keywords_endpoint(
    request: AudienceKeywordGenerateRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Generate target audience and keywords based on client profile
    BRD REQUIREMENT: AI generates target audience & keywords from client profile
    """
    try:
        result = await generate_audience_and_keywords(
            client_id=request.client_id,
            topic=request.topic or "General Marketing",
            platform=request.platform or "instagram",
            industry=None
        )
        
        return {
            "success": True,
            "client_id": request.client_id,
            "target_audience": result.get('target_audience', {}),
            "keywords": result.get('keywords', {}),
            "content_recommendations": result.get('content_recommendations', {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate audience and keywords: {str(e)}"
        )


@router.post("/analyze")
async def analyze_content(
    request: ContentAnalyzeRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Analyze content and return performance score (1-100)
    BRD REQUIREMENT: Performance Score 1-100 scale (≥70 = Optimized)
    """
    try:
        result = await calculate_performance_score(
            content_text=request.content_text,
            platform=request.platform,
            target_audience=request.target_audience,
            keywords=request.keywords
        )
        
        return {
            "success": True,
            "performance_score": result.get('overall_score', 0),
            "optimization_status": result.get('optimization_status', 'Unknown'),
            "is_optimized": result.get('overall_score', 0) >= 70,
            "analysis": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content analysis failed: {str(e)}"
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
        
        # Calculate performance score if not provided
        optimization_score = request.optimization_score
        if optimization_score is None:
            performance = await calculate_performance_score(
                content_text=request.content_text,
                platform=request.platform
            )
            optimization_score = performance.get('overall_score', 0)
        
        cursor.execute("""
            INSERT INTO content_library (
                client_id, created_by, platform, content_type,
                title, content_text, hashtags, cta_text,
                optimization_score, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.client_id,
            current_user['user_id'],
            request.platform,
            request.content_type,
            request.title,
            request.content_text,
            json.dumps(request.hashtags),
            request.cta_text,
            optimization_score,
            request.status
        ))
        
        connection.commit()
        content_id = cursor.lastrowid
        
        return {
            "success": True,
            "content_id": content_id,
            "message": "Content saved successfully",
            "optimization_score": optimization_score,
            "is_optimized": optimization_score >= 70
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save content: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/library/{client_id}")
async def get_content_library(
    client_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get content library for a client"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT c.*, u.full_name as creator_name
            FROM content_library c
            LEFT JOIN users u ON c.created_by = u.user_id
            WHERE c.client_id = %s
            ORDER BY c.created_at DESC
        """, (client_id,))
        
        content_list = cursor.fetchall()
        
        for item in content_list:
            if item.get('hashtags'):
                try:
                    item['hashtags'] = json.loads(item['hashtags'])
                except:
                    item['hashtags'] = []
            if item.get('created_at'):
                item['created_at'] = item['created_at'].isoformat()
            if item.get('updated_at'):
                item['updated_at'] = item['updated_at'].isoformat()
            
            # Add optimization status
            score = item.get('optimization_score', 0)
            item['is_optimized'] = score >= 70 if score else False
            item['optimization_status'] = "Optimized" if score >= 70 else "Needs Improvement" if score >= 50 else "Poor"
        
        return {
            "success": True,
            "content": content_list,
            "total": len(content_list)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch content library: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/{content_id}")
async def get_content(
    content_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get specific content item"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT c.*, u.full_name as creator_name
            FROM content_library c
            LEFT JOIN users u ON c.created_by = u.user_id
            WHERE c.content_id = %s
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
        
        if content.get('created_at'):
            content['created_at'] = content['created_at'].isoformat()
        
        # Add optimization status
        score = content.get('optimization_score', 0)
        content['is_optimized'] = score >= 70 if score else False
        content['optimization_status'] = "Optimized" if score >= 70 else "Needs Improvement" if score >= 50 else "Poor"
        
        return {
            "success": True,
            "content": content
        }
        
    except HTTPException:
        raise
    except Exception as e:
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
    """Update content item"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Build update query
        updates = []
        values = []
        
        if request.title is not None:
            updates.append("title = %s")
            values.append(request.title)
        
        if request.content_text is not None:
            updates.append("content_text = %s")
            values.append(request.content_text)
        
        if request.hashtags is not None:
            updates.append("hashtags = %s")
            values.append(json.dumps(request.hashtags))
        
        if request.cta_text is not None:
            updates.append("cta_text = %s")
            values.append(request.cta_text)
        
        if request.status is not None:
            updates.append("status = %s")
            values.append(request.status)
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        updates.append("updated_at = NOW()")
        values.append(content_id)
        
        query = f"UPDATE content_library SET {', '.join(updates)} WHERE content_id = %s"
        cursor.execute(query, values)
        connection.commit()
        
        # Recalculate performance score if content was updated
        if request.content_text:
            cursor.execute("SELECT platform FROM content_library WHERE content_id = %s", (content_id,))
            content = cursor.fetchone()
            if content:
                performance = await calculate_performance_score(
                    content_text=request.content_text,
                    platform=content['platform']
                )
                cursor.execute(
                    "UPDATE content_library SET optimization_score = %s WHERE content_id = %s",
                    (performance.get('overall_score', 0), content_id)
                )
                connection.commit()
        
        return {
            "success": True,
            "message": "Content updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
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
    """Delete content item"""
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM content_library WHERE content_id = %s", (content_id,))
        connection.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        return {
            "success": True,
            "message": "Content deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
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
    
    platforms = ["instagram", "facebook", "linkedin", "twitter", "pinterest"]
    guidelines = {}
    
    for platform in platforms:
        guidelines[platform] = get_platform_guidelines(platform)
    
    return {
        "success": True,
        "guidelines": guidelines
    }