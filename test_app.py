#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_app():
    print("🧪 Testing DICOM Anonymizer Service...")
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from app.main import app
        from app.config import settings
        print(f"✅ All imports successful")
        print(f"🔧 DEV_MODE: {settings.DEV_MODE}")
        
        # Test FastAPI app
        print("🚀 Testing FastAPI app...")
        print(f"📋 App title: {app.title}")
        print(f"📋 App version: {app.version}")
        
        # List routes
        print("🛣️  Available routes:")
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = getattr(route, 'methods', ['GET'])
                print(f"  - {' '.join(methods)} {route.path}")
        
        # Test configuration
        print("⚙️  Configuration test:")
        print(f"  - Profiles path: {settings.PROFILES_PATH}")
        print(f"  - OSS endpoint: {settings.OSS_ENDPOINT}")
        
        # Test anonymizer
        print("🔒 Testing anonymizer...")
        from app.anonymizer import DicomAnonymizer
        anonymizer = DicomAnonymizer('default')
        print(f"  - Default profile loaded with {len(anonymizer.rules)} rules")
        
        print("✅ All tests passed! The application is ready to run.")
        print("\n🚀 To start the server, run:")
        print("   uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("\n📖 API Documentation will be available at:")
        print("   http://localhost:8000/docs")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app()
    sys.exit(0 if success else 1)
