# app/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # OSS Credentials
    OSS_ACCESS_KEY_ID: str = os.getenv("OSS_ACCESS_KEY_ID")
    OSS_ACCESS_KEY_SECRET: str = os.getenv("OSS_ACCESS_KEY_SECRET")
    OSS_BUCKET_NAME: str = os.getenv("OSS_BUCKET_NAME")
    OSS_ENDPOINT: str = os.getenv("OSS_ENDPOINT")

    # Path to the profiles configuration file
    PROFILES_PATH: str = "app/profiles.yaml"

settings = Settings()

# Basic validation
if not all([settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET, settings.OSS_BUCKET_NAME, settings.OSS_ENDPOINT]):
    raise ValueError("One or more OSS environment variables are not set. Please check your .env file.")

