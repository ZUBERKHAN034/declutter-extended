#!/bin/bash

# Exit on error
set -e

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build the application
# Use the macOS-native .icns asset (with proper Dock padding) instead of .ico
pyinstaller --name Zeno --windowed --onefile --icon=assets/Zeno.icns src/Zeno.py

# Create a DMG
mkdir -p build/macos
hdiutil create build/macos/Zeno.dmg -volname "Zeno" -srcfolder "dist/Zeno.app"
