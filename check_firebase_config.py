#!/usr/bin/env python3
"""Check Firebase configuration and provide setup instructions."""

import os
import sys

def check_firebase_config():
    """Check current Firebase configuration."""
    print("=" * 70)
    print("Firebase Configuration Check")
    print("=" * 70)
    
    # Try to load .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ .env file loader available")
    except ImportError:
        print("⚠ python-dotenv not installed (optional)")
    
    # Check environment variables
    project_id = os.getenv("FIREBASE_PROJECT_ID", "")
    credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    service_account_json_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_B64", "")
    
    print("\nCurrent Configuration:")
    print(f"  FIREBASE_PROJECT_ID: {project_id or 'Not set (using default: alzmate-8c68b)'}")
    print(f"  FIREBASE_CREDENTIALS_PATH: {credentials_path or 'Not set'}")
    print(f"  FIREBASE_SERVICE_ACCOUNT_JSON: {'Set' if service_account_json else 'Not set'}")
    print(f"  FIREBASE_SERVICE_ACCOUNT_JSON_B64: {'Set' if service_account_json_b64 else 'Not set'}")
    
    # Check if credentials file exists
    if credentials_path:
        if os.path.exists(credentials_path):
            print(f"  ✓ Credentials file exists at: {credentials_path}")
        else:
            print(f"  ✗ Credentials file NOT found at: {credentials_path}")
    
    # Determine which method is configured
    print("\n" + "=" * 70)
    print("Configuration Status:")
    print("=" * 70)
    
    if service_account_json_b64:
        print("✓ Method 1 (Recommended): FIREBASE_SERVICE_ACCOUNT_JSON_B64 is set")
        print("  This is the recommended method for cloud deployments.")
    elif service_account_json:
        print("✓ Method 2: FIREBASE_SERVICE_ACCOUNT_JSON is set")
        print("  This method works but is less secure for production.")
    elif credentials_path and os.path.exists(credentials_path):
        print("✓ Method 3: FIREBASE_CREDENTIALS_PATH points to existing file")
        print("  This method works for local development.")
    else:
        print("✗ NO FIREBASE CREDENTIALS CONFIGURED")
        print("\nThis is why you're getting the JWT signature error!")
        print("\n" + "=" * 70)
        print("SETUP INSTRUCTIONS:")
        print("=" * 70)
        print("\nYou need to set up Firebase credentials using ONE of these methods:\n")
        print("METHOD 1 (Recommended - Base64 encoded):")
        print("  1. Get your Firebase service account JSON file")
        print("  2. Encode it to base64:")
        print("     python encode_firebase_credentials.py path/to/service-account.json")
        print("  3. Set the environment variable:")
        print("     export FIREBASE_SERVICE_ACCOUNT_JSON_B64=\"<base64-string>\"")
        print("     (or add to .env file)")
        print("\nMETHOD 2 (Direct JSON string):")
        print("  1. Get your Firebase service account JSON file")
        print("  2. Set the environment variable with the JSON content:")
        print("     export FIREBASE_SERVICE_ACCOUNT_JSON='{\"type\":\"service_account\",...}'")
        print("     (or add to .env file)")
        print("\nMETHOD 3 (File path - local only):")
        print("  1. Place your service account JSON file in the project")
        print("  2. Set the environment variable:")
        print("     export FIREBASE_CREDENTIALS_PATH=\"/path/to/service-account.json\"")
        print("     (or add to .env file)")
        print("\nFor detailed instructions, see: FIREBASE_CREDENTIALS_SETUP.md")
        return False
    
    # Test Firebase initialization
    print("\n" + "=" * 70)
    print("Testing Firebase Initialization:")
    print("=" * 70)
    try:
        from firebase_service import init_firebase
        print("Attempting to initialize Firebase...")
        client = init_firebase()
        print("✓ Firebase initialized successfully!")
        print("✓ Firestore client ready")
        return True
    except ValueError as e:
        print(f"✗ Firebase initialization failed:")
        print(f"  {str(e)}")
        print("\nPlease check your credentials and try again.")
        return False
    except Exception as e:
        print(f"✗ Unexpected error:")
        print(f"  {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_firebase_config()
    sys.exit(0 if success else 1)

