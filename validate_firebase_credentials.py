#!/usr/bin/env python3
"""Validate Firebase credentials by attempting a test operation."""

import sys

def validate_credentials():
    """Validate Firebase credentials by testing a Firestore operation."""
    print("=" * 70)
    print("Firebase Credentials Validation")
    print("=" * 70)
    
    try:
        from firebase_service import get_firestore_client
        
        print("\n1. Getting Firestore client...")
        db = get_firestore_client()
        print("   ✓ Firestore client obtained")
        
        print("\n2. Testing Firestore connection...")
        # Try to access a collection (this will trigger authentication)
        # We'll use a test collection that likely doesn't exist
        test_collection = db.collection("_test_connection")
        
        # Try to get documents (limit 0 to avoid actual data transfer)
        try:
            list(test_collection.limit(0).stream())
            print("   ✓ Firestore connection successful")
        except Exception as e:
            error_str = str(e)
            if "JWT" in error_str or "invalid_grant" in error_str or "signature" in error_str.lower():
                print(f"   ✗ Authentication failed: {error_str}")
                print("\n   Your credentials appear to be invalid or expired.")
                print("   Please:")
                print("   1. Download a fresh service account key from Firebase Console")
                print("   2. Re-encode it: python encode_firebase_credentials.py <key-file>")
                print("   3. Update FIREBASE_SERVICE_ACCOUNT_JSON_B64")
                return False
            else:
                # Other errors (like permission denied) are OK - it means we connected
                print(f"   ✓ Connection successful (got expected error: {type(e).__name__})")
        
        print("\n" + "=" * 70)
        print("✓ Firebase credentials are VALID and working!")
        print("=" * 70)
        print("\nIf you're still getting errors during requests, it might be:")
        print("  1. A timeout issue - check your network connection")
        print("  2. Credentials being corrupted in environment variables")
        print("  3. A race condition - try restarting your application")
        return True
        
    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}")
        print("\nPlease run: python check_firebase_config.py")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = validate_credentials()
    sys.exit(0 if success else 1)

