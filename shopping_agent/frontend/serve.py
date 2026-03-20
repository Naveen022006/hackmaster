"""
Simple HTTP server to serve the frontend.
Run this alongside the API server.
"""
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Configuration
PORT = 3000
FRONTEND_DIR = Path(__file__).parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def run_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n{'='*50}")
        print(f"Frontend server running at: http://localhost:{PORT}")
        print(f"{'='*50}")
        print("\nMake sure the API server is running at http://localhost:8000")
        print("Start API server with: python main.py serve")
        print("\nPress Ctrl+C to stop the server")

        # Open browser
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            pass

        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
