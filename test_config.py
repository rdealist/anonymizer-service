#!/usr/bin/env python3

from app.config import settings

print(f"DEV_MODE: {settings.DEV_MODE}")
print(f"OSS_ACCESS_KEY_ID: {settings.OSS_ACCESS_KEY_ID}")
print(f"OSS_ACCESS_KEY_SECRET: {settings.OSS_ACCESS_KEY_SECRET}")
print(f"OSS_BUCKET_NAME: {settings.OSS_BUCKET_NAME}")
print(f"OSS_ENDPOINT: {settings.OSS_ENDPOINT}")
