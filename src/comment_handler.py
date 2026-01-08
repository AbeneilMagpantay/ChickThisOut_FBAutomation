"""
Comment Handler - Processes and replies to Facebook comments.
"""
import logging
from typing import Optional, List, Dict

from src.facebook_api import facebook_api
from src.ai_responder import ai_responder
from src.database import db_manager

logger = logging.getLogger(__name__)


class CommentHandler:
    """Handles Facebook comment processing and replies."""
    
    def __init__(self):
        self.fb = facebook_api
        self.ai = ai_responder
        self.db = db_manager
        self.page_id = self.fb.page_id
    
    def process_all_comments(self) -> Dict[str, int]:
        """
        Process all unprocessed comments on recent posts.
        
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            "posts_checked": 0,
            "comments_found": 0,
            "new_comments": 0,
            "replies_sent": 0,
            "errors": 0
        }
        
        try:
            # Get recent posts
            posts = self.fb.get_page_posts(limit=10)
            stats["posts_checked"] = len(posts)
            
            for post in posts:
                post_id = post.get("id")
                if not post_id:
                    continue
                
                # Get comments on this post
                comments_data = post.get("comments", {}).get("data", [])
                if not comments_data:
                    # Try fetching comments directly
                    comments_data = self.fb.get_post_comments(post_id)
                
                stats["comments_found"] += len(comments_data)
                
                for comment in comments_data:
                    result = self._process_single_comment(comment, post_id)
                    if result == "replied":
                        stats["replies_sent"] += 1
                        stats["new_comments"] += 1
                    elif result == "skipped":
                        pass  # Already processed
                    elif result == "new":
                        stats["new_comments"] += 1
                    elif result == "error":
                        stats["errors"] += 1
            
            self.db.log_activity("comment_check", f"Checked {stats['posts_checked']} posts, {stats['comments_found']} comments")
            logger.info(f"Comment processing complete: {stats}")
            
        except Exception as e:
            logger.error(f"Error processing comments: {e}")
            stats["errors"] += 1
        
        return stats
    
    def _process_single_comment(self, comment: Dict, post_id: str) -> str:
        """
        Process a single comment.
        
        Returns:
            'replied' - Successfully replied
            'skipped' - Already processed
            'new' - New but not replied (e.g., from page itself)
            'error' - Error occurred
        """
        comment_id = comment.get("id")
        comment_text = comment.get("message", "")
        from_info = comment.get("from", {})
        from_id = from_info.get("id", "")
        from_name = from_info.get("name", "Unknown")
        
        if not comment_id:
            return "error"
        
        # Skip if already processed
        if self.db.is_comment_processed(comment_id):
            return "skipped"
        
        # Skip if comment is from our own page
        if from_id == self.page_id:
            self.db.mark_comment_processed(
                comment_id=comment_id,
                post_id=post_id,
                message=comment_text,
                from_name=from_name,
                from_id=from_id,
                replied=False,
                error="Skipped: Own page comment"
            )
            return "new"
        
        # Skip hidden comments
        if comment.get("is_hidden", False):
            self.db.mark_comment_processed(
                comment_id=comment_id,
                post_id=post_id,
                message=comment_text,
                from_name=from_name,
                from_id=from_id,
                replied=False,
                error="Skipped: Hidden comment"
            )
            return "new"
        
        # Skip empty comments
        if not comment_text.strip():
            self.db.mark_comment_processed(
                comment_id=comment_id,
                post_id=post_id,
                message=comment_text,
                from_name=from_name,
                from_id=from_id,
                replied=False,
                error="Skipped: Empty comment"
            )
            return "new"
        
        # Check if we already replied to this comment
        existing_replies = self.fb.get_comment_replies(comment_id)
        for reply in existing_replies:
            reply_from = reply.get("from", {}).get("id", "")
            if reply_from == self.page_id:
                # We already replied
                self.db.mark_comment_processed(
                    comment_id=comment_id,
                    post_id=post_id,
                    message=comment_text,
                    from_name=from_name,
                    from_id=from_id,
                    our_reply=reply.get("message", ""),
                    replied=True
                )
                return "skipped"
        
        # Generate AI response
        logger.info(f"Generating reply for comment from {from_name}: '{comment_text[:50]}...'")
        ai_response = self.ai.generate_comment_reply(comment_text)
        
        if not ai_response:
            self.db.mark_comment_processed(
                comment_id=comment_id,
                post_id=post_id,
                message=comment_text,
                from_name=from_name,
                from_id=from_id,
                replied=False,
                error="AI failed to generate response"
            )
            return "error"
        
        # Send the reply
        result = self.fb.reply_to_comment(comment_id, ai_response)
        
        if result:
            self.db.mark_comment_processed(
                comment_id=comment_id,
                post_id=post_id,
                message=comment_text,
                from_name=from_name,
                from_id=from_id,
                our_reply=ai_response,
                replied=True
            )
            logger.info(f"✓ Replied to {from_name}'s comment")
            return "replied"
        else:
            self.db.mark_comment_processed(
                comment_id=comment_id,
                post_id=post_id,
                message=comment_text,
                from_name=from_name,
                from_id=from_id,
                our_reply=ai_response,
                replied=False,
                error="Failed to post reply to Facebook"
            )
            return "error"


# Singleton instance
comment_handler = CommentHandler()
