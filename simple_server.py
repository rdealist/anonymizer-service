#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    print("🚀 Starting DICOM Anonymizer Service on http://localhost:8000")
    print("⚠️  This is a development server. Use uvicorn for production.")
    
    # Simple test to see if the app is working
    print("✅ FastAPI app created successfully")
    print("📋 Available routes:")
    for route in app.routes:
        print(f"  - {route.path}")
    
    # Try to import uvicorn and run
    try:
        import uvicorn
        print("🔄 Starting uvicorn server...")
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)
