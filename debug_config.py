# debug_config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Environment Variables (Raw) ===")
for key in ['MONGO_URI', 'REDIS_PORT', 'REDIS_URL', 'JWT_SECRET']:
    value = os.getenv(key, 'NOT SET')
    if key == 'JWT_SECRET' and value != 'NOT SET':
        value = '***HIDDEN***'
    print(f"{key}: {value}")

# Try loading settings
print("\n=== Loading Pydantic Settings ===")
try:
    from app.utils.config import settings
    print("✅ Settings loaded successfully!")
    print(f"MONGO_URI: {settings.MONGO_URI}")
    print(f"REDIS_URL: {settings.REDIS_URL}")
    print(f"JWT_SECRET: {'***HIDDEN***' if settings.JWT_SECRET else 'NOT SET'}")
except Exception as e:
    print(f"❌ Settings error: {e}")

# Test imports
print("\n=== Testing Critical Imports ===")
try:
    from app.dependencies import get_database, get_redis
    print("✅ Dependencies imported successfully")
except Exception as e:
    print(f"❌ Dependencies error: {e}")

try:
    from jose import jwt
    print("✅ JWT (python-jose) imported successfully")
except Exception as e:
    print(f"❌ JWT error: {e}")

try:
    import bcrypt
    print("✅ bcrypt imported successfully")
except Exception as e:
    print(f"❌ bcrypt error: {e}")

print("\n=== File Check ===")
print(f".env exists: {os.path.exists('.env')}")
print(f"app/utils/config.py exists: {os.path.exists('app/utils/config.py')}")
print(f"app/dependencies.py exists: {os.path.exists('app/dependencies.py')}")