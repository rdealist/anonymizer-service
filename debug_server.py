#!/usr/bin/env python3

import sys
import os
import asyncio

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔧 Debug Server Starting...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

try:
    print("📦 Importing app...")
    from app.main import app
    print("✅ App imported successfully")
    
    print("📦 Importing uvicorn...")
    import uvicorn
    print("✅ Uvicorn imported successfully")
    
    print("🚀 Starting server on http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    
    # Run with minimal configuration
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8000,
        log_level="debug",
        access_log=True
    )
    server = uvicorn.Server(config)
    
    print("🔄 Server configured, starting...")
    asyncio.run(server.serve())
    
except KeyboardInterrupt:
    print("\n🛑 Server stopped by user")
except Exception as e:
    print(f"❌ Error starting server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
