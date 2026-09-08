# app/test.py
import sys
import os

print("=" * 50)
print("🚀 Starting test...")
print("=" * 50)

# 1. Check Python version
print(f"✅ Python version: {sys.version}")

# 2. Check current directory
print(f"✅ Current directory: {os.getcwd()}")

# 3. List files
print("📁 Files in current directory:")
for file in os.listdir('.'):
    print(f"   - {file}")

# 4. Check if .env exists
env_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(env_path):
    print("✅ .env file found")
else:
    print("❌ .env file NOT found")

# 5. Try importing libraries
try:
    from aiogram import Bot
    print("✅ aiogram imported")
except Exception as e:
    print(f"❌ aiogram import failed: {e}")

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv imported")
except Exception as e:
    print(f"❌ python-dotenv import failed: {e}")

try:
    from sqlalchemy import create_engine
    print("✅ sqlalchemy imported")
except Exception as e:
    print(f"❌ sqlalchemy import failed: {e}")

print("=" * 50)
print("✅ Test completed!")
print("=" * 50)
