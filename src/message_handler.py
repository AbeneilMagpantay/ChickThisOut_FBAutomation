"""
Message Handler - Processes and replies to Facebook Messenger messages.
"""
import logging
from typing import Dict, List, Optional

from src.facebook_api import facebook_api
from src.ai_responder import ai_responder
from src.database import db_manager

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles Facebook Messenger message processing and replies."""
    
    def __init__(self):
        self.fb = facebook_api
        self.ai = ai_responder
        self.db = db_manager
        self.page_id = self.fb.page_id
    
    def process_all_messages(self) -> Dict[str, int]:
        """
        Process all unprocessed messages in conversations.
        
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            "conversations_checked": 0,
            "messages_found": 0,
            "new_messages": 0,
            "replies_sent": 0,
            "errors": 0
        }
        
        try:
            # Get recent conversations
            conversations = self.fb.get_conversations(limit=25)
            stats["conversations_checked"] = len(conversations)
            
            for conversation in conversations:
                conv_id = conversation.get("id")
                if not conv_id:
                    continue
                
                # Get messages in this conversation
                messages_data = conversation.get("messages", {}).get("data", [])
                if not messages_data:
                    messages_data = self.fb.get_conversation_messages(conv_id)
                
                stats["messages_found"] += len(messages_data)
                
                # Process only the most recent message from customer
                # (to avoid replying to old messages)
                latest_customer_message = self._get_latest_customer_message(messages_data)
                
                if latest_customer_message:
                    result = self._process_single_message(latest_customer_message, conv_id)
                    if result == "replied":
                        stats["replies_sent"] += 1
                        stats["new_messages"] += 1
                    elif result == "skipped":
                        pass
                    elif result == "new":
                        stats["new_messages"] += 1
                    elif result == "error":
                        stats["errors"] += 1
            
            self.db.log_activity("message_check", f"Checked {stats['conversations_checked']} conversations")
            logger.info(f"Message processing complete: {stats}")
            
        except Exception as e:
            logger.error(f"Error processing messages: {e}")
            stats["errors"] += 1
        
        return stats
    
    def _get_latest_customer_message(self, messages: List[Dict]) -> Optional[Dict]:
        """Get the most recent message from a customer (not from our page)."""
        for message in messages:
            from_info = message.get("from", {})
            from_id = from_info.get("id", "")
            
            # Skip messages from our own page
            if from_id != self.page_id:
                return message
        
        return None
    
    def _check_if_we_replied_after(self, messages: List[Dict], target_message_id: str) -> bool:
        """Check if we already replied after a specific message."""
        found_target = False
        
        for message in messages:
            msg_id = message.get("id")
            from_id = message.get("from", {}).get("id", "")
            
            if msg_id == target_message_id:
                found_target = True
                continue
            
            if found_target and from_id == self.page_id:
                # We sent a message after the target message
                return True
        
        return False
    
    def _process_single_message(self, message: Dict, conversation_id: str) -> str:
        """
        Process a single message.
        
        Returns:
            'replied' - Successfully replied
            'skipped' - Already processed
            'new' - New but not replied
            'error' - Error occurred
        """
        message_id = message.get("id")
        message_text = message.get("message", "")
        from_info = message.get("from", {})
        from_id = from_info.get("id", "")
        from_name = from_info.get("name", "Unknown")
        
        if not message_id:
            return "error"
        
        # Skip if already processed
        if self.db.is_message_processed(message_id):
            return "skipped"
        
        # Skip messages from our own page
        if from_id == self.page_id:
            self.db.mark_message_processed(
                message_id=message_id,
                conversation_id=conversation_id,
                message=message_text,
                from_name=from_name,
                from_id=from_id,
                replied=False,
                error="Skipped: Own page message"
            )
            return "new"
        
        # Skip empty messages
        if not message_text.strip():
            self.db.mark_message_processed(
                message_id=message_id,
                conversation_id=conversation_id,
                message=message_text,
                from_name=from_name,
                from_id=from_id,
                replied=False,
                error="Skipped: Empty message"
            )
            return "new"
        
        # Build conversation context (last few messages)
        conversation_context = self._build_conversation_context(conversation_id)
        
        # Generate AI response
        logger.info(f"Generating reply for message from {from_name}: '{message_text[:50]}...'")
        ai_response = self.ai.generate_message_reply(message_text, conversation_context)
        
        if not ai_response:
            self.db.mark_message_processed(
                message_id=message_id,
                conversation_id=conversation_id,
                message=message_text,
                from_name=from_name,
                from_id=from_id,
                replied=False,
                error="AI failed to generate response"
            )
            return "error"
        
        # Send the reply
        result = self.fb.send_message(from_id, ai_response)
        
        if result:
            self.db.mark_message_processed(
                message_id=message_id,
                conversation_id=conversation_id,
                message=message_text,
                from_name=from_name,
                from_id=from_id,
                our_reply=ai_response,
                replied=True
            )
            logger.info(f"✓ Replied to {from_name}'s message")
            return "replied"
        else:
            self.db.mark_message_processed(
                message_id=message_id,
                conversation_id=conversation_id,
                message=message_text,
                from_name=from_name,
                from_id=from_id,
                our_reply=ai_response,
                replied=False,
                error="Failed to send message via Facebook"
            )
            return "error"
    
    def _build_conversation_context(self, conversation_id: str, limit: int = 5) -> str:
        """Build context from recent messages in a conversation."""
        try:
            messages = self.fb.get_conversation_messages(conversation_id, limit=limit)
            
            context_lines = []
            for msg in reversed(messages):  # Oldest first
                from_name = msg.get("from", {}).get("name", "Unknown")
                text = msg.get("message", "")
                if text:
                    context_lines.append(f"{from_name}: {text}")
            
            return "\n".join(context_lines) if context_lines else ""
            
        except Exception as e:
            logger.error(f"Error building conversation context: {e}")
            return ""


# Singleton instance  
message_handler = MessageHandler()
