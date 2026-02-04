
import os
import datetime
import json
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes required for uploading
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Default paths relative to this file's directory
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
AUTH_DIR = os.path.join(os.path.dirname(BASE_PATH), "auth")
DEFAULT_SECRETS = os.path.join(AUTH_DIR, "client_secrets.json")
DEFAULT_TOKEN = os.path.join(AUTH_DIR, "token.pickle")

def get_authenticated_service(secrets_file=DEFAULT_SECRETS, token_file=DEFAULT_TOKEN):
    """
    Authenticate and return a YouTube service object.
    Supports Base64 encoded credentials via environment variables for cloud environments.
    """
    import base64
    import tempfile

    creds = None
    env_token = os.getenv("YOUTUBE_TOKEN_B64")
    env_secrets = os.getenv("YOUTUBE_SECRETS_B64")

    # 1. Try Token from Env
    if env_token:
        try:
            print("🔑 Using YouTube Token from environment variable")
            token_data = base64.b64decode(env_token)
            creds = pickle.loads(token_data)
        except Exception as e:
            print(f"⚠️ Failed to decode YOUTUBE_TOKEN_B64: {e}")

    # 2. Try Token from File if not in Env
    if not creds and os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # 3. Handle expired credentials
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # If we have a file path, update it locally. 
        # In cloud (Env mode), we just keep it in memory.
        if os.path.exists(token_file):
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

    # 4. Final Fallback/Initialization
    if not creds or not creds.valid:
        # If we have secrets in ENV, use a temporary file for the library
        if env_secrets:
            print("🔑 Using YouTube Secrets from environment variable")
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as tmp:
                tmp.write(base64.b64decode(env_secrets))
                tmp_secrets_path = tmp.name
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(tmp_secrets_path, SCOPES)
                creds = flow.run_local_server(port=0)
                os.unlink(tmp_secrets_path) # Clean up
            except Exception as e:
                if os.path.exists(tmp_secrets_path): os.unlink(tmp_secrets_path)
                raise e
        else:
            if not os.path.exists(secrets_file):
                raise FileNotFoundError(f"Client secrets file not found at: {secrets_file}")
                
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # For local use only: save the credentials for next run
        if os.path.exists(os.path.dirname(token_file)):
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

    return build('youtube', 'v3', credentials=creds)

def generate_description(baby_name, lyrics_text, language="Punjabi", occasion="Lori"):
    """
    Generates the dynamic description based on the provided template.
    """
    # Remove spaces for hashtag
    baby_name_tag = baby_name.replace(" ", "")
    
    template = f"""{baby_name}’s very own lori is here! ✨

Give your child the gift of heritage with a song that features their very own name. This {language} {occasion} was created especially for {baby_name} to bring peace, comfort, and the sweet sounds of home to bedtime.

🎵 About this Song: This melody is a soulful fusion of traditional Punjabi folk roots and soothing ambient sounds. Featuring a soft harmonium, gentle tabla, and motherly vocals, it is designed to help babies like {baby_name} drift into a deep, peaceful sleep while staying connected to their mother tongue.

📝 Lyrics for {baby_name} ({language}):

{lyrics_text}

👩👧 From the Founder: "I created Mithi Baby so my daughter Liv could grow up hearing her name in the beautiful melodies of our culture. I want to create a digital village where our children’s names and our traditions live forever. I hope this song brings as much peace to your home as it does to ours." — Liv’s Mom, Founder of Mithi Baby

You can generate a high-quality lori in seconds and have the option to share it on this YouTube channel with a single click to share with your family across the world.

✨ Create your own personalized lori at: https://mithi.baby

Join the Village: Subscribe for more personalized loris and traditional Punjabi & Hindi sleep music.

#MithiBaby #{baby_name_tag} #PunjabiLori #HindiLullaby #PersonalizedBabySongs #DesiParenting #BabySleepMusic #NewbornCare #PunjabiLullaby"""

    return template

def upload_video(file_path, title, description, privacy_status='public', secrets_file=DEFAULT_SECRETS, token_file=DEFAULT_TOKEN):
    """
    Standard upload function.
    """
    try:
        youtube = get_authenticated_service(secrets_file, token_file)

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['Mithi Baby', 'Lori', 'Punjabi Lullaby', 'Personalized Song'],
                'categoryId': '10' # Music
            },
            'status': {
                'privacyStatus': privacy_status,
                'madeForKids': True, 
                'selfDeclaredMadeForKids': True
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")

        print(f"Upload Complete! Video ID: {response['id']}")
        return {"status": "success", "video_id": response['id'], "video_url": f"https://youtu.be/{response['id']}"}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"status": "error", "message": str(e)}

def upload_to_youtube(video_path, ai_title, lyrics_text, baby_name=None, language="Punjabi", occasion="Lori", characters=None):
    """
    Branded wrapper used by both server and process_song.
    Format: [Name] — Personalized [Lang] [Occasion] ft. [Chars] ([Month Year]) | Mithi Baby
    """
    occ = occasion if (occasion and occasion != 'SpecialSong') else 'Lori'
    clean_name = baby_name or "Baby"
    
    # Format characters: "Mummy, Papa" -> "Mummy & Papa"
    char_str = ""
    if characters:
        if isinstance(characters, str):
            char_list = [c.strip() for c in characters.split(',') if c.strip()]
        else:
            char_list = characters
            
        if char_list:
            if len(char_list) > 1:
                char_str = f" ft. {', '.join(char_list[:-1])} & {char_list[-1]}"
            else:
                char_str = f" ft. {char_list[0]}"

    # Milestone suffix (Month Year)
    milestone = datetime.datetime.now().strftime("%b %Y")
    
    display_title = f"{clean_name} — Personalized {language} {occ}{char_str} ({milestone}) | Mithi Baby"

    
    # Cap title length at 100 for YT
    if len(display_title) > 100:
        display_title = display_title[:97] + "..."

    description = generate_description(clean_name, lyrics_text, language=language, occasion=occ)
    
    return upload_video(video_path, display_title, description, privacy_status='public')


if __name__ == '__main__':
    # Test run
    # upload_video('test.mp4', 'Test Video', 'Test Description')
    pass
