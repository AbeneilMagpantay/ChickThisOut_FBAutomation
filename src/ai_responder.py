"""
AI Response Generator using Google Gemini
Generates contextual responses for ChickThisOut restaurant.
"""
import logging
from pathlib import Path
from typing import Optional

import google.generativeai as genai

from config.settings import GEMINI_API_KEY, GEMINI_MODEL, PROMPTS_DIR

logger = logging.getLogger(__name__)


class AIResponder:
    """Google Gemini-based AI responder for customer messages."""
    
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model_name = GEMINI_MODEL
        self.system_prompt = self._load_system_prompt()
        self.model = None
        self._initialize_model()
    
    def _load_system_prompt(self) -> str:
        """Load the restaurant system prompt from file."""
        prompt_file = PROMPTS_DIR / "restaurant_prompt.txt"
        
        try:
            if prompt_file.exists():
                return prompt_file.read_text(encoding="utf-8")
            else:
                logger.warning(f"Prompt file not found: {prompt_file}")
                return self._get_default_prompt()
        except Exception as e:
            logger.error(f"Error loading prompt file: {e}")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Return a default prompt if file is not available."""
        return """You are a friendly customer service assistant for ChickThisOut restaurant.
Be helpful, warm, and professional. If you don't know something, say you'll have someone get back to them."""
    
    def _initialize_model(self):
        """Initialize the Gemini model."""
        try:
            genai.configure(api_key=self.api_key)
            
            # Configure generation settings
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 256,
            }
            
            # Safety settings - allow normal conversation
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
            
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                safety_settings=safety_settings,
                system_instruction=self.system_prompt,
            )
            
            logger.info(f"Gemini model '{self.model_name}' initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.model = None
    
    def generate_response(
        self, 
        customer_message: str, 
        context: Optional[str] = None,
        message_type: str = "comment"
    ) -> Optional[str]:
        """
        Generate an AI response to a customer message.
        
        Args:
            customer_message: The customer's message/comment
            context: Optional context (e.g., previous messages in thread)
            message_type: Either 'comment' or 'message'
            
        Returns:
            Generated response string or None if failed
        """
        if not self.model:
            logger.error("Model not initialized, cannot generate response")
            return None
        
        try:
            # Build the prompt
            if message_type == "comment":
                prompt = f"A customer left this comment on our Facebook post:\n\n\"{customer_message}\"\n\nWrite a friendly response."
            else:
                prompt = f"A customer sent this message to our Facebook page:\n\n\"{customer_message}\"\n\nWrite a helpful response."
            
            # Add context if available
            if context:
                prompt = f"Previous context:\n{context}\n\n{prompt}"
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                generated_text = response.text.strip()
                
                # Clean up any quotes that might wrap the response
                if generated_text.startswith('"') and generated_text.endswith('"'):
                    generated_text = generated_text[1:-1]
                
                logger.info(f"Generated response for: '{customer_message[:50]}...'")
                return generated_text
            else:
                logger.warning("Empty response from Gemini")
                return None
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None
    
    def generate_comment_reply(self, comment_text: str, post_context: Optional[str] = None) -> Optional[str]:
        """Generate a reply specifically for a Facebook comment."""
        return self.generate_response(comment_text, context=post_context, message_type="comment")
    
    def generate_message_reply(self, message_text: str, conversation_context: Optional[str] = None) -> Optional[str]:
        """Generate a reply specifically for a Facebook message."""
        return self.generate_response(message_text, context=conversation_context, message_type="message")
    
    def test_connection(self) -> bool:
        """Test if the AI model is working."""
        try:
            response = self.generate_response("Hello, testing!", message_type="comment")
            return response is not None
        except Exception as e:
            logger.error(f"AI connection test failed: {e}")
            return False


# Singleton instance
ai_responder = AIResponder()
