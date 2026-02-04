import os
import json
import time
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Add current dir to path for utils
# We need to be in 'backend' for imports to work as expected if we use 'backend/utils'
# But actually 'process_song.py' is in 'backend' and does 'from utils import ...'
# So if we run from 'backend' dir, it works.

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import notifier, youtube_upload

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def rescue_song(song_id, baby_name, user_email, video_path_rel, title, lyrics_path_rel):
    print(f"\n🚀 Rescuing song {song_id} ({baby_name})...")
    
    # Absolute paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(base_dir, video_path_rel)
    lyrics_json_path = os.path.join(base_dir, lyrics_path_rel.replace(".txt", ".json")) # Assuming .json exists
    
    # Check if video exists
    if not os.path.exists(video_path):
        print(f"❌ Video not found at {video_path}")
        return

    # Try to get full lyrics from text file or json
    lyrics_text = ""
    txt_path = os.path.join(base_dir, lyrics_path_rel)
    if os.path.exists(txt_path):
        with open(txt_path, 'r') as f:
            lyrics_text = f.read()
    
    youtube_url = None
    print("🎥 Preparing YouTube Upload...")
    description = youtube_upload.generate_description(baby_name, lyrics_text)
    yt_result = youtube_upload.upload_video(video_path, title, description)
    
    if yt_result and yt_result.get('status') == 'success':
        youtube_url = yt_result['video_url']
        print(f"✅ YouTube Upload Success: {youtube_url}")
        # Update DB
        supabase.table("songs").update({"youtube_url": youtube_url}).eq("id", song_id).execute()
    else:
        print(f"⚠️ YouTube Upload failed: {yt_result.get('message') if yt_result else 'Unknown error'}")

    if user_email:
        print(f"📧 Sending completion email to {user_email}...")
        
        # Public video URL from supabase
        video_filename = os.path.basename(video_path)
        video_url = f"{SUPABASE_URL}/storage/v1/object/public/mithi_assets/videos/{video_filename}"
        
        success = notifier.send_completion_email(
            user_email=user_email,
            baby_name=baby_name,
            song_title=title,
            video_url=video_url,
            youtube_url=youtube_url
        )
        if success:
            print(f"✅ Email sent successfully.")
        else:
            print(f"❌ Failed to send email.")

if __name__ == "__main__":
    # 1. Liv Kaur
    rescue_song(
        song_id="07bf6117-7d35-424a-b34e-f2759f5c483a",
        baby_name="Liv Kaur",
        user_email="japnik1@gmail.com",
        video_path_rel="temp/LivKaur_SpecialSong_07bf61_20260203_225043.mp4",
        title="ਲਿਵ ਕੌਰ ਦਾ ਖਾਸ ਗੀਤ",
        lyrics_path_rel="temp/LivKaur_SpecialSong_07bf61_20260203_225043.txt"
    )

    # 2. Baani Kaur
    rescue_song(
        song_id="d89a0fb4-46b5-4bb9-84d2-1887b671acd8",
        baby_name="Baani Kaur",
        user_email="japnik1@gmail.com",
        video_path_rel="temp/BaaniKaur_SpecialSong_d89a0f_20260203_225549.mp4",
        title="ਬਾਣੀ ਕੌਰ ਦਾ ਖਾਸ ਗੀਤ: ਮਿੱਠੀ ਲੋਰੀ",
        lyrics_path_rel="temp/BaaniKaur_SpecialSong_d89a0f_20260203_225549.txt"
    )
    
    print("\n✅ Rescue operation complete.")
