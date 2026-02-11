import os
import sys
import pickle
import base64
from google_auth_oauthlib.flow import InstalledAppFlow

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def finish_auth():
    auth_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "auth")
    secrets_file = os.path.join(auth_dir, 'client_secrets.json')
    token_file = os.path.join(auth_dir, 'token.pickle')

    print("🔑 Manual YouTube Token Completion")
    print("--------------------------------")
    
    auth_url = "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=997989328753-trd3dvg7h6bee89ogn70roqr4n19ve7b.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A53048%2F&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube.upload&state=MVJYAeCEZ5Cm96m4egiYGbPf076Syt&access_type=offline"
    
    print("It looks like you already have the code from the URL.")
    code = input("\n👉 Paste the 'code' value here (the part after code= in your URL bar): ").strip()
    
    if not code:
        print("❌ Error: No code provided.")
        return

    try:
        flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
        # We need to use the exact SAME redirect URI as used in the initial request
        flow.redirect_uri = "http://localhost:53048/"
        
        print("Exchanging code for token...")
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Save locally
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
            
        print(f"✅ Token saved to {token_file}")
        
        # Print for production
        token_b64 = base64.b64encode(pickle.dumps(creds)).decode('utf-8')
        print("\n" + "="*50)
        print("🚀 YOUR PRODUCTION TOKEN (YOUTUBE_TOKEN_B64):")
        print("="*50)
        print(token_b64)
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"❌ Failed to exchange code: {e}")

if __name__ == "__main__":
    finish_auth()
