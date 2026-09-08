# app/test.py
import sys
import os

print("=" * 50)
print("Testing environment...")
print("=" * 50)

# Check Python version
print(f"Python version: {sys.version}")

# Check current directory
print(f"Current directory: {os.getcwd()}")

# Check files in current directory
print("Files in current directory:")
for file in os.listdir('.'):
    print(f"  - {file}")

# Check if .env exists
if os.path.exists('.env'):
    print("✅ .env file found")
else:
    print("❌ .env file NOT found")

# Try importing aiogram
try:
    from aiogram import Bot
    print("✅ aiogram imported successfully")
except Exception as e:
    print(f"❌ Failed to import aiogram: {e}")

print("=" * 50)
print("Test completed!")
print("=" * 50)
