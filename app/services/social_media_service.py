"""
Social Media API Integration Service
File: app/services/social_media_service.py

Complete implementation for Meta, LinkedIn, Twitter/X, and Pinterest APIs
"""

import requests
import json
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.core.config import settings
import pymysql
from app.core.security import get_db_connection


class SocialMediaService:
    """Service for integrating with social media platform APIs"""
    
    def __init__(self):
        # API Base URLs
        self.meta_graph_url = "https://graph.facebook.com/v18.0"
        self.linkedin_api_url = "https://api.linkedin.com/v2"
        self.twitter_api_url = "https://api.twitter.com/2"
        self.pinterest_api_url = "https://api.pinterest.com/v5"
    
    
    # ========== CREDENTIAL MANAGEMENT ==========
    
    def get_client_credentials(self, client_id: int, platform: str):
        """Get credentials for a client's platform"""
        connection = None
        cursor = None
        
        try:
            from app.core.security import get_db_connection
            connection = get_db_connection()
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            # ✅ FIXED: Use correct table name
            cursor.execute("""
                SELECT 
                    access_token,
                    refresh_token,
                    platform_account_id,
                    platform_account_name,
                    token_expires_at
                FROM social_media_credentials
                WHERE client_id = %s 
                AND platform = %s 
                AND is_active = TRUE
                LIMIT 1
            """, (client_id, platform))
            
            return cursor.fetchone()
            
        except Exception as e:
            print(f"Error getting credentials: {str(e)}")
            return None
            
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        
    
    def save_client_credentials(
        self,
        client_id: int,
        platform: str,
        platform_account_id: str,
        platform_account_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
        account_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save or update platform credentials for a client
        
        Returns:
            True if successful, False otherwise
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            metadata_json = json.dumps(account_metadata) if account_metadata else None
            
            cursor.execute("""
                INSERT INTO social_media_accounts (
                    client_id, platform, platform_account_id, platform_account_name,
                    access_token, refresh_token, token_expires_at, account_metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    access_token = VALUES(access_token),
                    refresh_token = VALUES(refresh_token),
                    token_expires_at = VALUES(token_expires_at),
                    account_metadata = VALUES(account_metadata),
                    platform_account_name = VALUES(platform_account_name),
                    is_active = TRUE,
                    last_used_at = CURRENT_TIMESTAMP
            """, (
                client_id, platform, platform_account_id, platform_account_name,
                access_token, refresh_token, token_expires_at, metadata_json
            ))
            
            connection.commit()
            return True
            
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"Error saving credentials: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    
    # ========== META (FACEBOOK & INSTAGRAM) ==========
    
    def publish_to_instagram(
        self,
        client_id: int,
        caption: str,
        image_url: Optional[str] = None,
        video_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish post to Instagram using Meta Graph API
        
        Args:
            client_id: Client ID
            caption: Post caption
            image_url: URL of image to post
            video_url: URL of video to post
        
        Returns:
            Dict with post_id and status
        """
        try:
            # Get credentials
            credentials = self.get_client_credentials(client_id, 'instagram')
            if not credentials:
                return {
                    "success": False,
                    "error": "Instagram account not connected. Please connect your account first."
                }
            
            access_token = credentials['access_token']
            instagram_account_id = credentials['platform_account_id']
            
            # Step 1: Create media container
            if image_url:
                container_url = f"{self.meta_graph_url}/{instagram_account_id}/media"
                container_params = {
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": access_token
                }
            elif video_url:
                container_url = f"{self.meta_graph_url}/{instagram_account_id}/media"
                container_params = {
                    "media_type": "VIDEO",
                    "video_url": video_url,
                    "caption": caption,
                    "access_token": access_token
                }
            else:
                # Text-only post (not supported on Instagram, needs image)
                return {
                    "success": False,
                    "error": "Instagram requires at least one image or video"
                }
            
            container_response = requests.post(container_url, data=container_params, timeout=30)
            container_response.raise_for_status()
            container_data = container_response.json()
            creation_id = container_data.get('id')
            
            # Step 2: Publish the container
            publish_url = f"{self.meta_graph_url}/{instagram_account_id}/media_publish"
            publish_params = {
                "creation_id": creation_id,
                "access_token": access_token
            }
            
            publish_response = requests.post(publish_url, data=publish_params, timeout=30)
            publish_response.raise_for_status()
            publish_data = publish_response.json()
            
            # Update last_used_at
            self._update_account_last_used(client_id, 'instagram')
            
            return {
                "success": True,
                "post_id": publish_data.get('id'),
                "platform": "instagram"
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', str(e))
                except:
                    pass
            
            return {
                "success": False,
                "error": f"Instagram API Error: {error_msg}",
                "platform": "instagram"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "platform": "instagram"
            }
    
    
    def publish_to_facebook(
        self,
        client_id: int,
        message: str,
        link: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish post to Facebook Page using Meta Graph API
        
        Args:
            client_id: Client ID
            message: Post message
            link: URL to share
            image_url: Image URL
        
        Returns:
            Dict with post_id and status
        """
        try:
            # Get credentials
            credentials = self.get_client_credentials(client_id, 'facebook')
            if not credentials:
                return {
                    "success": False,
                    "error": "Facebook page not connected. Please connect your page first."
                }
            
            access_token = credentials['access_token']
            page_id = credentials['platform_account_id']
            
            url = f"{self.meta_graph_url}/{page_id}/feed"
            
            params = {
                "message": message,
                "access_token": access_token
            }
            
            if link:
                params["link"] = link
            
            if image_url:
                # For image posts, use /photos endpoint instead
                url = f"{self.meta_graph_url}/{page_id}/photos"
                params["url"] = image_url
            
            response = requests.post(url, data=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Update last_used_at
            self._update_account_last_used(client_id, 'facebook')
            
            return {
                "success": True,
                "post_id": data.get('id') or data.get('post_id'),
                "platform": "facebook"
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', str(e))
                except:
                    pass
            
            return {
                "success": False,
                "error": f"Facebook API Error: {error_msg}",
                "platform": "facebook"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "platform": "facebook"
            }
    
    
    # ========== LINKEDIN ==========
    
    def publish_to_linkedin(
        self,
        client_id: int,
        text: str,
        image_url: Optional[str] = None,
        article_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish post to LinkedIn using LinkedIn Marketing API
        
        Args:
            client_id: Client ID
            text: Post text
            image_url: Optional image URL
            article_link: Optional article URL
        
        Returns:
            Dict with post_id and status
        """
        try:
            # Get credentials
            credentials = self.get_client_credentials(client_id, 'linkedin')
            if not credentials:
                return {
                    "success": False,
                    "error": "LinkedIn account not connected. Please connect your account first."
                }
            
            access_token = credentials['access_token']
            author_urn = credentials['platform_account_id']  # Format: urn:li:person:XXXX or urn:li:organization:XXXX
            
            url = f"{self.linkedin_api_url}/ugcPosts"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            post_data = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Add article link if provided
            if article_link:
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                    {
                        "status": "READY",
                        "originalUrl": article_link
                    }
                ]
            
            # Note: Image upload to LinkedIn requires additional steps (register upload, upload image, reference in post)
            # This is a simplified version for text/link posts
            
            response = requests.post(url, headers=headers, json=post_data, timeout=30)
            response.raise_for_status()
            
            # LinkedIn returns the post URN in the headers or response
            post_id = response.headers.get('X-RestLi-Id') or response.json().get('id', 'unknown')
            
            # Update last_used_at
            self._update_account_last_used(client_id, 'linkedin')
            
            return {
                "success": True,
                "post_id": post_id,
                "platform": "linkedin"
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', str(e))
                except:
                    pass
            
            return {
                "success": False,
                "error": f"LinkedIn API Error: {error_msg}",
                "platform": "linkedin"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "platform": "linkedin"
            }
    
    
    # ========== TWITTER/X ==========
    
    def publish_to_twitter(
        self,
        client_id: int,
        text: str,
        media_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Publish tweet to Twitter/X using Twitter API v2
        
        Args:
            client_id: Client ID
            text: Tweet text (max 280 characters)
            media_ids: List of media IDs (pre-uploaded)
        
        Returns:
            Dict with post_id and status
        """
        try:
            # Get credentials
            credentials = self.get_client_credentials(client_id, 'twitter')
            if not credentials:
                return {
                    "success": False,
                    "error": "Twitter account not connected. Please connect your account first."
                }
            
            access_token = credentials['access_token']
            
            url = f"{self.twitter_api_url}/tweets"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            tweet_data = {
                "text": text[:280]  # Twitter character limit
            }
            
            if media_ids:
                tweet_data["media"] = {"media_ids": media_ids}
            
            response = requests.post(url, headers=headers, json=tweet_data, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Update last_used_at
            self._update_account_last_used(client_id, 'twitter')
            
            return {
                "success": True,
                "post_id": data.get('data', {}).get('id'),
                "platform": "twitter"
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('detail', str(e))
                except:
                    pass
            
            return {
                "success": False,
                "error": f"Twitter API Error: {error_msg}",
                "platform": "twitter"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "platform": "twitter"
            }
    
    
    # ========== PINTEREST ==========
    
    def publish_to_pinterest(
        self,
        client_id: int,
        title: str,
        description: str,
        board_id: str,
        image_url: str,
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish pin to Pinterest using Pinterest API
        
        Args:
            client_id: Client ID
            title: Pin title
            description: Pin description
            board_id: Pinterest board ID
            image_url: Image URL
            link: Optional destination link
        
        Returns:
            Dict with post_id and status
        """
        try:
            # Get credentials
            credentials = self.get_client_credentials(client_id, 'pinterest')
            if not credentials:
                return {
                    "success": False,
                    "error": "Pinterest account not connected. Please connect your account first."
                }
            
            access_token = credentials['access_token']
            
            url = f"{self.pinterest_api_url}/pins"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            pin_data = {
                "board_id": board_id,
                "title": title,
                "description": description,
                "media_source": {
                    "source_type": "image_url",
                    "url": image_url
                }
            }
            
            if link:
                pin_data["link"] = link
            
            response = requests.post(url, headers=headers, json=pin_data, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Update last_used_at
            self._update_account_last_used(client_id, 'pinterest')
            
            return {
                "success": True,
                "post_id": data.get('id'),
                "platform": "pinterest"
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', str(e))
                except:
                    pass
            
            return {
                "success": False,
                "error": f"Pinterest API Error: {error_msg}",
                "platform": "pinterest"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "platform": "pinterest"
            }
    
    
    # ========== UNIFIED PUBLISHING ==========
    
    def publish_to_platform(
        self,
        client_id: int,
        platform: str,
        caption: str,
        media_urls: List[str],
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Unified method to publish to any platform
        
        Args:
            client_id: Client ID
            platform: Platform name (instagram, facebook, linkedin, twitter, pinterest)
            caption: Post caption/text
            media_urls: List of media URLs
            additional_data: Platform-specific additional data
        
        Returns:
            Dict with success status and post_id
        """
        additional_data = additional_data or {}
        
        # Get first media URL if available
        image_url = media_urls[0] if media_urls else None
        
        if platform == 'instagram':
            return self.publish_to_instagram(
                client_id=client_id,
                caption=caption,
                image_url=image_url
            )
        
        elif platform == 'facebook':
            return self.publish_to_facebook(
                client_id=client_id,
                message=caption,
                image_url=image_url,
                link=additional_data.get('link')
            )
        
        elif platform == 'linkedin':
            return self.publish_to_linkedin(
                client_id=client_id,
                text=caption,
                image_url=image_url,
                article_link=additional_data.get('link')
            )
        
        elif platform == 'twitter':
            return self.publish_to_twitter(
                client_id=client_id,
                text=caption,
                media_ids=additional_data.get('media_ids', [])
            )
        
        elif platform == 'pinterest':
            board_id = additional_data.get('board_id')
            if not board_id:
                return {
                    "success": False,
                    "error": "Pinterest requires board_id in additional_data"
                }
            
            return self.publish_to_pinterest(
                client_id=client_id,
                title=caption[:100],  # Pinterest title limit
                description=caption,
                board_id=board_id,
                image_url=image_url,
                link=additional_data.get('link')
            )
        
        else:
            return {
                "success": False,
                "error": f"Unsupported platform: {platform}"
            }
    
    
    # ========== HELPER METHODS ==========
    
    def _update_account_last_used(self, client_id: int, platform: str):
        """Update last_used_at timestamp for an account"""
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE social_media_accounts
                SET last_used_at = CURRENT_TIMESTAMP
                WHERE client_id = %s AND platform = %s
            """, (client_id, platform))
            
            connection.commit()
        except:
            pass
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    
    def get_connected_accounts(self, client_id: int) -> List[Dict[str, Any]]:
        """
        Get all connected social media accounts for a client
        
        Returns:
            List of connected accounts with details
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            cursor.execute("""
                SELECT 
                    account_id,
                    platform,
                    platform_account_id,
                    platform_account_name,
                    is_active,
                    connected_at,
                    last_used_at
                FROM social_media_accounts
                WHERE client_id = %s
                ORDER BY platform, connected_at DESC
            """, (client_id,))
            
            accounts = cursor.fetchall()
            return accounts or []
            
        except Exception as e:
            print(f"Error getting connected accounts: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()