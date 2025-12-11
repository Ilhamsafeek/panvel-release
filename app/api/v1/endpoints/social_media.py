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
        
        print(f"📤 Publishing post {post_id} to {post['platform']} for client {post['client_id']}")
        
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
        print(f"📤 Publishing to {platform}")
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
            
            print(f"📤 LinkedIn payload (truncated): {json.dumps(payload, indent=2)[:300]}...")
            
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
            print(f"📤 Publishing to Facebook Page ID: {platform_account_id}")
            
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
            print(f"📤 Publishing to Instagram Account: {platform_account_id}")
            
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
            print(f"📤 Publishing to Twitter/X")
            
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
            print(f"📤 Publishing to Pinterest")
            
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
@router.post("/best-times", summary="Get AI-powered best posting times")
async def get_best_times(
    request: BestTimeRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    AI-powered best time recommendations based on platform and engagement patterns
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Check existing best times data
        cursor.execute("""
            SELECT day_of_week, hour_of_day, engagement_score
            FROM platform_best_times
            WHERE client_id = %s AND platform = %s
            ORDER BY engagement_score DESC
            LIMIT 5
        """, (request.client_id, request.platform))
        
        existing_times = cursor.fetchall()
        
        if existing_times:
            # Return existing data
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            recommendations = []
            
            for time_data in existing_times:
                recommendations.append({
                    "day": day_names[time_data['day_of_week']],
                    "hour": time_data['hour_of_day'],
                    "time_formatted": f"{time_data['hour_of_day']:02d}:00",
                    "engagement_score": float(time_data['engagement_score'])
                })
            
            return {
                "success": True,
                "platform": request.platform,
                "recommended_times": recommendations
            }
        
        # Generate AI recommendations if no data exists
        prompt = f"""Based on industry best practices for {request.platform}, suggest the top 5 best times to post for maximum engagement.

Consider:
- Platform: {request.platform}
- General audience behavior patterns
- Peak engagement times

Provide response in JSON format:
[
  {{"day": "Monday", "hour": 9, "engagement_score": 85.5}},
  {{"day": "Tuesday", "hour": 14, "engagement_score": 82.3}}
]

Day should be day name, hour in 24h format (0-23), engagement_score (0-100)
"""
        
        response = openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a social media analytics expert specializing in optimal posting times."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        ai_recommendations = json.loads(response.choices[0].message.content)
        
        # Save recommendations to database
        day_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
        
        for rec in ai_recommendations:
            day_num = day_map.get(rec['day'], 0)
            cursor.execute("""
                INSERT INTO platform_best_times 
                (client_id, platform, day_of_week, hour_of_day, engagement_score, last_calculated)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                engagement_score = %s, last_calculated = NOW()
            """, (
                request.client_id,
                request.platform,
                day_num,
                rec['hour'],
                rec['engagement_score'],
                rec['engagement_score']
            ))
        
        connection.commit()
        
        # Format response
        recommendations = []
        for rec in ai_recommendations:
            recommendations.append({
                "day": rec['day'],
                "hour": rec['hour'],
                "time_formatted": f"{rec['hour']:02d}:00",
                "engagement_score": rec['engagement_score']
            })
        
        return {
            "success": True,
            "platform": request.platform,
            "recommended_times": recommendations
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
        #  UPDATED: Remove r_emailaddress, keep only posting scopes
        'scopes': ['openid', 'profile', 'w_member_social'],  # Changed from r_liteprofile, r_emailaddress
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
    
    # Handle OAuth errors
    if error:
        error_msg = error_description or error
        print(f"❌ OAuth error from {platform}: {error_msg}")
        return HTMLResponse(f"""[... error HTML ...]""", status_code=400)
    
    if not code or not state:
        return HTMLResponse("""[... error HTML ...]""", status_code=400)
    
    if state not in oauth_states:
        return HTMLResponse("""[... error HTML ...]""")
    
    oauth_data = oauth_states[state]
    config = OAUTH_CONFIGS[platform]
    
    print(f"✅ Valid OAuth callback - Platform: {platform}, Code: {code[:20]}...")
    
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
        
        import requests
        response = requests.post(config['token_url'], data=token_data, timeout=30)
        
        if not response.ok:
            print(f"❌ Token exchange failed: {response.text}")
            raise Exception(f"Token exchange failed: {response.text[:200]}")
        
        token_response = response.json()
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')
        expires_in = token_response.get('expires_in')
        
        if not access_token:
            raise Exception("No access token in response")
        
        print(f"✅ Access token received from {platform}")
        
        # Get account info
        print(f"📋 Fetching account info from {platform}...")
        account_info = get_platform_account_info(platform, access_token)
        print(f"✅ Account info: {account_info['name']}")
        
        # ✅ SAVE CREDENTIALS DIRECTLY (FIXED TABLE NAME)
        connection = get_db_connection()
        cursor = connection.cursor()
        
        token_expires_at = datetime.now() + timedelta(seconds=expires_in) if expires_in else None
        
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
        
        connection.commit()
        cursor.close()
        connection.close()
        
        # Clean up state
        del oauth_states[state]
        
        print(f"✅ {platform} account connected successfully for client {oauth_data['client_id']}")
        
        return HTMLResponse(f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: 'Segoe UI', Arial; padding: 40px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
                        .success-box {{ background: white; color: #1e293b; padding: 50px 40px; border-radius: 20px; max-width: 500px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
                        h2 {{ margin: 0 0 20px 0; color: #10b981; font-size: 2rem; }}
                        .checkmark {{ font-size: 4rem; margin-bottom: 1rem; }}
                        .account-name {{ background: #f0fdf4; color: #166534; padding: 0.75rem 1.5rem; border-radius: 10px; margin: 1.5rem 0; font-weight: 600; }}
                        .countdown {{ color: #9926F3; font-weight: 600; margin-top: 1rem; }}
                    </style>
                </head>
                <body>
                    <div class="success-box">
                        <div class="checkmark">✅</div>
                        <h2>Connected!</h2>
                        <div class="account-name">{account_info['name']}</div>
                        <p>Your {platform.title()} account has been successfully connected.</p>
                        <p style="font-size: 0.9rem;">You can now publish posts directly to {platform.title()}.</p>
                        <p class="countdown">Closing in <span id="countdown">3</span> seconds...</p>
                    </div>
                    <script>
                        let seconds = 3;
                        const countdownEl = document.getElementById('countdown');
                        
                        const interval = setInterval(() => {{
                            seconds--;
                            countdownEl.textContent = seconds;
                            if (seconds <= 0) {{
                                clearInterval(interval);
                                window.opener?.postMessage({{type: 'oauth_success', platform: '{platform}'}}, '*');
                                setTimeout(() => window.close(), 500);
                            }}
                        }}, 1000);
                    </script>
                </body>
            </html>
        """)
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ OAuth callback error: {error_msg}")
        
        return HTMLResponse(f"""[... error HTML ...]""")


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
