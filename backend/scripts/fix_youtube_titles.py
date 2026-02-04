import os
import sys
from dotenv import load_dotenv

# Add current dir to path for utils
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
from utils import youtube_upload

def fix_title(video_id, baby_name, ai_title, language="Punjabi", occasion="Lori"):
    print(f"🔧 Fixing title for {video_id} ({baby_name})...")
    
    # Standard format: "Name — Personalized Lang Occasion | AI Title"
    occ = occasion if (occasion and occasion != 'SpecialSong') else 'Lori'
    display_title = f"{baby_name} — Personalized {language} {occ} | {ai_title}"
    if len(display_title) > 100:
        display_title = display_title[:97] + "..."
        
    try:
        youtube = youtube_upload.get_authenticated_service()
        
        # We need the full snippet to update it
        video_response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()
        
        if not video_response['items']:
            print(f"❌ Video {video_id} not found.")
            return

        snippet = video_response['items'][0]['snippet']
        snippet['title'] = display_title
        
        youtube.videos().update(
            part='snippet',
            body={
                'id': video_id,
                'snippet': snippet
            }
        ).execute()
        
        print(f"✅ Success! New title: {display_title}")
        
    except Exception as e:
        print(f"❌ Error fixing title: {e}")

if __name__ == "__main__":
    # 1. Liv Kaur
    fix_title(
        video_id="zha7qpFiQ18",
        baby_name="Liv Kaur",
        ai_title="ਲਿਵ ਕੌਰ ਦਾ ਖਾਸ ਗੀਤ"
    )

    # 2. Baani Kaur
    fix_title(
        video_id="l7ISWKEP-fk",
        baby_name="Baani Kaur",
        ai_title="ਬਾਣੀ ਕੌਰ ਦਾ ਖਾਸ ਗੀਤ: ਮਿੱਠੀ ਲੋਰੀ"
    )
