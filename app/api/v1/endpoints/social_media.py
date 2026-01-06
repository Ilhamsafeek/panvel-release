"""
Social Media Command Center API - Module 6
File: app/api/v1/endpoints/social_media.py

Multi-platform scheduling with Module 5 & 8 integration + Real API Publishing
"""

import secrets
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi import Query, Request

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pymysql
import json
from openai import OpenAI
from typing import Optional
from urllib.parse import urlencode

from jose import jwt, JWTError
from urllib.parse import urlencode

import requests

from app.core.config import settings
from app.core.security import require_admin_or_employee, get_current_user
from app.core.security import get_db_connection
from app.services.social_media_service import SocialMediaService
from collections import defaultdict

router = APIRouter()

# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Initialize Social Media Service
social_media_service = SocialMediaService()


# ========== PYDANTIC MODELS ==========

class SocialMediaPostCreate(BaseModel):
    """Create social media post"""
    client_id: int
    content_id: Optional[int] = None  # Link to Module 5 content
    platform: str = Field(..., description="Platform: instagram, facebook, linkedin, twitter, pinterest")
    caption: str
    media_urls: List[str] = Field(default_factory=list)  # Media from Module 8
    hashtags: List[str] = Field(default_factory=list)
    scheduled_at: Optional[str] = None
    status: str = Field("draft", description="draft, scheduled, published")


class PostListResponse(BaseModel):
    post_id: int
    client_id: int
    client_name: str
    platform: str
    caption: str
    media_count: int
    hashtags: List[str]
    scheduled_at: Optional[str]
    published_at: Optional[str]
    status: str
    created_at: str


class BestTimeRequest(BaseModel):
    """Get AI-powered best posting times"""
    client_id: int
    platform: str


class BestTimeResponse(BaseModel):
    platform: str
    recommended_times: List[Dict[str, Any]]
    engagement_score: float


class MessageReplyRequest(BaseModel):
    message_id: int
    reply_text: str




# ========== A/B TESTING MODELS ==========
class ABTestCreate(BaseModel):
    """Create A/B test campaign"""
    client_id: int
    platform: str
    test_name: str
    test_type: str = "time"  # time, content, hashtags, combined
    
    # Variant A
    variant_a_caption: str
    variant_a_hashtags: List[str] = Field(default_factory=list)
    variant_a_media_urls: List[str] = Field(default_factory=list)
    variant_a_scheduled_at: Optional[str] = None
    
    # Variant B  
    variant_b_caption: str
    variant_b_hashtags: List[str] = Field(default_factory=list)
    variant_b_media_urls: List[str] = Field(default_factory=list)
    variant_b_scheduled_at: Optional[str] = None


# ========== CREATE POST ==========

@router.post("/posts", summary="Create social media post")
async def create_post(
    post: SocialMediaPostCreate,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Create social media post with integration to Module 5 (Content) and Module 8 (Media)
    Publishes immediately if status is 'published', schedules for later if 'scheduled'
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Verify client exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s AND role = 'client'", (post.client_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Client not found")
        
        # If content_id provided, fetch content from Module 5
        if post.content_id:
            cursor.execute("""
                SELECT content_text, hashtags, cta_text 
                FROM content_library 
                WHERE content_id = %s AND client_id = %s
            """, (post.content_id, post.client_id))
            content_data = cursor.fetchone()
            
            if content_data:
                if not post.caption and content_data.get('content_text'):
                    post.caption = content_data['content_text']
                
                if content_data.get('hashtags'):
                    try:
                        content_hashtags = json.loads(content_data['hashtags']) if isinstance(content_data['hashtags'], str) else content_data['hashtags']
                        if not post.hashtags and content_hashtags:
                            post.hashtags = content_hashtags
                    except:
                        pass
        
        # Convert scheduled_at to datetime if provided
        scheduled_datetime = None
        external_post_id = None
        
        if post.scheduled_at:
            try:
                scheduled_datetime = datetime.fromisoformat(post.scheduled_at.replace('Z', '+00:00'))
            except:
                raise HTTPException(status_code=400, detail="Invalid scheduled_at format. Use ISO format.")
        
        # If status is 'published', publish immediately to platform
        if post.status == 'published':
            publish_result = await publish_to_platform(
                platform=post.platform,
                client_id=post.client_id,
                caption=post.caption,
                media_urls=post.media_urls
            )
            
            if publish_result['success']:
                external_post_id = publish_result.get('post_id')
                post.status = 'published'
            else:
                # If publishing failed, save as draft
                post.status = 'draft'
                print(f"Publishing failed: {publish_result.get('error')}")
        
        # Insert post into database
        cursor.execute("""
            INSERT INTO social_media_posts 
            (client_id, content_id, created_by, platform, caption, media_urls, hashtags, 
             scheduled_at, status, external_post_id, published_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            post.client_id,
            post.content_id,
            current_user['user_id'],
            post.platform,
            post.caption,
            json.dumps(post.media_urls),
            json.dumps(post.hashtags),
            scheduled_datetime,
            post.status,
            external_post_id,
            datetime.now() if post.status == 'published' else None
        ))
        
        connection.commit()
        post_id = cursor.lastrowid
        
        return {
            "success": True,
            "message": "Social media post created successfully",
            "post_id": post_id,
            "status": post.status,
            "scheduled_at": post.scheduled_at,
            "external_post_id": external_post_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== LIST POSTS ==========

@router.get("/posts", summary="Get all social media posts")
async def list_posts(
    client_id: Optional[int] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    List social media posts with filters
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                smp.post_id,
                smp.client_id,
                u.full_name as client_name,
                smp.platform,
                smp.caption,
                smp.media_urls,
                smp.hashtags,
                smp.scheduled_at,
                smp.published_at,
                smp.status,
                smp.created_at
            FROM social_media_posts smp
            JOIN users u ON smp.client_id = u.user_id
            WHERE 1=1
        """
        params = []
        
        if client_id:
            query += " AND smp.client_id = %s"
            params.append(client_id)
        
        if platform:
            query += " AND smp.platform = %s"
            params.append(platform)
        
        if status:
            query += " AND smp.status = %s"
            params.append(status)
        
        query += " ORDER BY smp.created_at DESC"
        
        cursor.execute(query, params)
        posts = cursor.fetchall()
        
        # Format response
        posts_list = []
        for post in posts:
            try:
                media_urls = json.loads(post['media_urls']) if post.get('media_urls') else []
                hashtags = json.loads(post['hashtags']) if post.get('hashtags') else []
            except:
                media_urls = []
                hashtags = []
            
            posts_list.append({
                "post_id": post['post_id'],
                "client_id": post['client_id'],
                "client_name": post['client_name'],
                "platform": post['platform'],
                "caption": post['caption'] or "",
                "media_count": len(media_urls),
                "hashtags": hashtags,
                "scheduled_at": post['scheduled_at'].isoformat() if post.get('scheduled_at') else None,
                "published_at": post['published_at'].isoformat() if post.get('published_at') else None,
                "status": post['status'],
                "created_at": post['created_at'].isoformat()
            })
        
        return {
            "success": True,
            "posts": posts_list,
            "total": len(posts_list)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== GET SINGLE POST ==========

@router.get("/posts/{post_id}", summary="Get single post details")
async def get_post(
    post_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get detailed information about a specific post"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT 
                smp.*,
                u.full_name as client_name,
                u.email as client_email
            FROM social_media_posts smp
            JOIN users u ON smp.client_id = u.user_id
            WHERE smp.post_id = %s
        """, (post_id,))
        
        post = cursor.fetchone()
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Parse JSON fields
        try:
            post['media_urls'] = json.loads(post['media_urls']) if post.get('media_urls') else []
            post['hashtags'] = json.loads(post['hashtags']) if post.get('hashtags') else []
        except:
            post['media_urls'] = []
            post['hashtags'] = []
        
        # Convert datetime fields
        if post.get('scheduled_at'):
            post['scheduled_at'] = post['scheduled_at'].isoformat()
        if post.get('published_at'):
            post['published_at'] = post['published_at'].isoformat()
        if post.get('created_at'):
            post['created_at'] = post['created_at'].isoformat()
        
        return {
            "success": True,
            "post": post
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== UPDATE POST ==========

@router.put("/posts/{post_id}", summary="Update social media post")
async def update_post(
    post_id: int,
    post: SocialMediaPostCreate,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Update an existing social media post"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Check if post exists
        cursor.execute("SELECT post_id FROM social_media_posts WHERE post_id = %s", (post_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Convert scheduled_at
        scheduled_datetime = None
        if post.scheduled_at:
            try:
                scheduled_datetime = datetime.fromisoformat(post.scheduled_at.replace('Z', '+00:00'))
            except:
                raise HTTPException(status_code=400, detail="Invalid scheduled_at format")
        
        # Update post
        cursor.execute("""
            UPDATE social_media_posts 
            SET platform = %s, caption = %s, media_urls = %s, hashtags = %s, 
                scheduled_at = %s, status = %s
            WHERE post_id = %s
        """, (
            post.platform,
            post.caption,
            json.dumps(post.media_urls),
            json.dumps(post.hashtags),
            scheduled_datetime,
            post.status,
            post_id
        ))
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Post updated successfully",
            "post_id": post_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== DELETE POST ==========

@router.delete("/posts/{post_id}", summary="Delete social media post")
async def delete_post(
    post_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Delete a social media post"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM social_media_posts WHERE post_id = %s", (post_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Post not found")
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Post deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



# ========== PUBLISH EXISTING POST ==========
@router.post("/posts/{post_id}/publish", summary="Publish post to social media")
async def publish_post(
    post_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Publish a post immediately to the connected social media platform"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get post details
        cursor.execute("""
            SELECT 
                p.*,
                u.full_name as client_name
            FROM social_media_posts p
            JOIN users u ON p.client_id = u.user_id
            WHERE p.post_id = %s
        """, (post_id,))
        
        post = cursor.fetchone()
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        print(f" Publishing post {post_id} to {post['platform']} for client {post['client_id']}")
        
        # ✅ FIXED: Get credentials from correct table
        cursor.execute("""
            SELECT 
                access_token,
                refresh_token,
                platform_account_id,
                platform_account_name
            FROM social_media_credentials
            WHERE client_id = %s 
            AND platform = %s 
            AND is_active = TRUE
            LIMIT 1
        """, (post['client_id'], post['platform']))
        
        credentials = cursor.fetchone()
        
        if not credentials:
            print(f"❌ No credentials found for client {post['client_id']}, platform {post['platform']}")
            raise HTTPException(
                status_code=400,
                detail=f"No {post['platform']} account connected for this client. Please connect account first."
            )
        
        print(f"✅ Credentials found for {post['platform']}: {credentials['platform_account_name']}")
        
        # Publish to platform
        access_token = credentials['access_token']
        platform = post['platform']
        caption = post['caption']
        media_urls = json.loads(post['media_urls']) if post['media_urls'] else []
        
        # Call platform API to publish
        published = await publish_to_platform(
            platform=platform,
            access_token=access_token,
            caption=caption,
            media_urls=media_urls,
            platform_account_id=credentials['platform_account_id']
        )
        
        if published:
            # Update post status
            cursor.execute("""
                UPDATE social_media_posts
                SET status = 'published',
                    published_at = NOW()
                WHERE post_id = %s
            """, (post_id,))
            
            connection.commit()
            
            print(f"✅ Post {post_id} published successfully to {platform}")
            
            return {
                "success": True,
                "message": f"Post published successfully to {platform}!",
                "post_id": post_id,
                "platform": platform
            }
        else:
            raise Exception("Failed to publish to platform")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error publishing post: {str(e)}")
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to publish post: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



async def publish_to_platform(
    platform: str,
    access_token: str,
    caption: str,
    media_urls: list,
    platform_account_id: str
) -> bool:
    """
    Publish content to social media platform
    Supports: LinkedIn, Facebook, Instagram, Twitter, Pinterest
    """
    import requests
    import json
    
    try:
        print(f" Publishing to {platform}")
        print(f"   Account ID: {platform_account_id}")
        print(f"   Caption length: {len(caption)}")
        print(f"   Media count: {len(media_urls)}")
        
        # ==================== LINKEDIN ====================
        if platform == 'linkedin':
            # ✅ Ensure proper URN format
            if not platform_account_id.startswith('urn:li:'):
                platform_account_id = f"urn:li:person:{platform_account_id}"
            
            print(f"🔍 LinkedIn author URN: {platform_account_id}")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            # Build payload based on media
            if media_urls and len(media_urls) > 0:
                # Post with images
                payload = {
                    "author": platform_account_id,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {
                                "text": caption
                            },
                            "shareMediaCategory": "IMAGE",
                            "media": [
                                {
                                    "status": "READY",
                                    "description": {
                                        "text": caption[:200]
                                    },
                                    "media": url,
                                    "title": {
                                        "text": "Shared Image"
                                    }
                                } for url in media_urls[:9]  # LinkedIn max 9 images
                            ]
                        }
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                    }
                }
            else:
                # Text-only post
                payload = {
                    "author": platform_account_id,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {
                                "text": caption
                            },
                            "shareMediaCategory": "NONE"
                        }
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                    }
                }
            
            print(f" LinkedIn payload (truncated): {json.dumps(payload, indent=2)[:300]}...")
            
            response = requests.post(
                'https://api.linkedin.com/v2/ugcPosts',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"📥 LinkedIn response: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ LinkedIn post created: {result.get('id', 'N/A')}")
                return True
            else:
                print(f"❌ LinkedIn API error: {response.text}")
                return False
        
        # ==================== FACEBOOK ====================
        elif platform == 'facebook':
            print(f" Publishing to Facebook Page ID: {platform_account_id}")
            
            url = f"https://graph.facebook.com/v18.0/{platform_account_id}/feed"
            
            data = {
                'message': caption,
                'access_token': access_token
            }
            
            # Add media if provided
            if media_urls and len(media_urls) > 0:
                # For single image
                if len(media_urls) == 1:
                    data['link'] = media_urls[0]
                else:
                    # For multiple images, use photos endpoint
                    url = f"https://graph.facebook.com/v18.0/{platform_account_id}/photos"
                    data['url'] = media_urls[0]
                    data['caption'] = caption
            
            response = requests.post(url, data=data, timeout=30)
            
            print(f"📥 Facebook response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Facebook post created: {result.get('id', 'N/A')}")
                return True
            else:
                print(f"❌ Facebook API error: {response.text}")
                return False
        
        # ==================== INSTAGRAM ====================
        elif platform == 'instagram':
            print(f" Publishing to Instagram Account: {platform_account_id}")
            
            # Instagram requires at least one image
            if not media_urls or len(media_urls) == 0:
                print("❌ Instagram requires at least one image")
                return False
            
            # Step 1: Create media container
            container_url = f"https://graph.facebook.com/v18.0/{platform_account_id}/media"
            
            container_data = {
                'image_url': media_urls[0],
                'caption': caption,
                'access_token': access_token
            }
            
            container_response = requests.post(container_url, data=container_data, timeout=30)
            
            if container_response.status_code != 200:
                print(f"❌ Instagram container creation failed: {container_response.text}")
                return False
            
            creation_id = container_response.json().get('id')
            print(f"✅ Instagram container created: {creation_id}")
            
            # Step 2: Publish the container
            publish_url = f"https://graph.facebook.com/v18.0/{platform_account_id}/media_publish"
            publish_data = {
                'creation_id': creation_id,
                'access_token': access_token
            }
            
            publish_response = requests.post(publish_url, data=publish_data, timeout=30)
            
            print(f"📥 Instagram publish response: {publish_response.status_code}")
            
            if publish_response.status_code == 200:
                result = publish_response.json()
                print(f"✅ Instagram post published: {result.get('id', 'N/A')}")
                return True
            else:
                print(f"❌ Instagram publish failed: {publish_response.text}")
                return False
        
        # ==================== TWITTER/X ====================
        elif platform == 'twitter':
            print(f" Publishing to Twitter/X")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'text': caption[:280]  # Twitter character limit
            }
            
            # Note: Twitter API v2 media upload is complex and requires separate endpoint
            # For now, text-only posts
            if media_urls and len(media_urls) > 0:
                print("⚠️ Twitter media upload requires additional implementation")
            
            response = requests.post(
                'https://api.twitter.com/2/tweets',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"📥 Twitter response: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                tweet_id = result.get('data', {}).get('id', 'N/A')
                print(f"✅ Twitter post created: {tweet_id}")
                return True
            else:
                print(f"❌ Twitter API error: {response.text}")
                return False
        
        # ==================== PINTEREST ====================
        elif platform == 'pinterest':
            print(f" Publishing to Pinterest")
            
            # Pinterest requires at least one image
            if not media_urls or len(media_urls) == 0:
                print("❌ Pinterest requires at least one image")
                return False
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get user's boards first (simplified - using default board)
            boards_response = requests.get(
                'https://api.pinterest.com/v5/boards',
                headers=headers,
                timeout=30
            )
            
            if boards_response.status_code != 200:
                print(f"❌ Failed to get Pinterest boards: {boards_response.text}")
                return False
            
            boards = boards_response.json().get('items', [])
            
            if not boards:
                print("❌ No Pinterest boards found")
                return False
            
            board_id = boards[0]['id']  # Use first board
            print(f"📌 Using Pinterest board: {boards[0]['name']} ({board_id})")
            
            # Create pin
            payload = {
                'board_id': board_id,
                'media_source': {
                    'source_type': 'image_url',
                    'url': media_urls[0]
                },
                'description': caption[:500]  # Pinterest description limit
            }
            
            response = requests.post(
                'https://api.pinterest.com/v5/pins',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"📥 Pinterest response: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ Pinterest pin created: {result.get('id', 'N/A')}")
                return True
            else:
                print(f"❌ Pinterest API error: {response.text}")
                return False
        
        # ==================== UNSUPPORTED PLATFORM ====================
        else:
            print(f"❌ Platform '{platform}' is not supported for publishing")
            return False
    
    except requests.exceptions.Timeout:
        print(f"❌ Timeout error publishing to {platform}")
        return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error publishing to {platform}: {str(e)}")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error publishing to {platform}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


# ========== ADD THIS ENDPOINT FOR CONTENT LIBRARY ==========
@router.get("/content-library/{client_id}", summary="Get content library for client")
async def get_content_library(
    client_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get content from Module 5 (Content Intelligence Hub) for a specific client
    This provides compatibility for the Social Media Command Center
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT 
                content_id,
                client_id,
                platform,
                content_type,
                title,
                content_text,
                hashtags,
                cta_text,
                optimization_score,
                status,
                created_at
            FROM content_library
            WHERE client_id = %s AND status IN ('draft', 'approved')
            ORDER BY created_at DESC
            LIMIT 50
        """, (client_id,))
        
        content = cursor.fetchall()
        
        # Parse JSON fields
        for item in content:
            if item.get('hashtags'):
                try:
                    item['hashtags'] = json.loads(item['hashtags']) if isinstance(item['hashtags'], str) else item['hashtags']
                except:
                    item['hashtags'] = []
            else:
                item['hashtags'] = []
            
            if item.get('created_at'):
                item['created_at'] = item['created_at'].isoformat()
        
        return {
            "success": True,
            "content": content,
            "count": len(content)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== ADD THIS ENDPOINT FOR MEDIA LIBRARY ==========
@router.get("/media-library/{client_id}", summary="Get media library for client")
async def get_media_library(
    client_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get media assets from Module 8 (Creative Media Studio) for a specific client
    This provides compatibility for the Social Media Command Center
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT 
                asset_id,
                client_id,
                asset_type,
                asset_name,
                file_url,
                thumbnail_url,
                created_at
            FROM media_assets
            WHERE client_id = %s
            ORDER BY created_at DESC
            LIMIT 100
        """, (client_id,))
        
        assets = cursor.fetchall()
        
        # Format dates
        for asset in assets:
            if asset.get('created_at'):
                asset['created_at'] = asset['created_at'].isoformat()
        
        return {
            "success": True,
            "assets": assets,
            "count": len(assets)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



# ========== AI BEST TIME RECOMMENDATIONS ==========
# ========== AI BEST TIME RECOMMENDATIONS (REAL DATA ANALYSIS) ==========
@router.post("/best-times", summary="Get AI-powered best posting times")
async def get_best_times(
    request: BestTimeRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    AI-powered best time recommendations based on REAL historical performance data
    Analyzes actual post engagement patterns to suggest optimal posting times
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Check if we have recent calculations (within last 7 days)
        cursor.execute("""
            SELECT day_of_week, hour_of_day, engagement_score
            FROM platform_best_times
            WHERE client_id = %s AND platform = %s
            AND last_calculated >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY engagement_score DESC
            LIMIT 10
        """, (request.client_id, request.platform))
        
        existing_times = cursor.fetchall()
        
        # If we have recent data, return it
        if existing_times and len(existing_times) >= 5:
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            recommendations = []
            
            # Primary recommendations (top 5)
            for i, time_data in enumerate(existing_times[:5]):
                recommendations.append({
                    "day": day_names[time_data['day_of_week']],
                    "hour": time_data['hour_of_day'],
                    "time_formatted": f"{time_data['hour_of_day']:02d}:00",
                    "engagement_score": float(time_data['engagement_score']),
                    "rank": i + 1,
                    "type": "primary"
                })
            
            # Alternative slots for A/B testing (next 3)
            for i, time_data in enumerate(existing_times[5:8]):
                recommendations.append({
                    "day": day_names[time_data['day_of_week']],
                    "hour": time_data['hour_of_day'],
                    "time_formatted": f"{time_data['hour_of_day']:02d}:00",
                    "engagement_score": float(time_data['engagement_score']),
                    "rank": i + 6,
                    "type": "alternative"
                })
            
            return {
                "success": True,
                "platform": request.platform,
                "recommended_times": recommendations,
                "data_source": "historical_analysis",
                "last_calculated": existing_times[0].get('last_calculated').isoformat() if existing_times[0].get('last_calculated') else None
            }
        
        # ========== CALCULATE NEW RECOMMENDATIONS FROM REAL DATA ==========
        print(f"[BEST TIMES] Calculating new recommendations for client {request.client_id}, platform {request.platform}")
        
        # Query historical published posts with analytics
        cursor.execute("""
            SELECT 
                p.post_id,
                p.published_at,
                DAYOFWEEK(p.published_at) - 1 as day_of_week,
                HOUR(p.published_at) as hour_of_day,
                a.impressions,
                a.reach,
                a.engagement_count,
                (a.engagement_count / GREATEST(a.reach, 1)) * 100 as engagement_rate
            FROM social_media_posts p
            LEFT JOIN social_media_analytics a ON (
                a.client_id = p.client_id 
                AND a.platform = p.platform
                AND a.metric_date = DATE(p.published_at)
            )
            WHERE p.client_id = %s 
            AND p.platform = %s
            AND p.status = 'published'
            AND p.published_at IS NOT NULL
            AND p.published_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
            ORDER BY p.published_at DESC
        """, (request.client_id, request.platform))
        
        posts = cursor.fetchall()
        
        if not posts or len(posts) < 5:
            # Not enough historical data - use AI-powered industry best practices
            print(f"[BEST TIMES] Insufficient historical data ({len(posts) if posts else 0} posts), using AI recommendations")
            
            prompt = f"""Based on industry best practices and social media research for {request.platform}, provide the top 8 optimal posting times for maximum engagement.

Consider factors like:
- Peak user activity hours
- Day of week patterns
- Platform-specific algorithms
- Typical audience behavior

Return ONLY a JSON array with this exact format:
[
  {{"day": 1, "hour": 9, "score": 85.5}},
  {{"day": 1, "hour": 12, "score": 82.3}}
]

Where day is 0-6 (Monday=0, Sunday=6) and hour is 0-23.
Provide exactly 8 time slots ranked by engagement potential (score 0-100)."""

            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if json_match:
                ai_times = json.loads(json_match.group())
            else:
                ai_times = json.loads(ai_response)
            
            # Store AI recommendations in database
            for time_slot in ai_times:
                cursor.execute("""
                    INSERT INTO platform_best_times 
                    (client_id, platform, day_of_week, hour_of_day, engagement_score, last_calculated)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE 
                    engagement_score = VALUES(engagement_score),
                    last_calculated = NOW()
                """, (
                    request.client_id,
                    request.platform,
                    time_slot['day'],
                    time_slot['hour'],
                    time_slot['score']
                ))
            
            connection.commit()
            
            # Format response
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            recommendations = []
            
            for i, time_slot in enumerate(ai_times[:5]):
                recommendations.append({
                    "day": day_names[time_slot['day']],
                    "hour": time_slot['hour'],
                    "time_formatted": f"{time_slot['hour']:02d}:00",
                    "engagement_score": float(time_slot['score']),
                    "rank": i + 1,
                    "type": "primary"
                })
            
            for i, time_slot in enumerate(ai_times[5:8]):
                recommendations.append({
                    "day": day_names[time_slot['day']],
                    "hour": time_slot['hour'],
                    "time_formatted": f"{time_slot['hour']:02d}:00",
                    "engagement_score": float(time_slot['score']),
                    "rank": i + 6,
                    "type": "alternative"
                })
            
            return {
                "success": True,
                "platform": request.platform,
                "recommended_times": recommendations,
                "data_source": "ai_industry_best_practices",
                "note": f"Using AI-powered recommendations. Only {len(posts) if posts else 0} historical posts found. Recommendations will improve with more data."
            }
        
        # ========== ANALYZE REAL HISTORICAL DATA ==========
        print(f"[BEST TIMES] Analyzing {len(posts)} historical posts")
        
        # Group by day/hour and calculate average engagement
        time_slots = defaultdict(lambda: {'total_engagement': 0, 'count': 0, 'total_rate': 0})
        
        for post in posts:
            if post['day_of_week'] is not None and post['hour_of_day'] is not None:
                key = (post['day_of_week'], post['hour_of_day'])
                engagement_rate = float(post['engagement_rate'] or 0)
                
                time_slots[key]['total_engagement'] += engagement_rate
                time_slots[key]['total_rate'] += engagement_rate
                time_slots[key]['count'] += 1
        
        # Calculate averages and scores
        scored_times = []
        for (day, hour), data in time_slots.items():
            if data['count'] > 0:
                avg_engagement_rate = data['total_rate'] / data['count']
                # Normalize score to 0-100 range
                score = min(avg_engagement_rate, 100.0)
                
                scored_times.append({
                    'day': day,
                    'hour': hour,
                    'score': score,
                    'post_count': data['count']
                })
        
        # Sort by score
        scored_times.sort(key=lambda x: x['score'], reverse=True)
        
        # If we still don't have enough data points
        if len(scored_times) < 5:
            # Fill with AI recommendations for missing time slots
            print(f"[BEST TIMES] Only {len(scored_times)} time slots found, supplementing with AI")
            
            # Use OpenAI to fill gaps
            prompt = f"""Based on industry best practices for {request.platform}, suggest 8 optimal posting times.
Return ONLY a JSON array: [{{"day": 1, "hour": 9, "score": 85.5}}]
Where day is 0-6 (Monday=0) and hour is 0-23."""
            
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            ai_response = response.choices[0].message.content.strip()
            import re
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if json_match:
                ai_times = json.loads(json_match.group())
                scored_times.extend([{'day': t['day'], 'hour': t['hour'], 'score': t['score'], 'post_count': 0} for t in ai_times])
            
            # Remove duplicates and resort
            seen = set()
            unique_times = []
            for t in scored_times:
                key = (t['day'], t['hour'])
                if key not in seen:
                    seen.add(key)
                    unique_times.append(t)
            scored_times = sorted(unique_times, key=lambda x: x['score'], reverse=True)
        
        # Take top 10 and store in database
        top_times = scored_times[:10]
        
        for time_slot in top_times:
            cursor.execute("""
                INSERT INTO platform_best_times 
                (client_id, platform, day_of_week, hour_of_day, engagement_score, last_calculated)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                engagement_score = VALUES(engagement_score),
                last_calculated = NOW()
            """, (
                request.client_id,
                request.platform,
                time_slot['day'],
                time_slot['hour'],
                time_slot['score']
            ))
        
        connection.commit()
        
        # Format response
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        recommendations = []
        
        # Primary recommendations (top 5)
        for i, time_slot in enumerate(top_times[:5]):
            recommendations.append({
                "day": day_names[time_slot['day']],
                "hour": time_slot['hour'],
                "time_formatted": f"{time_slot['hour']:02d}:00",
                "engagement_score": round(time_slot['score'], 2),
                "rank": i + 1,
                "type": "primary",
                "based_on_posts": time_slot['post_count']
            })
        
        # Alternative slots for A/B testing (next 3)
        for i, time_slot in enumerate(top_times[5:8]):
            recommendations.append({
                "day": day_names[time_slot['day']],
                "hour": time_slot['hour'],
                "time_formatted": f"{time_slot['hour']:02d}:00",
                "engagement_score": round(time_slot['score'], 2),
                "rank": i + 6,
                "type": "alternative",
                "based_on_posts": time_slot['post_count']
            })
        
        return {
            "success": True,
            "platform": request.platform,
            "recommended_times": recommendations,
            "data_source": "real_historical_analysis",
            "analyzed_posts": len(posts),
            "note": "Recommendations based on your actual post performance over the last 90 days"
        }
        
    except Exception as e:
        print(f"[BEST TIMES ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze best times: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== ADD ANALYTICS SUMMARY ENDPOINT ==========
@router.get("/analytics/summary", summary="Get analytics summary for all platforms")
async def get_analytics_summary(
    client_id: Optional[int] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get performance summaries for each platform
    Used by the Social Media Command Center dashboard
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Build query based on client filter
        query = """
            SELECT 
                platform,
                COUNT(*) as total_posts,
                SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published_posts,
                SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled_posts,
                SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as draft_posts
            FROM social_media_posts
        """
        params = []
        
        if client_id:
            query += " WHERE client_id = %s"
            params.append(client_id)
        
        query += " GROUP BY platform"
        
        cursor.execute(query, params)
        platform_stats = cursor.fetchall()
        
        # Get analytics data if available
        analytics_query = """
            SELECT 
                platform,
                SUM(followers_count) as followers,
                SUM(impressions) as impressions,
                SUM(reach) as reach,
                SUM(engagement_count) as engagement
            FROM social_media_analytics
        """
        
        if client_id:
            analytics_query += " WHERE client_id = %s"
        
        analytics_query += " GROUP BY platform"
        
        cursor.execute(analytics_query, params if client_id else [])
        analytics_data = cursor.fetchall()
        
        # Merge data
        analytics_map = {row['platform']: row for row in analytics_data}
        
        summaries = []
        for stat in platform_stats:
            platform = stat['platform']
            analytics = analytics_map.get(platform, {})
            
            summaries.append({
                "platform": platform,
                "total_posts": stat['total_posts'] or 0,
                "published_posts": stat['published_posts'] or 0,
                "scheduled_posts": stat['scheduled_posts'] or 0,
                "draft_posts": stat['draft_posts'] or 0,
                "followers": analytics.get('followers') or 0,
                "impressions": analytics.get('impressions') or 0,
                "reach": analytics.get('reach') or 0,
                "engagement": analytics.get('engagement') or 0
            })
        
        # If no data, return default structure for common platforms
        if not summaries:
            for platform in ['instagram', 'facebook', 'linkedin', 'twitter', 'pinterest']:
                summaries.append({
                    "platform": platform,
                    "total_posts": 0,
                    "published_posts": 0,
                    "scheduled_posts": 0,
                    "draft_posts": 0,
                    "followers": 0,
                    "impressions": 0,
                    "reach": 0,
                    "engagement": 0
                })
        
        return {
            "success": True,
            "summaries": summaries
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== GET CALENDAR DATA ==========

from fastapi import Query  # Add this import at the top if not present

@router.get("/calendar", summary="Get calendar view of posts")
async def get_calendar(
    client_id: Optional[int] = None,  # Made optional
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get calendar view of scheduled posts for a specific month.
    If client_id is not provided, returns posts for ALL clients.
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Default to current month
        if not month or not year:
            now = datetime.now()
            month = month or now.month
            year = year or now.year
        
        # Get first and last day of month
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Build query - client_id is now optional
        if client_id:
            cursor.execute("""
                SELECT 
                    smp.post_id,
                    smp.platform,
                    smp.caption,
                    smp.scheduled_at,
                    smp.status,
                    smp.media_urls,
                    u.full_name as client_name
                FROM social_media_posts smp
                JOIN users u ON smp.client_id = u.user_id
                WHERE smp.client_id = %s 
                AND smp.scheduled_at >= %s 
                AND smp.scheduled_at <= %s
                ORDER BY smp.scheduled_at ASC
            """, (client_id, first_day, last_day))
        else:
            # Get posts for ALL clients
            cursor.execute("""
                SELECT 
                    smp.post_id,
                    smp.platform,
                    smp.caption,
                    smp.scheduled_at,
                    smp.status,
                    smp.media_urls,
                    u.full_name as client_name
                FROM social_media_posts smp
                JOIN users u ON smp.client_id = u.user_id
                WHERE smp.scheduled_at >= %s 
                AND smp.scheduled_at <= %s
                ORDER BY smp.scheduled_at ASC
            """, (first_day, last_day))
        
        posts = cursor.fetchall()
        
        # Group by date
        calendar_data = {}
        for post in posts:
            if post['scheduled_at']:
                date_key = post['scheduled_at'].strftime('%Y-%m-%d')
                
                if date_key not in calendar_data:
                    calendar_data[date_key] = []
                
                try:
                    media_urls = json.loads(post['media_urls']) if post.get('media_urls') else []
                except:
                    media_urls = []
                
                calendar_data[date_key].append({
                    "post_id": post['post_id'],
                    "platform": post['platform'],
                    "caption": post['caption'][:100] if post.get('caption') else "",
                    "client_name": post.get('client_name', 'Unknown'),
                    "scheduled_at": post['scheduled_at'].isoformat(),
                    "status": post['status'],
                    "media_count": len(media_urls)
                })
        
        return {
            "success": True,
            "month": month,
            "year": year,
            "calendar": calendar_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@router.get("/stats", summary="Get post statistics")
async def get_stats(
    client_id: Optional[int] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get post statistics (total, scheduled, published, drafts)
    Optionally filter by client_id
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Build query
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled,
                SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published,
                SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as draft
            FROM social_media_posts
        """
        params = []
        
        if client_id:
            query += " WHERE client_id = %s"
            params.append(client_id)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        return {
            "success": True,
            "stats": {
                "total": result['total'] or 0,
                "scheduled": result['scheduled'] or 0,
                "published": result['published'] or 0,
                "draft": result['draft'] or 0
            }
        }
        
    except Exception as e:
        # Return zeros on error instead of failing
        return {
            "success": True,
            "stats": {
                "total": 0,
                "scheduled": 0,
                "published": 0,
                "draft": 0
            }
        }
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

            
# ========== PLATFORM ANALYTICS ==========

@router.get("/analytics/{client_id}", summary="Get platform-wise analytics")
async def get_analytics(
    client_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get platform-wise performance analytics"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get post counts by platform
        cursor.execute("""
            SELECT 
                platform,
                COUNT(*) as total_posts,
                SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published_posts,
                SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled_posts,
                SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as draft_posts
            FROM social_media_posts
            WHERE client_id = %s
            GROUP BY platform
        """, (client_id,))
        
        platform_stats = cursor.fetchall()
        
        # Get analytics data if available
        cursor.execute("""
            SELECT 
                platform,
                SUM(followers_count) as total_followers,
                SUM(impressions) as total_impressions,
                SUM(reach) as total_reach,
                SUM(engagement_count) as total_engagement
            FROM social_media_analytics
            WHERE client_id = %s
            GROUP BY platform
        """, (client_id,))
        
        analytics_data = cursor.fetchall()
        
        # Merge data
        analytics_map = {row['platform']: row for row in analytics_data}
        
        result = []
        for stat in platform_stats:
            platform = stat['platform']
            analytics = analytics_map.get(platform, {})
            
            result.append({
                "platform": platform,
                "total_posts": stat['total_posts'],
                "published_posts": stat['published_posts'],
                "scheduled_posts": stat['scheduled_posts'],
                "draft_posts": stat['draft_posts'],
                "followers": analytics.get('total_followers', 0),
                "impressions": analytics.get('total_impressions', 0),
                "reach": analytics.get('total_reach', 0),
                "engagement": analytics.get('total_engagement', 0)
            })
        
        return {
            "success": True,
            "analytics": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== TRENDING TOPICS ==========
@router.get("/trending", summary="Get trending topics from platforms")
async def get_trending_topics(
    platform: Optional[str] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get trending topics from social media platforms
    Uses AI to generate relevant trending topics when API data unavailable
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Check for stored trends (last 24 hours)
        query = """
            SELECT platform, topic, category, volume, detected_at
            FROM trending_topics
            WHERE detected_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """
        params = []
        
        if platform:
            query += " AND platform = %s"
            params.append(platform)
        
        query += " ORDER BY volume DESC LIMIT 20"
        
        cursor.execute(query, params)
        stored_trends = cursor.fetchall()
        
        if stored_trends and len(stored_trends) >= 5:
            # Format and return stored trends
            for trend in stored_trends:
                if trend.get('detected_at'):
                    trend['detected_at'] = trend['detected_at'].isoformat()
            
            return {
                "success": True,
                "topics": stored_trends,
                "source": "stored"
            }
        
        # Generate AI-based trending suggestions
        try:
            prompt = f"""Generate 6 current trending topics for social media marketing.
            {f'Focus on {platform} platform.' if platform else 'Include topics suitable for various platforms.'}
            
            Return as JSON array with format:
            [
                {{"topic": "Topic Name", "category": "Category", "platform": "platform_name", "volume": 50000}}
            ]
            
            Categories: Technology, Business, Marketing, Lifestyle, Entertainment, News
            Platforms: instagram, facebook, linkedin, twitter, pinterest
            Volume: estimated posts/engagement (10000-500000)
            
            Make topics relevant to digital marketing and business."""
            
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a social media trend analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON from response
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            trending = json.loads(content)
            
            # Store trends for future use
            for trend in trending:
                try:
                    cursor.execute("""
                        INSERT INTO trending_topics (platform, topic, category, volume, detected_at)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (
                        trend.get('platform', 'general'),
                        trend.get('topic', ''),
                        trend.get('category', 'General'),
                        trend.get('volume', 10000)
                    ))
                except:
                    pass
            
            connection.commit()
            
            return {
                "success": True,
                "topics": trending,
                "source": "ai_generated"
            }
            
        except Exception as ai_error:
            print(f"AI trending error: {ai_error}")
            
            # Return default trends
            default_trends = [
                {"topic": "#DigitalMarketing", "category": "Marketing", "platform": platform or "instagram", "volume": 125000},
                {"topic": "#ContentCreation", "category": "Marketing", "platform": platform or "instagram", "volume": 98000},
                {"topic": "#SocialMediaTips", "category": "Marketing", "platform": platform or "facebook", "volume": 87000},
                {"topic": "#BusinessGrowth", "category": "Business", "platform": platform or "linkedin", "volume": 76000},
                {"topic": "#MarketingStrategy", "category": "Marketing", "platform": platform or "twitter", "volume": 65000},
                {"topic": "#BrandBuilding", "category": "Business", "platform": platform or "instagram", "volume": 54000}
            ]
            
            return {
                "success": True,
                "topics": default_trends,
                "source": "default"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
# ========== PERFORMANCE SUMMARY ==========

@router.get("/performance-summary/{client_id}", summary="Get performance summary by platform")
async def get_performance_summary(
    client_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get small performance summaries for each platform
    Returns key metrics: engagement rate, reach, best performing post
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get performance data by platform
        cursor.execute("""
            SELECT 
                smp.platform,
                COUNT(DISTINCT smp.post_id) as total_published,
                COALESCE(SUM(sma.impressions), 0) as total_impressions,
                COALESCE(SUM(sma.reach), 0) as total_reach,
                COALESCE(SUM(sma.engagement_count), 0) as total_engagement,
                COALESCE(AVG(sma.followers_count), 0) as avg_followers
            FROM social_media_posts smp
            LEFT JOIN social_media_analytics sma ON smp.client_id = sma.client_id AND smp.platform = sma.platform
            WHERE smp.client_id = %s AND smp.status = 'published'
            GROUP BY smp.platform
        """, (client_id,))
        
        platform_data = cursor.fetchall()
        
        summaries = []
        
        for data in platform_data:
            platform = data['platform']
            total_published = data['total_published']
            total_impressions = data['total_impressions']
            total_reach = data['total_reach']
            total_engagement = data['total_engagement']
            avg_followers = data['avg_followers']
            
            # Calculate engagement rate
            engagement_rate = 0
            if total_impressions > 0:
                engagement_rate = (total_engagement / total_impressions) * 100
            elif avg_followers > 0:
                engagement_rate = (total_engagement / avg_followers) * 100
            
            # Get best performing post
            cursor.execute("""
                SELECT caption, scheduled_at
                FROM social_media_posts
                WHERE client_id = %s AND platform = %s AND status = 'published'
                ORDER BY created_at DESC
                LIMIT 1
            """, (client_id, platform))
            
            best_post = cursor.fetchone()
            
            # Generate AI insights
            insight = generate_platform_insight(platform, engagement_rate, total_published)
            
            summaries.append({
                "platform": platform,
                "metrics": {
                    "total_posts": total_published,
                    "impressions": int(total_impressions),
                    "reach": int(total_reach),
                    "engagement": int(total_engagement),
                    "engagement_rate": round(engagement_rate, 2),
                    "followers": int(avg_followers)
                },
                "best_post": {
                    "caption": best_post['caption'][:100] if best_post else "No posts yet",
                    "date": best_post['scheduled_at'].isoformat() if best_post and best_post['scheduled_at'] else None
                },
                "insight": insight,
                "status": "excellent" if engagement_rate > 5 else "good" if engagement_rate > 2 else "needs_improvement"
            })
        
        return {
            "success": True,
            "summaries": summaries
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def generate_platform_insight(platform: str, engagement_rate: float, total_posts: int) -> str:
    """Generate AI insight for platform performance"""
    
    if total_posts == 0:
        return f"Start posting on {platform} to build your presence."
    
    if engagement_rate > 5:
        return f"Excellent performance on {platform}! Your audience is highly engaged."
    elif engagement_rate > 2:
        return f"Good engagement on {platform}. Consider posting at peak times for better reach."
    elif engagement_rate > 0.5:
        return f"Moderate engagement. Try different content formats and posting times on {platform}."
    else:
        return f"Low engagement detected. Review your content strategy for {platform}."


# ========== SYNC ANALYTICS FROM PLATFORMS ==========

@router.post("/sync-analytics/{client_id}", summary="Sync analytics from social platforms")
async def sync_platform_analytics(
    client_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Sync real analytics data from social media platforms (Meta, LinkedIn)
    Fetches latest metrics and saves to database
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Verify client exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (client_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Client not found")
        
        results = {}
        
        # Sync Instagram analytics
        try:
            instagram_result = social_media_service.get_instagram_insights(
                instagram_account_id="placeholder_account_id"  # Get from client config
            )
            
            if instagram_result['success']:
                insights = instagram_result['insights']
                
                cursor.execute("""
                    INSERT INTO social_media_analytics 
                    (client_id, platform, metric_date, followers_count, impressions, reach, engagement_count)
                    VALUES (%s, %s, CURDATE(), %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    followers_count = VALUES(followers_count),
                    impressions = VALUES(impressions),
                    reach = VALUES(reach),
                    engagement_count = VALUES(engagement_count)
                """, (
                    client_id,
                    'instagram',
                    insights.get('follower_count', 0),
                    insights.get('impressions', 0),
                    insights.get('reach', 0),
                    insights.get('profile_views', 0)
                ))
                
                results['instagram'] = "synced"
        except Exception as e:
            results['instagram'] = f"error: {str(e)}"
        
        # Sync Facebook analytics
        try:
            facebook_result = social_media_service.get_facebook_page_insights(
                page_id="placeholder_page_id"  # Get from client config
            )
            
            if facebook_result['success']:
                insights = facebook_result['insights']
                
                cursor.execute("""
                    INSERT INTO social_media_analytics 
                    (client_id, platform, metric_date, followers_count, impressions, engagement_count)
                    VALUES (%s, %s, CURDATE(), %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    followers_count = VALUES(followers_count),
                    impressions = VALUES(impressions),
                    engagement_count = VALUES(engagement_count)
                """, (
                    client_id,
                    'facebook',
                    insights.get('page_fans', 0),
                    insights.get('page_impressions', 0),
                    insights.get('page_engaged_users', 0)
                ))
                
                results['facebook'] = "synced"
        except Exception as e:
            results['facebook'] = f"error: {str(e)}"
        
        # Sync LinkedIn analytics
        try:
            linkedin_result = social_media_service.get_linkedin_analytics(
                organization_urn="placeholder_org_urn"  # Get from client config
            )
            
            if linkedin_result['success']:
                analytics = linkedin_result['analytics']
                
                cursor.execute("""
                    INSERT INTO social_media_analytics 
                    (client_id, platform, metric_date, impressions, engagement_count)
                    VALUES (%s, %s, CURDATE(), %s, %s)
                    ON DUPLICATE KEY UPDATE
                    impressions = VALUES(impressions),
                    engagement_count = VALUES(engagement_count)
                """, (
                    client_id,
                    'linkedin',
                    analytics.get('impressions', 0),
                    analytics.get('likes', 0) + analytics.get('comments', 0) + analytics.get('shares', 0)
                ))
                
                results['linkedin'] = "synced"
        except Exception as e:
            results['linkedin'] = f"error: {str(e)}"
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Analytics synced from platforms",
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()




# ========== SOCIAL MEDIA ACCOUNT CONNECTION ENDPOINTS ==========

@router.get("/accounts/{client_id}", summary="Get connected social media accounts")
async def get_connected_accounts(
    client_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get all connected social media accounts for a client"""
    accounts = social_media_service.get_connected_accounts(client_id)
    
    return {
        "success": True,
        "accounts": accounts
    }


@router.post("/accounts/connect", summary="Connect social media account")
async def connect_social_account(
    client_id: int,
    platform: str,
    platform_account_id: str,
    platform_account_name: str,
    access_token: str,
    refresh_token: Optional[str] = None,
    expires_in: Optional[int] = None,  # seconds
    account_metadata: Optional[Dict] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Connect a social media account for a client
    This would typically be called after OAuth flow completion
    """
    token_expires_at = None
    if expires_in:
        token_expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    success = social_media_service.save_client_credentials(
        client_id=client_id,
        platform=platform,
        platform_account_id=platform_account_id,
        platform_account_name=platform_account_name,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=token_expires_at,
        account_metadata=account_metadata
    )
    
    if success:
        return {
            "success": True,
            "message": f"{platform.title()} account connected successfully"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save credentials")


@router.delete("/accounts/{account_id}", summary="Disconnect social media account")
async def disconnect_social_account(
    account_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Disconnect/deactivate a social media account"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE social_media_accounts
            SET is_active = FALSE
            WHERE account_id = %s
        """, (account_id,))
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Account disconnected successfully"
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()





# ========== OAUTH INTEGRATION (NO NEW FILES) ==========

# OAuth States (temporary storage)
oauth_states = {}

# OAuth Configuration
OAUTH_CONFIGS = {
    'facebook': {
        'authorize_url': 'https://www.facebook.com/v18.0/dialog/oauth',
        'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
        'scopes': ['pages_manage_posts', 'pages_read_engagement', 'pages_show_list'],
        'client_id': getattr(settings, 'FACEBOOK_APP_ID', ''),
        'client_secret': getattr(settings, 'FACEBOOK_APP_SECRET', ''),
    },
    'instagram': {
        'authorize_url': 'https://www.facebook.com/v18.0/dialog/oauth',
        'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
        'scopes': ['instagram_basic', 'instagram_content_publish', 'pages_read_engagement'],
        'client_id': getattr(settings, 'FACEBOOK_APP_ID', ''),
        'client_secret': getattr(settings, 'FACEBOOK_APP_SECRET', ''),
    },
    'linkedin': {
        'authorize_url': 'https://www.linkedin.com/oauth/v2/authorization',
        'token_url': 'https://www.linkedin.com/oauth/v2/accessToken',
        # ✅ FIXED: Add openid scope for userinfo endpoint
        'scopes': ['openid', 'profile', 'email', 'w_member_social'],
        'client_id': getattr(settings, 'LINKEDIN_CLIENT_ID', ''),
        'client_secret': getattr(settings, 'LINKEDIN_CLIENT_SECRET', ''),
    },
    'twitter': {
        'authorize_url': 'https://twitter.com/i/oauth2/authorize',
        'token_url': 'https://api.twitter.com/2/oauth2/token',
        'scopes': ['tweet.read', 'tweet.write', 'users.read', 'offline.access'],
        'client_id': getattr(settings, 'TWITTER_CLIENT_ID', ''),
        'client_secret': getattr(settings, 'TWITTER_CLIENT_SECRET', ''),
    },
    'pinterest': {
        'authorize_url': 'https://www.pinterest.com/oauth/',
        'token_url': 'https://api.pinterest.com/v5/oauth/token',
        'scopes': ['boards:read', 'boards:write', 'pins:read', 'pins:write'],
        'client_id': getattr(settings, 'PINTEREST_APP_ID', ''),
        'client_secret': getattr(settings, 'PINTEREST_APP_SECRET', ''),
    }
}



@router.get("/oauth/connect/{platform}", summary="Initiate OAuth flow")
async def initiate_oauth(
    platform: str,
    client_id: int = Query(...),
    token: Optional[str] = Query(None),  #  Add token as query parameter
    request: Request = None
):
    """Start OAuth authorization flow"""
    
    access_token = None
    
    #  PRIORITY 1: Get from URL query parameter (most reliable for popups)
    if token:
        access_token = token
        print(f" Token from URL parameter: {access_token[:20]}...")
    
    # 2. Try from cookie
    if not access_token:
        access_token = request.cookies.get('access_token')
        if access_token:
            print(f"Token from cookie: {access_token[:20]}...")
    
    # 3. Try from Authorization header
    if not access_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
            print(f"Token from header: {access_token[:20]}...")
    
    if not access_token:
        print("❌ No token found in query, cookie, or header")
        return HTMLResponse("""
            <html>
                <head>
                    <style>
                        body { font-family: 'Segoe UI', Arial; padding: 40px; text-align: center; background: #f8fafc; }
                        .error-box { background: white; padding: 40px; border-radius: 16px; max-width: 500px; margin: 50px auto; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
                        h2 { color: #ef4444; margin-bottom: 1rem; }
                        p { color: #64748b; margin-bottom: 1.5rem; }
                        button { padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
                        button:hover { background: #2563eb; }
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h2>🔒 Authentication Required</h2>
                        <p>You need to be logged in to connect social media accounts.</p>
                        <button onclick="closeAndRedirect()">Close & Login</button>
                    </div>
                    <script>
                        function closeAndRedirect() {
                            if (window.opener) {
                                window.opener.location.href = '/auth/login';
                            }
                            window.close();
                        }
                    </script>
                </body>
            </html>
        """, status_code=401)
    
    # Verify token
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(
            access_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        current_user = payload
        print(f" Authenticated user ID: {current_user.get('user_id')}")
        
    except JWTError as e:
        print(f"❌ Token validation failed: {str(e)}")
        return HTMLResponse("""
            <html>
                <head>
                    <style>
                        body { font-family: 'Segoe UI', Arial; padding: 40px; text-align: center; background: #f8fafc; }
                        .error-box { background: white; padding: 40px; border-radius: 16px; max-width: 500px; margin: 50px auto; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
                        h2 { color: #ef4444; margin-bottom: 1rem; }
                        button { padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h2>⚠️ Session Expired</h2>
                        <p>Your session has expired. Please login again.</p>
                        <button onclick="closeAndRedirect()">Close & Login</button>
                    </div>
                    <script>
                        function closeAndRedirect() {
                            if (window.opener) {
                                window.opener.location.href = '/auth/login';
                            }
                            window.close();
                        }
                    </script>
                </body>
            </html>
        """, status_code=401)
    
    if platform not in OAUTH_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Platform {platform} not supported")
    
    config = OAUTH_CONFIGS[platform]
    
    if not config['client_id'] or not config['client_secret']:
        return HTMLResponse(f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: 'Segoe UI', Arial; padding: 40px; text-align: center; background: #f8fafc; }}
                        .error-box {{ background: white; padding: 40px; border-radius: 16px; max-width: 500px; margin: 50px auto; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                        h2 {{ color: #f59e0b; margin-bottom: 1rem; }}
                        button {{ padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }}
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h2>⚙️ Configuration Missing</h2>
                        <p>{platform.title()} OAuth is not configured.</p>
                        <p style="color: #64748b; font-size: 0.9rem;">Please contact your administrator.</p>
                        <button onclick="window.close()">Close</button>
                    </div>
                </body>
            </html>
        """, status_code=500)
    
    # Generate state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        'platform': platform,
        'client_id': client_id,
        'user_id': current_user['user_id'],
        'timestamp': datetime.now()
    }
    
    print(f" OAuth state created - Platform: {platform}, Client: {client_id}, User: {current_user['user_id']}")
    
    # Build redirect URI
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/v1/social-media/oauth/callback/{platform}"
    
    # Build authorization URL
    from urllib.parse import urlencode
    auth_params = {
        'client_id': config['client_id'],
        'redirect_uri': redirect_uri,
        'scope': ' '.join(config['scopes']),
        'state': state,
        'response_type': 'code'
    }
    
    if platform == 'twitter':
        auth_params['code_challenge'] = 'challenge'
        auth_params['code_challenge_method'] = 'plain'
    
    auth_url = config['authorize_url'] + '?' + urlencode(auth_params)
    
    print(f" Redirecting to {platform} OAuth: {auth_url[:80]}...")
    
    return RedirectResponse(url=auth_url)


# Update the oauth_callback function's error handling:
@router.get("/oauth/callback/{platform}", summary="OAuth callback handler")
async def oauth_callback(
    platform: str,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    request: Request = None
):
    """Handle OAuth callback from platform"""
    
    # Handle OAuth errors with specific LinkedIn instructions
    if error:
        error_msg = error_description or error
        print(f"❌ OAuth error from {platform}: {error_msg}")
        
        # Special handling for LinkedIn scope errors
        if platform == 'linkedin' and 'scope' in error.lower():
            return HTMLResponse(f"""
                <html>
                    <head>
                        <title>LinkedIn Setup Required</title>
                        <style>
                            body {{ font-family: 'Segoe UI', Arial; padding: 20px; background: #f8fafc; }}
                            .error-box {{ background: white; padding: 30px; border-radius: 12px; max-width: 700px; margin: 30px auto; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                            h2 {{ color: #0077b5; margin-bottom: 1rem; display: flex; align-items: center; gap: 10px; }}
                            .steps {{ background: #f1f5f9; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                            .steps ol {{ margin: 10px 0; padding-left: 25px; }}
                            .steps li {{ margin: 10px 0; line-height: 1.6; }}
                            .code {{ background: #1e293b; color: #10b981; padding: 2px 8px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 0.9rem; }}
                            .btn {{ padding: 12px 24px; background: #0077b5; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; margin-top: 20px; }}
                            .btn:hover {{ background: #005885; }}
                            .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 15px 0; border-radius: 4px; }}
                        </style>
                    </head>
                    <body>
                        <div class="error-box">
                            <h2>
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="#0077b5"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H6.5v-7H9v7zM7.7 8.7c-.8 0-1.4-.6-1.4-1.4s.6-1.4 1.4-1.4 1.4.6 1.4 1.4-.6 1.4-1.4 1.4zM18 17h-2.5v-3.4c0-.9 0-2.1-1.3-2.1s-1.5 1-1.5 2v3.5h-2.5v-7h2.4v1h.03c.3-.6 1.1-1.3 2.2-1.3 2.4 0 2.8 1.6 2.8 3.6V17z"/></svg>
                                LinkedIn App Configuration Required
                            </h2>
                            
                            <div class="warning">
                                <strong>⚠️ Error:</strong> {error_msg}
                            </div>
                            
                            <p>Your LinkedIn app needs additional products enabled before OAuth will work. Follow these steps:</p>
                            
                            <div class="steps">
                                <h3>📋 Setup Instructions:</h3>
                                <ol>
                                    <li>Go to <a href="https://www.linkedin.com/developers/apps" target="_blank">LinkedIn Developer Portal</a></li>
                                    <li>Select your app: <span class="code">{getattr(settings, 'LINKEDIN_CLIENT_ID', 'YOUR_APP')}</span></li>
                                    <li>Click the <strong>"Products"</strong> tab</li>
                                    <li>Request access to these products:
                                        <ul style="margin-top: 8px;">
                                            <li>✅ <strong>Share on LinkedIn</strong> (Required for posting)</li>
                                            <li>✅ <strong>Sign In with LinkedIn using OpenID Connect</strong> (Required for auth)</li>
                                            <li>🔵 <strong>Marketing Developer Platform</strong> (Optional - for company pages)</li>
                                        </ul>
                                    </li>
                                    <li>Wait for approval (usually instant for "Share on LinkedIn")</li>
                                    <li>Once approved, verify <strong>OAuth 2.0 scopes</strong> under the "Auth" tab shows:
                                        <ul style="margin-top: 8px;">
                                            <li><span class="code">profile</span></li>
                                            <li><span class="code">email</span></li>
                                            <li><span class="code">w_member_social</span></li>
                                        </ul>
                                    </li>
                                    <li>Add redirect URI: <span class="code">{str(request.base_url).rstrip('/')}/api/v1/social-media/oauth/callback/linkedin</span></li>
                                </ol>
                            </div>
                            
                            <p style="color: #64748b; font-size: 0.95rem; margin-top: 20px;">
                                <strong>Note:</strong> If you need to post to LinkedIn Company Pages, you'll need the "Marketing Developer Platform" product, which may require LinkedIn review.
                            </p>
                            
                            <button class="btn" onclick="window.close()">Close & Try Again After Setup</button>
                        </div>
                        
                        <script>
                            setTimeout(() => {{
                                if (window.opener) {{
                                    window.opener.postMessage({{
                                        type: 'oauth_error',
                                        platform: 'linkedin',
                                        error: '{error_msg}'
                                    }}, '*');
                                }}
                            }}, 500);
                        </script>
                    </body>
                </html>
            """, status_code=400)
        
        # Generic error for other platforms
        return HTMLResponse(f"""
            <html>
                <head>
                    <title>OAuth Error</title>
                    <style>
                        body {{ font-family: 'Segoe UI', Arial; padding: 40px; text-align: center; background: #f8fafc; }}
                        .error-box {{ background: white; padding: 40px; border-radius: 16px; max-width: 500px; margin: 50px auto; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                        h2 {{ color: #ef4444; margin-bottom: 1rem; }}
                        .error-details {{ background: #fef2f2; padding: 15px; border-radius: 8px; margin: 20px 0; color: #991b1b; font-family: monospace; font-size: 0.9rem; }}
                        button {{ padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; margin-top: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h2>❌ Connection Failed</h2>
                        <p>{platform.title()} authorization was not completed.</p>
                        <div class="error-details">{error_msg}</div>
                        <button onclick="window.close()">Close Window</button>
                    </div>
                    <script>
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'oauth_error',
                                platform: '{platform}',
                                error: '{error_msg}'
                            }}, '*');
                        }}
                    </script>
                </body>
            </html>
        """, status_code=400)
    
    # Validate required parameters
    if not code or not state:
        return HTMLResponse("""
            <html>
                <head>
                    <title>Invalid Request</title>
                    <style>
                        body { font-family: 'Segoe UI', Arial; padding: 40px; text-align: center; background: #f8fafc; }
                        .error-box { background: white; padding: 40px; border-radius: 16px; max-width: 500px; margin: 50px auto; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
                        h2 { color: #ef4444; margin-bottom: 1rem; }
                        button { padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h2>❌ Invalid Request</h2>
                        <p>Missing required authorization parameters.</p>
                        <button onclick="window.close()">Close Window</button>
                    </div>
                </body>
            </html>
        """, status_code=400)
    
    # Validate state token
    if state not in oauth_states:
        return HTMLResponse("""
            <html>
                <head>
                    <title>Security Error</title>
                    <style>
                        body { font-family: 'Segoe UI', Arial; padding: 40px; text-align: center; background: #f8fafc; }
                        .error-box { background: white; padding: 40px; border-radius: 16px; max-width: 500px; margin: 50px auto; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
                        h2 { color: #ef4444; margin-bottom: 1rem; }
                        button { padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h2>❌ Security Validation Failed</h2>
                        <p>Invalid or expired state token. Please try connecting again.</p>
                        <button onclick="window.close()">Close Window</button>
                    </div>
                </body>
            </html>
        """, status_code=400)
    
    oauth_data = oauth_states[state]
    config = OAUTH_CONFIGS[platform]
    
    print(f"✅ Valid OAuth callback - Platform: {platform}, Code: {code[:20]}...")
    print(f"📦 OAuth data - Client ID: {oauth_data['client_id']}, User ID: {oauth_data['user_id']}")
    
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/v1/social-media/oauth/callback/{platform}"
    
    try:
        # Exchange code for token
        token_data = {
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        print(f"🔄 Exchanging code for token with {platform}...")
        print(f"   Token URL: {config['token_url']}")
        print(f"   Redirect URI: {redirect_uri}")
        
        import requests
        response = requests.post(config['token_url'], data=token_data, timeout=30)
        
        print(f"📡 Token exchange response status: {response.status_code}")
        
        if not response.ok:
            print(f"❌ Token exchange failed: {response.text}")
            raise Exception(f"Token exchange failed: {response.text[:200]}")
        
        token_response = response.json()
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')
        expires_in = token_response.get('expires_in')
        
        print(f"✅ Access token received (length: {len(access_token) if access_token else 0})")
        print(f"   Refresh token: {'Yes' if refresh_token else 'No'}")
        print(f"   Expires in: {expires_in} seconds")
        
        if not access_token:
            raise Exception("No access token in response")
        
        # Get account info
        print(f"📋 Fetching account info from {platform}...")
        account_info = get_platform_account_info(platform, access_token)
        print(f"✅ Account info retrieved:")
        print(f"   ID: {account_info['id']}")
        print(f"   Name: {account_info['name']}")
        
        # Save credentials to database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        token_expires_at = datetime.now() + timedelta(seconds=expires_in) if expires_in else None
        
        print(f"💾 Saving credentials to database...")
        print(f"   Client ID: {oauth_data['client_id']}")
        print(f"   Platform: {platform}")
        print(f"   Account ID: {account_info['id']}")
        print(f"   Account Name: {account_info['name']}")
        
        cursor.execute("""
            INSERT INTO social_media_credentials 
            (client_id, platform, platform_account_id, platform_account_name, 
             access_token, refresh_token, token_expires_at, account_metadata, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
                platform_account_name = VALUES(platform_account_name),
                access_token = VALUES(access_token),
                refresh_token = VALUES(refresh_token),
                token_expires_at = VALUES(token_expires_at),
                account_metadata = VALUES(account_metadata),
                is_active = TRUE,
                updated_at = CURRENT_TIMESTAMP
        """, (
            oauth_data['client_id'],
            platform,
            account_info['id'],
            account_info['name'],
            access_token,
            refresh_token,
            token_expires_at,
            json.dumps(account_info.get('metadata')) if account_info.get('metadata') else None
        ))
        
        affected_rows = cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"✅ Database updated - Affected rows: {affected_rows}")
        
        # Clean up state
        del oauth_states[state]
        
        print(f"🎉 {platform} account connected successfully for client {oauth_data['client_id']}")
        
        # Return beautiful success page with postMessage
        return HTMLResponse(f"""
            <html>
                <head>
                    <title>Connected Successfully</title>
                    <style>
                        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                        body {{ 
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; 
                            min-height: 100vh; 
                            display: flex; 
                            align-items: center; 
                            justify-content: center;
                            padding: 20px;
                        }}
                        .success-box {{
                            background: white;
                            color: #1e293b;
                            padding: 50px;
                            border-radius: 20px;
                            text-align: center;
                            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                            max-width: 500px;
                            width: 100%;
                            animation: slideIn 0.5s ease-out;
                        }}
                        @keyframes slideIn {{
                            from {{ transform: translateY(-50px); opacity: 0; }}
                            to {{ transform: translateY(0); opacity: 1; }}
                        }}
                        .checkmark {{
                            width: 80px;
                            height: 80px;
                            border-radius: 50%;
                            display: block;
                            margin: 0 auto 30px;
                            stroke-width: 3;
                            stroke: #10b981;
                            stroke-miterlimit: 10;
                            animation: fill .4s ease-in-out .4s forwards, scale .3s ease-in-out .9s both;
                        }}
                        .checkmark__circle {{
                            stroke-dasharray: 166;
                            stroke-dashoffset: 166;
                            stroke-width: 3;
                            stroke-miterlimit: 10;
                            stroke: #10b981;
                            fill: none;
                            animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
                        }}
                        .checkmark__check {{
                            transform-origin: 50% 50%;
                            stroke-dasharray: 48;
                            stroke-dashoffset: 48;
                            animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
                        }}
                        @keyframes stroke {{
                            100% {{ stroke-dashoffset: 0; }}
                        }}
                        @keyframes scale {{
                            0%, 100% {{ transform: none; }}
                            50% {{ transform: scale3d(1.1, 1.1, 1); }}
                        }}
                        h2 {{
                            color: #1e293b;
                            margin-bottom: 15px;
                            font-size: 2rem;
                            font-weight: 700;
                        }}
                        p {{
                            color: #64748b;
                            font-size: 1.1rem;
                            margin-bottom: 30px;
                            line-height: 1.6;
                        }}
                        .platform-badge {{
                            display: inline-block;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 8px 20px;
                            border-radius: 20px;
                            font-weight: 600;
                            margin-bottom: 20px;
                            font-size: 0.9rem;
                            letter-spacing: 0.5px;
                        }}
                        .account-info {{
                            background: #f1f5f9;
                            padding: 20px;
                            border-radius: 12px;
                            margin: 25px 0;
                        }}
                        .account-name {{
                            font-size: 1.2rem;
                            font-weight: 600;
                            color: #0f172a;
                            margin-top: 8px;
                        }}
                        .account-id {{
                            font-family: 'Courier New', monospace;
                            font-size: 0.85rem;
                            color: #64748b;
                            margin-top: 5px;
                        }}
                        .auto-close {{
                            color: #94a3b8;
                            font-size: 0.9rem;
                            margin-top: 25px;
                            font-style: italic;
                        }}
                        .countdown {{
                            display: inline-block;
                            font-weight: 700;
                            color: #667eea;
                        }}
                    </style>
                </head>
                <body>
                    <div class="success-box">
                        <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                            <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                            <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                        </svg>
                        
                        <div class="platform-badge">{platform.upper()}</div>
                        <h2>Successfully Connected!</h2>
                        <p>Your {platform.title()} account has been securely linked to PanvelIQ.</p>
                        
                        <div class="account-info">
                            <div style="color: #64748b; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Connected Account</div>
                            <div class="account-name">{account_info['name']}</div>
                            <div class="account-id">ID: {account_info['id']}</div>
                        </div>
                        
                        <p class="auto-close">
                            Closing in <span class="countdown" id="countdown">3</span> seconds...
                        </p>
                    </div>
                    
                    <script>
                        // Send success message to parent window
                        console.log('✅ Sending success message to parent window');
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'oauth_success',
                                platform: '{platform}',
                                account: {{
                                    id: '{account_info["id"]}',
                                    name: '{account_info["name"]}'
                                }}
                            }}, '*');
                            console.log(' Message sent to parent');
                        }} else {{
                            console.log('⚠️ No window.opener found');
                        }}
                        
                        // Countdown timer
                        let seconds = 3;
                        const countdownEl = document.getElementById('countdown');
                        
                        const countdown = setInterval(() => {{
                            seconds--;
                            countdownEl.textContent = seconds;
                            
                            if (seconds <= 0) {{
                                clearInterval(countdown);
                                window.close();
                            }}
                        }}, 1000);
                    </script>
                </body>
            </html>
        """)
        
    except Exception as e:
        print(f"❌ OAuth callback error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return HTMLResponse(f"""
            <html>
                <head>
                    <title>Connection Error</title>
                    <style>
                        body {{ 
                            font-family: 'Segoe UI', Arial; 
                            padding: 40px; 
                            text-align: center; 
                            background: #fef2f2; 
                        }}
                        .error-box {{ 
                            background: white; 
                            padding: 40px; 
                            border-radius: 16px; 
                            max-width: 500px; 
                            margin: 50px auto; 
                            box-shadow: 0 4px 20px rgba(0,0,0,0.1); 
                        }}
                        h2 {{ 
                            color: #ef4444; 
                            margin-bottom: 1rem; 
                        }}
                        .error-details {{ 
                            background: #fee2e2; 
                            padding: 15px; 
                            border-radius: 8px; 
                            margin: 20px 0; 
                            color: #991b1b; 
                            font-family: monospace; 
                            font-size: 0.9rem; 
                            word-break: break-all;
                            text-align: left;
                            max-height: 200px;
                            overflow-y: auto;
                        }}
                        button {{ 
                            padding: 12px 24px; 
                            background: #3b82f6; 
                            color: white; 
                            border: none; 
                            border-radius: 8px; 
                            cursor: pointer; 
                            font-size: 16px; 
                        }}
                        button:hover {{
                            background: #2563eb;
                        }}
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h2>❌ Connection Failed</h2>
                        <p>We encountered an error while connecting your {platform.title()} account.</p>
                        <div class="error-details">{str(e)}</div>
                        <p style="color: #64748b; font-size: 0.9rem; margin-top: 20px;">
                            Please try again or contact support if the problem persists.
                        </p>
                        <button onclick="window.close()">Close Window</button>
                    </div>
                    <script>
                        console.log('❌ OAuth error:', '{str(e)}');
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'oauth_error',
                                platform: '{platform}',
                                error: '{str(e)}'
                            }}, '*');
                        }}
                    </script>
                </body>
            </html>
        """, status_code=500)



def get_platform_account_info(platform: str, access_token: str) -> dict:
    """Get account info from platform"""
    import requests
    
    if platform == 'facebook':
        response = requests.get('https://graph.facebook.com/v18.0/me/accounts', params={'access_token': access_token})
        response.raise_for_status()
        pages = response.json().get('data', [])
        if pages:
            page = pages[0]
            return {'id': page['id'], 'name': page['name'], 'metadata': {'access_token': page['access_token']}}
        raise Exception("No Facebook pages found")
    
    elif platform == 'instagram':
        response = requests.get('https://graph.facebook.com/v18.0/me/accounts', 
                              params={'access_token': access_token, 'fields': 'instagram_business_account,name'})
        response.raise_for_status()
        pages = response.json().get('data', [])
        for page in pages:
            if 'instagram_business_account' in page:
                ig = page['instagram_business_account']
                return {'id': ig['id'], 'name': f"Instagram - {page['name']}", 'metadata': {}}
        raise Exception("No Instagram business account found")
    
    elif platform == 'linkedin':
        #  Use OpenID Connect userinfo endpoint
        response = requests.get(
            'https://api.linkedin.com/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        profile = response.json()
        
        person_id = profile.get('sub')  # OpenID subject identifier
        name = profile.get('name') or f"{profile.get('given_name', '')} {profile.get('family_name', '')}".strip()
        
        return {
            'id': person_id,
            'name': name or 'LinkedIn User',
            'metadata': {
                'email': profile.get('email'),
                'picture': profile.get('picture')
            }
        }
    
    elif platform == 'twitter':
        response = requests.get('https://api.twitter.com/2/users/me', headers={'Authorization': f'Bearer {access_token}'})
        response.raise_for_status()
        user = response.json().get('data', {})
        return {'id': user.get('id'), 'name': user.get('username'), 'metadata': {}}
    
    elif platform == 'pinterest':
        response = requests.get('https://api.pinterest.com/v5/user_account', headers={'Authorization': f'Bearer {access_token}'})
        response.raise_for_status()
        user = response.json()
        return {'id': user.get('username'), 'name': user.get('username'), 'metadata': {}}
    
    raise Exception(f"Platform {platform} not supported")


@router.get("/connected-accounts", summary="Get connected social media accounts")
async def get_connected_accounts(
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get all connected social media accounts for all clients (admin/employee view)"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # ✅ CORRECT TABLE NAME
        cursor.execute("""
            SELECT 
                smc.credential_id,
                smc.client_id,
                smc.platform,
                smc.platform_account_id,
                smc.platform_account_name,
                smc.token_expires_at,
                smc.created_at,
                u.full_name as client_name,
                u.email as client_email
            FROM social_media_credentials smc
            JOIN users u ON smc.client_id = u.user_id
            WHERE smc.is_active = TRUE
            ORDER BY smc.created_at DESC
        """)
        
        accounts = cursor.fetchall()
        
        print(f"✅ Found {len(accounts)} connected accounts")
        
        # Convert datetime to string
        for account in accounts:
            if account.get('token_expires_at'):
                account['token_expires_at'] = account['token_expires_at'].isoformat()
            if account.get('created_at'):
                account['created_at'] = account['created_at'].isoformat()
        
        return {
            "success": True,
            "accounts": accounts,
            "total": len(accounts)
        }
        
    except Exception as e:
        print(f"❌ Error fetching connected accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch connected accounts: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@router.delete("/disconnect-account/{credential_id}", summary="Disconnect social media account")
async def disconnect_account(
    credential_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Disconnect/delete a social media account"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # ✅ CORRECT TABLE NAME
        cursor.execute("""
            DELETE FROM social_media_credentials
            WHERE credential_id = %s
        """, (credential_id,))
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Account disconnected successfully"
        }
        
    except Exception as e:
        print(f"❌ Error disconnecting account: {str(e)}")
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect account: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



# ========== CONFLICT DETECTION ==========
@router.post("/check-conflicts", summary="Check for scheduling conflicts")
async def check_scheduling_conflicts(
    client_id: int,
    platform: str,
    scheduled_at: str,  # ISO format datetime
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Check if scheduling this post will create conflicts (posts too close together)
    Alerts when posts are within 2 hours of each other on the same platform
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Parse the scheduled time
        try:
            schedule_time = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
        except:
            raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
        
        # Calculate 2-hour window
        time_before = schedule_time - timedelta(hours=2)
        time_after = schedule_time + timedelta(hours=2)
        
        # Check for conflicts
        cursor.execute("""
            SELECT 
                post_id,
                caption,
                scheduled_at,
                TIMESTAMPDIFF(MINUTE, scheduled_at, %s) as minutes_diff
            FROM social_media_posts
            WHERE client_id = %s
            AND platform = %s
            AND status IN ('scheduled', 'draft')
            AND scheduled_at IS NOT NULL
            AND scheduled_at BETWEEN %s AND %s
            ORDER BY scheduled_at
        """, (scheduled_at, client_id, platform, time_before, time_after))
        
        conflicts = cursor.fetchall()
        
        has_conflicts = len(conflicts) > 0
        
        # Format conflicts
        conflict_details = []
        for conflict in conflicts:
            minutes = abs(conflict['minutes_diff'])
            hours = minutes // 60
            mins = minutes % 60
            
            time_diff = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
            
            conflict_details.append({
                "post_id": conflict['post_id'],
                "caption_preview": conflict['caption'][:50] + "..." if len(conflict['caption']) > 50 else conflict['caption'],
                "scheduled_at": conflict['scheduled_at'].isoformat(),
                "time_difference": time_diff,
                "minutes_apart": minutes
            })
        
        return {
            "success": True,
            "has_conflicts": has_conflicts,
            "conflict_count": len(conflicts),
            "conflicts": conflict_details,
            "warning": "⚠️ Posts scheduled too close together may reduce engagement effectiveness" if has_conflicts else None,
            "recommendation": "Consider spacing posts at least 2-3 hours apart for optimal reach" if has_conflicts else "No conflicts detected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== UNIFIED INBOX ENDPOINTS ==========

@router.get("/inbox/{client_id}", summary="Get unified inbox messages")
async def get_unified_inbox(
    client_id: int,
    platform: Optional[str] = None,
    is_read: Optional[bool] = None,
    limit: int = 50,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get all messages from unified inbox across platforms
    Supports filtering by platform and read status
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Build query with filters
        query = """
            SELECT 
                m.*,
                u.full_name as replied_by_name
            FROM social_media_messages m
            LEFT JOIN users u ON m.replied_by = u.user_id
            WHERE m.client_id = %s
        """
        params = [client_id]
        
        if platform:
            query += " AND m.platform = %s"
            params.append(platform)
        
        if is_read is not None:
            query += " AND m.is_read = %s"
            params.append(is_read)
        
        query += " ORDER BY m.created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        messages = cursor.fetchall()
        
        # Format dates
        for msg in messages:
            if msg.get('created_at'):
                msg['created_at'] = msg['created_at'].isoformat()
            if msg.get('replied_at'):
                msg['replied_at'] = msg['replied_at'].isoformat()
            if msg.get('updated_at'):
                msg['updated_at'] = msg['updated_at'].isoformat()
            
            # Parse JSON fields
            if msg.get('tags'):
                try:
                    msg['tags'] = json.loads(msg['tags']) if isinstance(msg['tags'], str) else msg['tags']
                except:
                    msg['tags'] = []
        
        # Get summary stats
        cursor.execute("""
            SELECT 
                platform,
                COUNT(*) as total_messages,
                SUM(CASE WHEN is_read = FALSE THEN 1 ELSE 0 END) as unread_count,
                SUM(CASE WHEN urgency_score >= 4 THEN 1 ELSE 0 END) as urgent_count
            FROM social_media_messages
            WHERE client_id = %s
            GROUP BY platform
        """, (client_id,))
        
        stats = cursor.fetchall()
        
        return {
            "success": True,
            "messages": messages,
            "total_count": len(messages),
            "platform_stats": stats,
            "note": "Instagram/Facebook Messenger requires Meta Business verification (pending)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.post("/inbox/reply", summary="Reply to a message")
async def reply_to_message(
    request: MessageReplyRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Reply to a message in unified inbox
    Routes message through correct platform API
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get message details
        cursor.execute("""
            SELECT *
            FROM social_media_messages
            WHERE message_id = %s
        """, (request.message_id,))
        
        message = cursor.fetchone()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # TODO: Route reply through platform API
        # For now, just store the reply in database
        
        cursor.execute("""
            UPDATE social_media_messages
            SET 
                is_replied = TRUE,
                replied_at = NOW(),
                replied_by = %s,
                reply_text = %s
            WHERE message_id = %s
        """, (current_user['user_id'], request.reply_text, request.message_id))
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Reply sent successfully",
            "note": "Platform API integration pending for actual message delivery"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.patch("/inbox/{message_id}/mark-read", summary="Mark message as read")
async def mark_message_as_read(
    message_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Mark a message as read"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE social_media_messages
            SET is_read = TRUE
            WHERE message_id = %s
        """, (message_id,))
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Message marked as read"
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()




# ========== AI CALENDAR SUGGESTIONS FOR KERALA ==========
@router.get("/calendar-suggestions", summary="Get AI-powered calendar suggestions for Kerala")
async def get_calendar_suggestions(
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get AI-powered calendar suggestions for special days, holidays, and events in Kerala
    Includes: National holidays, Kerala festivals, cultural events, and special days
    """
    from datetime import datetime
    import calendar as cal
    
    # Use current month/year if not provided
    now = datetime.now()
    target_month = month or now.month
    target_year = year or now.year
    
    # Comprehensive Kerala Holidays and Special Days Database
    kerala_holidays = {
        1: [  # January
            {"date": 1, "name": "New Year's Day", "type": "national", "category": "Public Holiday"},
            {"date": 14, "name": "Makar Sankranti / Pongal", "type": "festival", "category": "Harvest Festival"},
            {"date": 26, "name": "Republic Day", "type": "national", "category": "Public Holiday"},
        ],
        2: [  # February
            {"date": 14, "name": "Valentine's Day", "type": "special", "category": "International Day"},
            {"date": 21, "name": "International Mother Language Day", "type": "special", "category": "Cultural Day"},
        ],
        3: [  # March
            {"date": 8, "name": "International Women's Day", "type": "special", "category": "International Day"},
            {"date": 22, "name": "World Water Day", "type": "special", "category": "Environmental Day"},
        ],
        4: [  # April
            {"date": 1, "name": "April Fool's Day", "type": "special", "category": "Fun Day"},
            {"date": 14, "name": "Vishu", "type": "festival", "category": "Kerala New Year"},
            {"date": 15, "name": "Vishu (Day 2)", "type": "festival", "category": "Kerala New Year"},
            {"date": 22, "name": "Earth Day", "type": "special", "category": "Environmental Day"},
        ],
        5: [  # May
            {"date": 1, "name": "May Day / Labour Day", "type": "national", "category": "Public Holiday"},
            {"date": 12, "name": "International Nurses Day", "type": "special", "category": "Professional Day"},
        ],
        6: [  # June
            {"date": 5, "name": "World Environment Day", "type": "special", "category": "Environmental Day"},
            {"date": 21, "name": "International Yoga Day", "type": "special", "category": "Health Day"},
        ],
        7: [  # July
            {"date": 1, "name": "Kerala Piravi (Kerala Formation Day)", "type": "state", "category": "State Holiday"},
            {"date": 15, "name": "Karkkidakam Vavu", "type": "festival", "category": "Ancestral Day"},
        ],
        8: [  # August
            {"date": 15, "name": "Independence Day", "type": "national", "category": "Public Holiday"},
            {"date": 15, "name": "Onam Season Begins", "type": "festival", "category": "Kerala Festival"},
            {"date": 26, "name": "Thiruvonam (Onam)", "type": "festival", "category": "Kerala Festival"},
        ],
        9: [  # September
            {"date": 5, "name": "Teachers' Day", "type": "special", "category": "Professional Day"},
            {"date": 10, "name": "Ganesh Chaturthi", "type": "festival", "category": "Religious Festival"},
        ],
        10: [  # October
            {"date": 2, "name": "Gandhi Jayanti", "type": "national", "category": "Public Holiday"},
            {"date": 15, "name": "Dussehra", "type": "festival", "category": "Religious Festival"},
            {"date": 24, "name": "Diwali", "type": "festival", "category": "Festival of Lights"},
            {"date": 31, "name": "Halloween", "type": "special", "category": "International Day"},
        ],
        11: [  # November
            {"date": 1, "name": "Kerala Piravi Celebrations", "type": "state", "category": "Cultural Month"},
            {"date": 12, "name": "Diwali (Kerala)", "type": "festival", "category": "Festival of Lights"},
            {"date": 14, "name": "Children's Day", "type": "special", "category": "Special Day"},
        ],
        12: [  # December
            {"date": 25, "name": "Christmas", "type": "national", "category": "Public Holiday"},
            {"date": 31, "name": "New Year's Eve", "type": "special", "category": "Celebration"},
        ]
    }
    
    # Get holidays for the target month
    month_holidays = kerala_holidays.get(target_month, [])
    
    # Get the number of days in the month
    days_in_month = cal.monthrange(target_year, target_month)[1]
    
    # Generate AI suggestions for each holiday
    suggestions = []
    
    for holiday in month_holidays:
        day = holiday['date']
        if day <= days_in_month:
            date_str = f"{target_year}-{target_month:02d}-{day:02d}"
            
            # Generate AI-powered content suggestion using OpenAI
            try:
                prompt = f"""Generate a creative and engaging social media post idea for {holiday['name']} ({holiday['category']}) in Kerala.
                
Holiday Type: {holiday['type']}
Context: This is for businesses/brands in Kerala to connect with their audience.

Provide:
1. A catchy post caption (2-3 sentences)
2. 3-5 relevant hashtags
3. Content theme suggestion

Keep it culturally relevant, engaging, and suitable for Instagram/Facebook."""

                response = openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a creative social media content expert specializing in Kerala culture and festivals."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.8
                )
                
                ai_suggestion = response.choices[0].message.content.strip()
                
                suggestions.append({
                    "date": date_str,
                    "day": day,
                    "holiday_name": holiday['name'],
                    "holiday_type": holiday['type'],
                    "category": holiday['category'],
                    "ai_suggestion": ai_suggestion,
                    "relevance_score": 95 if holiday['type'] in ['national', 'festival', 'state'] else 75
                })
                
            except Exception as e:
                # Fallback if OpenAI fails
                suggestions.append({
                    "date": date_str,
                    "day": day,
                    "holiday_name": holiday['name'],
                    "holiday_type": holiday['type'],
                    "category": holiday['category'],
                    "ai_suggestion": f"Create engaging content celebrating {holiday['name']}. Share the cultural significance and connect with your audience through relevant visuals and messages.",
                    "relevance_score": 90 if holiday['type'] in ['national', 'festival', 'state'] else 70,
                    "note": "OpenAI suggestion unavailable"
                })
    
    return {
        "success": True,
        "month": target_month,
        "year": target_year,
        "month_name": cal.month_name[target_month],
        "total_suggestions": len(suggestions),
        "suggestions": suggestions
    }






# ========== CREATE A/B TEST ==========
@router.post("/ab-tests", summary="Create A/B test campaign")
async def create_ab_test(
    test: ABTestCreate,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Create A/B test campaign with two post variants
    Uses AI best time recommendations for optimal scheduling
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Verify client exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s AND role = 'client'", 
                      (test.client_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Create A/B test campaign
        cursor.execute("""
            INSERT INTO ab_test_campaigns 
            (client_id, platform, test_name, test_type, status, created_by)
            VALUES (%s, %s, %s, %s, 'active', %s)
        """, (test.client_id, test.platform, test.test_name, test.test_type, current_user['user_id']))
        
        ab_test_id = cursor.lastrowid
        
        # Parse scheduled times
        variant_a_time = None
        variant_b_time = None
        
        if test.variant_a_scheduled_at:
            try:
                variant_a_time = datetime.fromisoformat(test.variant_a_scheduled_at.replace('Z', '+00:00'))
            except:
                pass
        
        if test.variant_b_scheduled_at:
            try:
                variant_b_time = datetime.fromisoformat(test.variant_b_scheduled_at.replace('Z', '+00:00'))
            except:
                pass
        
        # Create Variant A Post
        cursor.execute("""
            INSERT INTO social_media_posts 
            (client_id, created_by, platform, caption, media_urls, hashtags, 
             scheduled_at, status, ab_test_id, ab_variant)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'A')
        """, (
            test.client_id,
            current_user['user_id'],
            test.platform,
            test.variant_a_caption,
            json.dumps(test.variant_a_media_urls),
            json.dumps(test.variant_a_hashtags),
            variant_a_time,
            'scheduled' if variant_a_time else 'draft',
            ab_test_id
        ))
        
        variant_a_post_id = cursor.lastrowid
        
        # Create Variant B Post
        cursor.execute("""
            INSERT INTO social_media_posts 
            (client_id, created_by, platform, caption, media_urls, hashtags, 
             scheduled_at, status, ab_test_id, ab_variant)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'B')
        """, (
            test.client_id,
            current_user['user_id'],
            test.platform,
            test.variant_b_caption,
            json.dumps(test.variant_b_media_urls),
            json.dumps(test.variant_b_hashtags),
            variant_b_time,
            'scheduled' if variant_b_time else 'draft',
            ab_test_id
        ))
        
        variant_b_post_id = cursor.lastrowid
        
        # Update A/B test with post IDs
        cursor.execute("""
            UPDATE ab_test_campaigns 
            SET variant_a_post_id = %s, variant_b_post_id = %s, started_at = NOW()
            WHERE test_id = %s
        """, (variant_a_post_id, variant_b_post_id, ab_test_id))
        
        connection.commit()
        
        return {
            "success": True,
            "message": "A/B test campaign created successfully",
            "test_id": ab_test_id,
            "variant_a_post_id": variant_a_post_id,
            "variant_b_post_id": variant_b_post_id,
            "variant_a_scheduled_at": test.variant_a_scheduled_at,
            "variant_b_scheduled_at": test.variant_b_scheduled_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error creating A/B test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create A/B test: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== GET A/B TESTS ==========
@router.get("/ab-tests", summary="Get all A/B test campaigns")
async def get_ab_tests(
    client_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get all A/B test campaigns with results"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Build query
        query = """
            SELECT 
                abt.*,
                u.full_name as client_name,
                pa.caption as variant_a_caption,
                pa.scheduled_at as variant_a_scheduled,
                pb.caption as variant_b_caption,
                pb.scheduled_at as variant_b_scheduled
            FROM ab_test_campaigns abt
            JOIN users u ON abt.client_id = u.user_id
            LEFT JOIN social_media_posts pa ON abt.variant_a_post_id = pa.post_id
            LEFT JOIN social_media_posts pb ON abt.variant_b_post_id = pb.post_id
            WHERE 1=1
        """
        params = []
        
        if client_id:
            query += " AND abt.client_id = %s"
            params.append(client_id)
        
        if status_filter:
            query += " AND abt.status = %s"
            params.append(status_filter)
        
        query += " ORDER BY abt.created_at DESC"
        
        cursor.execute(query, params)
        tests = cursor.fetchall()
        
        # Format response
        results = []
        for test in tests:
            results.append({
                "test_id": test['test_id'],
                "client_id": test['client_id'],
                "client_name": test['client_name'],
                "platform": test['platform'],
                "test_name": test['test_name'],
                "test_type": test['test_type'],
                "status": test['status'],
                "variant_a": {
                    "post_id": test['variant_a_post_id'],
                    "caption": test['variant_a_caption'],
                    "scheduled_at": test['variant_a_scheduled'].isoformat() if test['variant_a_scheduled'] else None
                },
                "variant_b": {
                    "post_id": test['variant_b_post_id'],
                    "caption": test['variant_b_caption'],
                    "scheduled_at": test['variant_b_scheduled'].isoformat() if test['variant_b_scheduled'] else None
                },
                "winner_variant": test['winner_variant'],
                "confidence_score": float(test['confidence_score']) if test['confidence_score'] else None,
                "started_at": test['started_at'].isoformat() if test['started_at'] else None,
                "completed_at": test['completed_at'].isoformat() if test['completed_at'] else None,
                "created_at": test['created_at'].isoformat()
            })
        
        return {
            "success": True,
            "tests": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== GET A/B TEST RESULTS ==========
@router.get("/ab-tests/{test_id}/results", summary="Get A/B test results and winner")
async def get_ab_test_results(
    test_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get detailed results for an A/B test
    Calculates winner based on engagement rate and statistical significance
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get test details
        cursor.execute("""
            SELECT * FROM ab_test_campaigns WHERE test_id = %s
        """, (test_id,))
        
        test = cursor.fetchone()
        if not test:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        # Get results from ab_test_results table
        cursor.execute("""
            SELECT * FROM ab_test_results 
            WHERE test_id = %s 
            ORDER BY variant, recorded_at DESC
        """, (test_id,))
        
        results = cursor.fetchall()
        
        # Calculate aggregated metrics for each variant
        variant_a_metrics = {
            "impressions": 0,
            "reach": 0,
            "engagement_count": 0,
            "clicks": 0,
            "engagement_rate": 0.0
        }
        
        variant_b_metrics = {
            "impressions": 0,
            "reach": 0,
            "engagement_count": 0,
            "clicks": 0,
            "engagement_rate": 0.0
        }
        
        for result in results:
            if result['variant'] == 'A':
                variant_a_metrics['impressions'] += result['impressions']
                variant_a_metrics['reach'] += result['reach']
                variant_a_metrics['engagement_count'] += result['engagement_count']
                variant_a_metrics['clicks'] += result['clicks']
            else:
                variant_b_metrics['impressions'] += result['impressions']
                variant_b_metrics['reach'] += result['reach']
                variant_b_metrics['engagement_count'] += result['engagement_count']
                variant_b_metrics['clicks'] += result['clicks']
        
        # Calculate engagement rates
        if variant_a_metrics['impressions'] > 0:
            variant_a_metrics['engagement_rate'] = round(
                (variant_a_metrics['engagement_count'] / variant_a_metrics['impressions']) * 100, 2
            )
        
        if variant_b_metrics['impressions'] > 0:
            variant_b_metrics['engagement_rate'] = round(
                (variant_b_metrics['engagement_count'] / variant_b_metrics['impressions']) * 100, 2
            )
        
        # Determine winner
        winner = None
        confidence = 0.0
        
        if variant_a_metrics['engagement_rate'] > variant_b_metrics['engagement_rate']:
            winner = 'A'
            if variant_b_metrics['engagement_rate'] > 0:
                confidence = round(
                    ((variant_a_metrics['engagement_rate'] - variant_b_metrics['engagement_rate']) / 
                     variant_b_metrics['engagement_rate']) * 100, 2
                )
        elif variant_b_metrics['engagement_rate'] > variant_a_metrics['engagement_rate']:
            winner = 'B'
            if variant_a_metrics['engagement_rate'] > 0:
                confidence = round(
                    ((variant_b_metrics['engagement_rate'] - variant_a_metrics['engagement_rate']) / 
                     variant_a_metrics['engagement_rate']) * 100, 2
                )
        else:
            winner = 'tie'
        
        # Update test with winner if not already set
        if test['status'] == 'active' and (variant_a_metrics['impressions'] > 100 or variant_b_metrics['impressions'] > 100):
            cursor.execute("""
                UPDATE ab_test_campaigns 
                SET winner_variant = %s, confidence_score = %s, 
                    status = 'completed', completed_at = NOW()
                WHERE test_id = %s
            """, (winner, confidence, test_id))
            connection.commit()
        
        return {
            "success": True,
            "test_id": test_id,
            "test_name": test['test_name'],
            "status": test['status'],
            "variant_a": variant_a_metrics,
            "variant_b": variant_b_metrics,
            "winner": winner,
            "confidence_score": confidence,
            "recommendation": f"Variant {winner} performed {confidence}% better" if winner != 'tie' else "Both variants performed equally"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()