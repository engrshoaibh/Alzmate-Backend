#!/usr/bin/env python3
"""
Utility script to encode Firebase service account JSON to base64.

This script helps you prepare your Firebase credentials for use with
FIREBASE_SERVICE_ACCOUNT_JSON_B64 environment variable.

Usage:
    python encode_firebase_credentials.py <path_to_service_account.json>
    
    Or run interactively:
    python encode_firebase_credentials.py
"""

import base64
import json
import sys
import os


def encode_file_to_base64(file_path: str) -> str:
    """
    Encode a Firebase service account JSON file to base64.
    
    Args:
        file_path: Path to the service account JSON file
        
    Returns:
        Base64-encoded string
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Validate it's valid JSON
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file: {e}")
    
    # Encode to base64
    encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    return encoded


def main():
    """Main function to encode Firebase credentials."""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Interactive mode
        file_path = input("Enter path to Firebase service account JSON file: ").strip()
        # Remove quotes if present
        if (file_path.startswith('"') and file_path.endswith('"')) or \
           (file_path.startswith("'") and file_path.endswith("'")):
            file_path = file_path[1:-1]
    
    try:
        encoded = encode_file_to_base64(file_path)
        
        print("\n" + "="*70)
        print("Base64-encoded Firebase Service Account JSON:")
        print("="*70)
        print(encoded)
        print("="*70)
        print("\nSet this as your FIREBASE_SERVICE_ACCOUNT_JSON_B64 environment variable.")
        print("\nExample (bash/zsh):")
        print(f'  export FIREBASE_SERVICE_ACCOUNT_JSON_B64="{encoded}"')
        print("\nExample (PowerShell):")
        print(f'  $env:FIREBASE_SERVICE_ACCOUNT_JSON_B64="{encoded}"')
        print("\nExample (.env file):")
        print(f'  FIREBASE_SERVICE_ACCOUNT_JSON_B64={encoded}')
        print()
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

