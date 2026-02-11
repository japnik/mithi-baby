
import os
import sys
import pickle
from google.auth.transport.requests import Request

# Add backend to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from utils import youtube_upload

def verify_token():
    token_file = os.path.join(backend_dir, "auth", "token.pickle")
    if not os.path.exists(token_file):
        print(f"❌ Token file not found at {token_file}")
        return False
    
    try:
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
        
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Token expired, attempting refresh...")
            creds.refresh(Request())
            print("✅ Token refreshed successfully!")
            return True
        elif creds and creds.valid:
            print("✅ Token is valid.")
            return True
        else:
            print("❌ Token is invalid and could not be refreshed.")
            return False
    except Exception as e:
        print(f"❌ Error verifying token: {e}")
        return False

if __name__ == "__main__":
    if verify_token():
        print("🚀 Token check passed.")
        sys.exit(0)
    else:
        print("⚠️ Token check failed.")
        sys.exit(1)
