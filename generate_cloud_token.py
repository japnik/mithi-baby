
import pickle
import base64
import os

# Paths
TOKEN_PATH = "backend/auth/token.pickle"

def generate_b64_token():
    if not os.path.exists(TOKEN_PATH):
        print(f"❌ Error: {TOKEN_PATH} not found!")
        print("Please run 'python backend/utils/setup_youtube_auth.py' first to generate the token.")
        return

    try:
        with open(TOKEN_PATH, "rb") as token_file:
            token_data = token_file.read()
            # Verify it loads as pickle
            creds = pickle.loads(token_data)
            
            # Encode
            b64_token = base64.b64encode(token_data).decode('utf-8')
            
            print("\n✅ Token Encoded Successfully!")
            print("--------------------------------------------------")
            print("Copy the string below and paste it into your Google Cloud Run Environment Variables")
            print("Variable Name: YOUTUBE_TOKEN_B64")
            print("--------------------------------------------------")
            print(b64_token)
            print("--------------------------------------------------")
            
    except Exception as e:
        print(f"❌ Error processing token: {e}")

if __name__ == "__main__":
    generate_b64_token()
