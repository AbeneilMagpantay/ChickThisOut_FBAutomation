"""
Facebook Webhook Handler for Vercel Serverless
Handles verification and incoming events from Facebook.
"""
import os
import json
import hmac
import hashlib
import logging
from http.server import BaseHTTPRequestHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
FACEBOOK_VERIFY_TOKEN = os.getenv("FACEBOOK_VERIFY_TOKEN", "chickthisout_verify_2024")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify that the payload came from Facebook."""
    if not FACEBOOK_APP_SECRET:
        return True  # Skip verification if no secret set
    
    if not signature:
        return False
    
    try:
        # Facebook sends: sha256=<signature>
        expected = hmac.new(
            FACEBOOK_APP_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        received = signature.replace("sha256=", "")
        return hmac.compare_digest(expected, received)
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


def generate_ai_response(message: str) -> str:
    """Generate AI response using Gemini."""
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        system_prompt = """You are a friendly customer service assistant for ChickThisOut, a restaurant in Canada.
        
Guidelines:
- Be warm, professional, and helpful
- Restaurant hours: 11 AM - 8 PM daily
- If you don't know something, say you'll have someone get back to them
- Keep responses concise (1-3 sentences)
- Use emojis sparingly 😊🍗"""
        
        full_prompt = f"{system_prompt}\n\n---\n\nCustomer message: \"{message}\"\n\nWrite a friendly response:"
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=256,
            )
        )
        
        if response and response.text:
            return response.text.strip()
        return None
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        return None


def reply_to_comment(comment_id: str, message: str) -> bool:
    """Reply to a Facebook comment."""
    import requests
    
    url = f"https://graph.facebook.com/v18.0/{comment_id}/comments"
    params = {
        "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
        "message": message
    }
    
    try:
        response = requests.post(url, params=params, timeout=30)
        response.raise_for_status()
        logger.info(f"Replied to comment {comment_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to reply to comment: {e}")
        return False


def send_message(recipient_id: str, message: str) -> bool:
    """Send a message to a user."""
    import requests
    
    url = f"https://graph.facebook.com/v18.0/me/messages"
    params = {"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message},
        "messaging_type": "RESPONSE"
    }
    
    try:
        response = requests.post(url, params=params, json=data, timeout=30)
        response.raise_for_status()
        logger.info(f"Sent message to {recipient_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return False


def process_comment_event(entry: dict):
    """Process a comment event from Facebook."""
    changes = entry.get("changes", [])
    
    for change in changes:
        if change.get("field") == "feed":
            value = change.get("value", {})
            item = value.get("item")
            verb = value.get("verb")
            
            # Only process new comments (not edits or deletes)
            if item == "comment" and verb == "add":
                comment_id = value.get("comment_id")
                message = value.get("message", "")
                from_id = value.get("from", {}).get("id", "")
                
                # Don't reply to our own comments
                if from_id == FACEBOOK_PAGE_ID:
                    logger.info("Skipping own comment")
                    return
                
                if comment_id and message:
                    logger.info(f"Processing comment: {message[:50]}...")
                    
                    # Generate AI response
                    ai_response = generate_ai_response(message)
                    
                    if ai_response:
                        reply_to_comment(comment_id, ai_response)


def process_message_event(entry: dict):
    """Process a message event from Facebook Messenger."""
    messaging = entry.get("messaging", [])
    
    for event in messaging:
        sender_id = event.get("sender", {}).get("id", "")
        recipient_id = event.get("recipient", {}).get("id", "")
        message_data = event.get("message", {})
        
        # Don't process messages from self or echo messages
        if sender_id == FACEBOOK_PAGE_ID or message_data.get("is_echo"):
            return
        
        message_text = message_data.get("text", "")
        
        if message_text:
            logger.info(f"Processing message: {message_text[:50]}...")
            
            # Generate AI response
            ai_response = generate_ai_response(message_text)
            
            if ai_response:
                send_message(sender_id, ai_response)


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler for Facebook webhooks."""
    
    def do_GET(self):
        """Handle webhook verification from Facebook."""
        from urllib.parse import urlparse, parse_qs
        
        # Parse query parameters
        query = parse_qs(urlparse(self.path).query)
        
        mode = query.get("hub.mode", [None])[0]
        token = query.get("hub.verify_token", [None])[0]
        challenge = query.get("hub.challenge", [None])[0]
        
        if mode == "subscribe" and token == FACEBOOK_VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(challenge.encode())
        else:
            logger.warning(f"Webhook verification failed. Token: {token}")
            self.send_response(403)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Verification failed")
    
    def do_POST(self):
        """Handle incoming webhook events from Facebook."""
        try:
            # Read the request body
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            
            # Verify signature (optional but recommended)
            signature = self.headers.get("X-Hub-Signature-256", "")
            if FACEBOOK_APP_SECRET and not verify_signature(body, signature):
                logger.warning("Invalid signature")
                self.send_response(403)
                self.end_headers()
                return
            
            # Parse the event
            data = json.loads(body.decode("utf-8"))
            object_type = data.get("object")
            
            logger.info(f"Received webhook: {object_type}")
            
            # Process entries
            for entry in data.get("entry", []):
                if object_type == "page":
                    # Could be feed (comments) or messaging
                    if "changes" in entry:
                        process_comment_event(entry)
                    if "messaging" in entry:
                        process_message_event(entry)
            
            # Always return 200 quickly to Facebook
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            self.send_response(500)
            self.end_headers()
