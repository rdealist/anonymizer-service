#!/usr/bin/env python3

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 Starting DICOM Anonymizer Service...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
