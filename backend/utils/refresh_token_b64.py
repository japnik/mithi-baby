import base64
import os
import sys

def get_b64_token():
    # Define path to token.pickle
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    token_file = os.path.join(base_dir, 'auth', 'token.pickle')

    if not os.path.exists(token_file):
        print(f"❌ Error: {token_file} not found!")
        print("Run 'python3 backend/utils/setup_youtube_auth.py' first to generate it.")
        return

    with open(token_file, 'rb') as f:
        token_b64 = base64.b64encode(f.read()).decode('utf-8')
        print("\n" + "="*50)
        print("🚀 YOUR PRODUCTION TOKEN (YOUTUBE_TOKEN_B64):")
        print("="*50)
        print(token_b64)
        print("="*50 + "\n")

if __name__ == "__main__":
    get_b64_token()
