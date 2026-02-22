"""
Vercel entrypoint — imports the FastAPI app from tools/api_server.py
"""

import sys
import os

# Add tools directory to path so imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from api_server import app
