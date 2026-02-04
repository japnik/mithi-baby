
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
    Uses a pickle file to store credentials for subsequent runs.
    """

    creds = None
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(secrets_file):
                raise FileNotFoundError(f"Client secrets file not found at: {secrets_file}")
                
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
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

We are opening the doors very soon! Once we launch, you can generate a high-quality lori in seconds and post it directly to this channel with a single click to share with your family across the world.

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
