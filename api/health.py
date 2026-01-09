"""
Health check endpoint for Vercel.
"""
from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    """Simple health check endpoint."""
    
    def do_GET(self):
        """Return health status."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        
        response = {
            "status": "healthy",
            "service": "ChickThisOut Facebook Bot",
            "version": "2.0.0"
        }
        
        self.wfile.write(json.dumps(response).encode())
