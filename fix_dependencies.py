#!/usr/bin/env python3
"""
Fix dependency conflicts in the project.

Resolves:
1. torch/torchaudio version mismatch
2. transformers/optimum-onnx version conflict
3. transformers 5.0.0 compatibility issues
"""

import subprocess
import sys

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ Success")
        if result.stdout:
            print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed")
        if e.stderr:
            print(f"Error: {e.stderr.strip()}")
        return False

def main():
    print("=" * 70)
    print("Dependency Conflict Resolution")
    print("=" * 70)
    print("\nCurrent conflicts:")
    print("  1. torchaudio 2.7.0 requires torch==2.7.0, but you have torch 2.10.0")
    print("  2. optimum-onnx 0.1.0 requires transformers<4.58.0, but you have 5.0.0")
    print("  3. giotto-tda 0.6.2 requires scikit-learn==1.3.2, but you have 1.7.0")
    print("\nThis script will:")
    print("  - Remove optional packages (optimum-onnx, giotto-tda) not needed for emotion analysis")
    print("  - Fix torch/torchaudio compatibility")
    print("  - Downgrade transformers to 4.x (fixes both conflicts)")
    print()
    
    response = input("Proceed with fix? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    # Step 1: Remove optional packages (not needed for this project)
    print("\n" + "=" * 70)
    print("Step 1: Removing optional packages")
    print("=" * 70)
    run_command(
        f"{sys.executable} -m pip uninstall optimum-onnx optimum giotto-tda giotto-ph -y",
        "Removing optional packages (optimum-onnx, optimum, giotto-tda, giotto-ph)"
    )
    
    # Step 2: Fix torch/torchaudio compatibility
    print("\n" + "=" * 70)
    print("Step 2: Fixing torch/torchaudio compatibility")
    print("=" * 70)
    run_command(
        f"{sys.executable} -m pip uninstall torch torchaudio torchvision -y",
        "Uninstalling torch, torchaudio, and torchvision"
    )
    
    run_command(
        f"{sys.executable} -m pip install torch torchaudio torchvision",
        "Installing compatible versions of torch, torchaudio, and torchvision"
    )
    
    # Step 3: Downgrade transformers
    print("\n" + "=" * 70)
    print("Step 3: Downgrading transformers to 4.x")
    print("=" * 70)
    run_command(
        f"{sys.executable} -m pip install 'transformers>=4.35.0,<5.0.0' --upgrade",
        "Downgrading transformers to 4.x (fixes BertForSequenceClassification error)"
    )
    
    # Verify
    print("\n" + "=" * 70)
    print("Verifying installation")
    print("=" * 70)
    run_command(
        f"{sys.executable} -m pip check",
        "Checking for remaining conflicts"
    )
    
    print("\n" + "=" * 70)
    print("✓ Dependency conflicts resolved!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Restart your application:")
    print("     uvicorn main:app --host 127.0.0.1 --port 8000")
    print("  2. The app should start without errors")
    print("  3. Test the emotion analysis endpoint")

if __name__ == "__main__":
    main()

