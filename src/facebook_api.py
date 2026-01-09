"""
Facebook Graph API Integration for ChickThisOut
Handles all Facebook API interactions for comments and messages.
"""
import requests
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

from config.settings import (
    FACEBOOK_GRAPH_API_URL,
    FACEBOOK_PAGE_ID,
    FACEBOOK_PAGE_ACCESS_TOKEN,
)

logger = logging.getLogger(__name__)


class FacebookAPI:
    """Facebook Graph API wrapper for page management."""
    
    def __init__(self):
        self.base_url = FACEBOOK_GRAPH_API_URL
        self.page_id = FACEBOOK_PAGE_ID
        self.access_token = FACEBOOK_PAGE_ACCESS_TOKEN
        
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make a request to the Facebook Graph API."""
        url = f"{self.base_url}/{endpoint}"
        
        # Always include access token
        if params is None:
            params = {}
        params["access_token"] = self.access_token
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, params=params, json=data, timeout=30)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            # Show the actual error from Facebook
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", {}).get("message", str(e))
                logger.error(f"Facebook API error: {error_msg}")
            except:
                logger.error(f"Facebook API request failed: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Facebook API request failed: {e}")
            return None
    
    # ==================== COMMENTS ====================
    
    def get_page_posts(self, limit: int = 25) -> List[Dict]:
        """Get recent posts from the page."""
        endpoint = f"{self.page_id}/posts"
        params = {
            "fields": "id,message,created_time,comments.limit(100){id,message,from,created_time,is_hidden}",
            "limit": limit
        }
        
        result = self._make_request("GET", endpoint, params)
        if result and "data" in result:
            return result["data"]
        return []
    
    def get_post_comments(self, post_id: str, limit: int = 100) -> List[Dict]:
        """Get comments on a specific post."""
        endpoint = f"{post_id}/comments"
        params = {
            "fields": "id,message,from,created_time,is_hidden,parent",
            "limit": limit,
            "filter": "stream"  # Get all comments including replies
        }
        
        result = self._make_request("GET", endpoint, params)
        if result and "data" in result:
            return result["data"]
        return []
    
    def reply_to_comment(self, comment_id: str, message: str) -> Optional[Dict]:
        """Reply to a comment."""
        endpoint = f"{comment_id}/comments"
        data = {"message": message}
        
        result = self._make_request("POST", endpoint, data=data)
        if result:
            logger.info(f"Successfully replied to comment {comment_id}")
        return result
    
    def get_comment_replies(self, comment_id: str) -> List[Dict]:
        """Get replies to a specific comment."""
        endpoint = f"{comment_id}/comments"
        params = {"fields": "id,message,from,created_time"}
        
        result = self._make_request("GET", endpoint, params)
        if result and "data" in result:
            return result["data"]
        return []
    
    # ==================== MESSAGES ====================
    
    def get_conversations(self, limit: int = 25) -> List[Dict]:
        """Get page conversations (message threads)."""
        endpoint = f"{self.page_id}/conversations"
        params = {
            "fields": "id,participants,messages.limit(10){id,message,from,created_time}",
            "limit": limit
        }
        
        result = self._make_request("GET", endpoint, params)
        if result and "data" in result:
            return result["data"]
        return []
    
    def get_conversation_messages(self, conversation_id: str, limit: int = 25) -> List[Dict]:
        """Get messages in a conversation."""
        endpoint = f"{conversation_id}/messages"
        params = {
            "fields": "id,message,from,created_time",
            "limit": limit
        }
        
        result = self._make_request("GET", endpoint, params)
        if result and "data" in result:
            return result["data"]
        return []
    
    def send_message(self, recipient_id: str, message: str) -> Optional[Dict]:
        """Send a message to a user."""
        endpoint = f"{self.page_id}/messages"
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message},
            "messaging_type": "RESPONSE"
        }
        
        result = self._make_request("POST", endpoint, data=data)
        if result:
            logger.info(f"Successfully sent message to {recipient_id}")
        return result
    
    def reply_to_conversation(self, conversation_id: str, message: str) -> Optional[Dict]:
        """Reply to a conversation thread."""
        endpoint = f"{conversation_id}/messages"
        data = {"message": message}
        
        result = self._make_request("POST", endpoint, data=data)
        if result:
            logger.info(f"Successfully replied to conversation {conversation_id}")
        return result
    
    # ==================== PAGE INFO ====================
    
    def get_page_info(self) -> Optional[Dict]:
        """Get information about the page."""
        endpoint = self.page_id
        params = {"fields": "id,name,about,category,fan_count"}
        
        return self._make_request("GET", endpoint, params)
    
    def verify_token(self) -> bool:
        """Verify that the access token is valid."""
        try:
            # Use 'me' endpoint - for page tokens this returns the page info
            url = f"{self.base_url}/me"
            params = {
                "fields": "id,name",
                "access_token": self.access_token
            }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            info = response.json()
            
            if info and "id" in info:
                # Update page_id to match the token's page
                actual_page_id = info.get("id")
                page_name = info.get("name", "Unknown")
                
                if self.page_id != actual_page_id:
                    logger.warning(f"Page ID mismatch! .env has '{self.page_id}' but token is for '{actual_page_id}'")
                    logger.info(f"Auto-correcting to use page ID: {actual_page_id}")
                    self.page_id = actual_page_id
                
                logger.info(f"Token verified for page: {page_name} (ID: {actual_page_id})")
                return True
            return False
        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", {}).get("message", str(e))
                logger.error(f"Token verification failed: {error_msg}")
            except:
                logger.error(f"Token verification failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return False


# Singleton instance
facebook_api = FacebookAPI()
