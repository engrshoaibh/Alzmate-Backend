#!/usr/bin/env python3
"""
Script to fix transformers compatibility issues with boltuix/bert-emotion model.

This script helps resolve the "Could not import module 'BertForSequenceClassification'" error
that occurs with transformers 5.0.0 and certain models.
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ Success: {description}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {description}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    print("=" * 70)
    print("Transformers Compatibility Fix for boltuix/bert-emotion")
    print("=" * 70)
    
    print("\nThis script will attempt to fix the model loading issue.")
    print("The error 'Could not import module BertForSequenceClassification'")
    print("is often caused by transformers 5.0.0 compatibility issues.\n")
    
    response = input("Do you want to proceed? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    fixes = [
        {
            "description": "Option 1: Fix torch/torchvision compatibility + Downgrade transformers (Recommended)",
            "command": f"{sys.executable} -m pip install torch torchvision --upgrade --index-url https://download.pytorch.org/whl/cpu",
            "command2": f"{sys.executable} -m pip install 'transformers>=4.35.0,<5.0.0' --upgrade",
            "recommended": True
        },
        {
            "description": "Option 2: Reinstall torch and torchvision (fix compatibility)",
            "command": f"{sys.executable} -m pip uninstall torch torchvision -y",
            "command2": f"{sys.executable} -m pip install torch torchvision",
            "recommended": False
        },
        {
            "description": "Option 3: Downgrade transformers to 4.x only",
            "command": f"{sys.executable} -m pip install 'transformers>=4.35.0,<5.0.0' --upgrade",
            "recommended": False
        },
        {
            "description": "Option 4: Clear HuggingFace cache",
            "command": None,  # Will be handled separately
            "recommended": False
        }
    ]
    
    print("\nAvailable fixes:")
    for i, fix in enumerate(fixes, 1):
        marker = "★" if fix["recommended"] else " "
        print(f"{marker} {i}. {fix['description']}")
    
    choice = input("\nEnter your choice (1-4, or 'all' for recommended): ").strip().lower()
    
    if choice == '1' or choice == 'all':
        # Fix torch/torchvision and downgrade transformers
        print("\nThis will fix torch/torchvision compatibility and downgrade transformers.")
        success1 = run_command(
            fixes[0]["command"],
            "Upgrading torch and torchvision"
        )
        if success1:
            success2 = run_command(
                fixes[0]["command2"],
                "Downgrading transformers to 4.x"
            )
            if success2:
                print("\n✓ All fixes applied successfully!")
                print("  Please restart your application and try loading the model again.")
    
    if choice == '2':
        # Reinstall torch and torchvision
        print("\nThis will reinstall torch and torchvision to fix compatibility.")
        success1 = run_command(
            fixes[1]["command"],
            "Uninstalling torch and torchvision"
        )
        if success1:
            success2 = run_command(
                fixes[1]["command2"],
                "Reinstalling torch and torchvision"
            )
            if success2:
                print("\n✓ Torch and torchvision reinstalled successfully!")
                print("  Please restart your application and try loading the model again.")
    
    if choice == '3':
        # Downgrade transformers only
        success = run_command(
            fixes[2]["command"],
            "Downgrading transformers to 4.x"
        )
        if success:
            print("\n✓ Transformers downgraded successfully!")
            print("  Please restart your application and try loading the model again.")
    
    if choice == '4' or choice == 'all':
        # Clear cache
        cache_paths = [
            os.path.expanduser("~/.cache/huggingface"),
            os.path.expanduser("~/.cache/huggingface/hub"),
        ]
        
        print("\nClearing HuggingFace cache...")
        import shutil
        cleared = False
        for cache_path in cache_paths:
            if os.path.exists(cache_path):
                try:
                    # Only clear the specific model cache
                    model_cache = os.path.join(cache_path, "models--boltuix--bert-emotion")
                    if os.path.exists(model_cache):
                        shutil.rmtree(model_cache)
                        print(f"✓ Cleared cache for boltuix/bert-emotion")
                        cleared = True
                except Exception as e:
                    print(f"✗ Could not clear cache at {cache_path}: {e}")
        
        if not cleared:
            print("  No cache found to clear.")
        else:
            print("  Cache cleared. Please restart your application.")
    
    print("\n" + "=" * 70)
    print("Fix process completed!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Restart your application")
    print("2. Try making a request to the emotion analysis endpoint")
    print("3. The model should load successfully now")
    print("\nIf issues persist, check:")
    print("- Internet connection (model needs to download)")
    print("- Firewall settings")
    print("- Model availability: https://huggingface.co/boltuix/bert-emotion")

if __name__ == "__main__":
    main()

