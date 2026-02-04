
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import youtube_upload

def setup():
    print("🎬 YouTube Auth Setup")
    print("---------------------")
    print("This script will help you authenticate with YouTube and save your credentials.")
    print("Ensure you have placed 'client_secrets.json' in the 'mylori/api' folder.")
    
    secrets_file = 'api/client_secrets.json'
    token_file = 'api/token.pickle'
    
    if not os.path.exists(secrets_file):
        print(f"❌ Error: {secrets_file} not found!")
        print("Please download it from Google Cloud Console and save it as 'api/client_secrets.json'.")
        return

    try:
        print("Opening browser for authentication...")
        service = youtube_upload.get_authenticated_service(secrets_file, token_file)
        if service:
            print(f"✅ Authentication successful! Token saved to {token_file}")
            
            # Optional: Test listing channels
            request = service.channels().list(mine=True, part='snippet')
            response = request.execute()
            if 'items' in response:
                channel = response['items'][0]['snippet']
                print(f"Authorized for Channel: {channel['title']}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")

if __name__ == "__main__":
    setup()
