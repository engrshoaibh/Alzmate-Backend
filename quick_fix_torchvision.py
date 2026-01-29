#!/usr/bin/env python3
"""Quick fix for torchvision compatibility issue."""

import subprocess
import sys

print("=" * 70)
print("Quick Fix for Torchvision Compatibility Issue")
print("=" * 70)
print("\nThis will reinstall torch and torchvision with compatible versions.")
print("Then downgrade transformers to avoid the BertForSequenceClassification error.\n")

response = input("Proceed? (y/n): ").strip().lower()
if response != 'y':
    print("Cancelled.")
    sys.exit(0)

commands = [
    ("Uninstalling torch and torchvision...", 
     f"{sys.executable} -m pip uninstall torch torchvision -y"),
    ("Installing compatible torch and torchvision...", 
     f"{sys.executable} -m pip install torch torchvision"),
    ("Downgrading transformers to 4.x...", 
     f"{sys.executable} -m pip install 'transformers>=4.35.0,<5.0.0' --upgrade"),
]

for desc, cmd in commands:
    print(f"\n{desc}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ Success")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e.stderr}")
        sys.exit(1)

print("\n" + "=" * 70)
print("✓ All fixes applied!")
print("=" * 70)
print("\nPlease restart your application:")
print("  uvicorn main:app --host 127.0.0.1 --port 8000")

