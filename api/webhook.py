"""
Facebook Webhook Handler for Vercel Serverless
Uses Flask for better Vercel compatibility.
"""
import os
import json
import hmac
import hashlib
import logging
from flask import Flask, request, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Environment variables
FACEBOOK_VERIFY_TOKEN = os.getenv("FACEBOOK_VERIFY_TOKEN", "chickthisout_verify_2024")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify that the payload came from Facebook."""
    if not FACEBOOK_APP_SECRET:
        return True
    if not signature:
        return False
    try:
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
            
            if item == "comment" and verb == "add":
                comment_id = value.get("comment_id")
                message = value.get("message", "")
                from_id = value.get("from", {}).get("id", "")
                
                if from_id == FACEBOOK_PAGE_ID:
                    return
                
                if comment_id and message:
                    logger.info(f"Processing comment: {message[:50]}...")
                    ai_response = generate_ai_response(message)
                    if ai_response:
                        reply_to_comment(comment_id, ai_response)


def process_message_event(entry: dict):
    """Process a message event from Facebook Messenger."""
    messaging = entry.get("messaging", [])
    
    for event in messaging:
        sender_id = event.get("sender", {}).get("id", "")
        message_data = event.get("message", {})
        
        if sender_id == FACEBOOK_PAGE_ID or message_data.get("is_echo"):
            return
        
        message_text = message_data.get("text", "")
        
        if message_text:
            logger.info(f"Processing message: {message_text[:50]}...")
            ai_response = generate_ai_response(message_text)
            if ai_response:
                send_message(sender_id, ai_response)


@app.route("/api/webhook", methods=["GET"])
def verify_webhook():
    """Handle webhook verification from Facebook."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    logger.info(f"Verification attempt - mode: {mode}, token: {token}")
    
    if mode == "subscribe" and token == FACEBOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return challenge, 200
    else:
        logger.warning(f"Verification failed. Expected: {FACEBOOK_VERIFY_TOKEN}, Got: {token}")
        return "Verification failed", 403


@app.route("/api/webhook", methods=["POST"])
def handle_webhook():
    """Handle incoming webhook events from Facebook."""
    try:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if FACEBOOK_APP_SECRET and not verify_signature(request.data, signature):
            return "Invalid signature", 403
        
        data = request.get_json()
        object_type = data.get("object")
        
        logger.info(f"Received webhook: {object_type}")
        
        for entry in data.get("entry", []):
            if object_type == "page":
                if "changes" in entry:
                    process_comment_event(entry)
                if "messaging" in entry:
                    process_message_event(entry)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/privacy", methods=["GET"])
@app.route("/api/privacy", methods=["GET"])
def privacy():
    """Privacy Policy page."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Privacy Policy - ChickThisOut</title></head>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
        <h1>Privacy Policy</h1>
        <p><strong>ChickThisOut Facebook Bot</strong></p>
        <p>Last updated: January 2026</p>
        
        <h2>Information We Collect</h2>
        <p>This bot only processes messages and comments sent to our Facebook Page to provide automated customer service responses.</p>
        
        <h2>How We Use Information</h2>
        <p>Messages are processed in real-time to generate helpful responses. We do not store personal data permanently.</p>
        
        <h2>Data Sharing</h2>
        <p>We do not sell or share your personal information with third parties.</p>
        
        <h2>Contact</h2>
        <p>For questions, contact us through our Facebook Page: Chick This Out</p>
    </body>
    </html>
    """, 200, {'Content-Type': 'text/html'}


@app.route("/", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "ChickThisOut Facebook Bot",
        "version": "2.0.0"
    })


# For local testing
if __name__ == "__main__":
    app.run(debug=True, port=3000)
