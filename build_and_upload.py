#!/usr/bin/env python
"""
Build and upload bensilence to PyPI.

This script helps you build distribution files and upload them to PyPI.

Requirements:
- pip install build twine

Usage:
1. Make sure you have a PyPI account at https://pypi.org/
2. Generate an API token from your PyPI account settings
3. Run this script or follow the manual steps below
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:")
        print(e.stderr)
        return False

def main():
    """Main build and upload process."""
    print("🚀 Building and uploading bensilence to PyPI")
    print("=" * 50)

    # Check if we're in the right directory
    if not os.path.exists("setup.py") and not os.path.exists("pyproject.toml"):
        print("❌ Error: Not in the bensilence package directory!")
        print("Please run this script from the bensilence folder.")
        sys.exit(1)

    # Clean previous builds
    if os.path.exists("dist"):
        run_command("rmdir /s /q dist", "Cleaning previous builds")

    if os.path.exists("build"):
        run_command("rmdir /s /q build", "Cleaning build directory")

    # Build distributions
    if not run_command("python -m build", "Building distribution files"):
        sys.exit(1)

    # Check what was built
    if os.path.exists("dist"):
        print("\n📦 Built files:")
        for file in os.listdir("dist"):
            print(f"  - {file}")
    else:
        print("❌ No dist directory created!")
        sys.exit(1)

    # Test upload to Test PyPI first (recommended)
    print("\n🧪 Testing upload to Test PyPI first...")
    print("This is recommended before uploading to real PyPI.")
    print("Run: python -m twine upload --repository testpypi dist/*")
    print("Then test install: pip install --index-url https://test.pypi.org/simple/ bensilence")

    # Real upload
    print("\n📤 Ready to upload to real PyPI!")
    print("Run: python -m twine upload dist/*")
    print("You'll be prompted for your PyPI username and password/API token.")

    # Ask user if they want to proceed
    response = input("\nDo you want to upload to PyPI now? (y/N): ").lower().strip()
    if response == 'y':
        if run_command("python -m twine upload dist/*", "Uploading to PyPI"):
            print("\n🎉 Successfully uploaded bensilence to PyPI!")
            print("Check your package at: https://pypi.org/project/bensilence/")
        else:
            print("\n❌ Upload failed. Check the error messages above.")
    else:
        print("\n📝 To upload later, run:")
        print("python -m twine upload dist/*")

if __name__ == "__main__":
    main()