# config.py
import os
from typing import Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use system environment variables
    pass

# Firebase Configuration
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "alzmate-8c68b")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
FIREBASE_SERVICE_ACCOUNT_JSON_B64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_B64", "")

# Cloudinary Configuration (matching Flutter app)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "dkiqc4jru")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "659932293576982")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "1f7M0nZpCLZ1F7ytj1CYwaV2xo8")
CLOUDINARY_UPLOAD_PRESET = os.getenv("CLOUDINARY_UPLOAD_PRESET", "alzMate")

# Firestore Collections (matching Flutter app)
FIRESTORE_JOURNAL_ENTRIES_COLLECTION = "journal_entries"
FIRESTORE_EMOTION_ANALYSIS_COLLECTION = "emotion_analysis"  # Optional: separate collection for emotion data

# Port configuration (for Render.com and other cloud platforms)
PORT = int(os.getenv("PORT", "8000"))

