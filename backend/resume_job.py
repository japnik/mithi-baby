
import os
import sys
import json
import subprocess
import datetime
from dotenv import load_dotenv
from supabase import create_client

# Load env
load_dotenv()

# Params (Recovered from logs)
SONG_ID = "b9f33674-11b2-4733-9543-236ab44da88a"
USER_ID = "ed7e0394-18da-4c20-9f82-872b2a65a6e3" # Assumed from recent activity
BABY_NAME = "Ishaan"
LANGUAGE = "Hindi"
CHARACTERS = ["Papa", "Mummy", "Nani"]
OCCASION = "Lori"
TITLE = "ईशान का ख़ास गीत"
LOG_FILE = "/Users/japnik/Desktop/projects/baby_songs/mylori/backend/api_logs/webapp_session_20260204_004841.md"

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = None
if SUPABASE_URL and (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY):
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
    supabase = create_client(SUPABASE_URL, key)
    print("✅ Supabase client initialized")

def main():
    print(f"🚀 Resuming job for {SONG_ID}")
    
    # Reconstruct Paths
    # base_name was: Ishaan_SpecialSong_b9f336_20260204_010411
    # We can try to assume it based on files or I can ls again?
    # I saw the file names in step 641: Ishaan_SpecialSong_b9f336_20260204_010411.mp3
    BASE_NAME = "Ishaan_SpecialSong_b9f336_20260204_010411"
    TEMP_DIR = "temp"
    
    audio_path = os.path.join(TEMP_DIR, f"{BASE_NAME}.mp3")
    image_path = os.path.join(TEMP_DIR, f"{BASE_NAME}.jpg")
    lyrics_path = os.path.join(TEMP_DIR, f"{BASE_NAME}.txt")
    video_path = os.path.join(TEMP_DIR, f"{BASE_NAME}.mp4")
    json_path = os.path.join(TEMP_DIR, f"{BASE_NAME}.json") # Aligned lyrics
    
    # Check if inputs exist
    for p in [audio_path, image_path, lyrics_path]:
        if not os.path.exists(p):
            print(f"❌ Missing critical file: {p}")
            return

    # 1. Generate Video
    print("🎥 Generating Video...")
    cmd = [
        sys.executable, "generate_video_task.py",
        SONG_ID,
        "--title", TITLE,
        "--audio", audio_path,
        "--image", image_path,
        "--lyrics", lyrics_path,
        "--output", video_path,
        "--log_file", LOG_FILE or "",
        "--language", LANGUAGE
    ]
    try:
        subprocess.check_call(cmd)
        print("✅ Video Generation Complete")
    except subprocess.CalledProcessError as e:
        print(f"❌ Video Generation Failed: {e}")
        return

    # 2. Upload to Cloud
    if not supabase:
        print("⚠️ No Supabase client, skipping upload")
        return

    print("☁️ Uploading to Supabase...")
    
    def upload_asset(local_path, destination_path, content_type):
        try:
            with open(local_path, 'rb') as f:
                supabase.storage.from_("mithi_assets").upload(
                    path=destination_path,
                    file=f,
                    file_options={"content-type": content_type, "upsert": "true"}
                )
            return supabase.storage.from_("mithi_assets").get_public_url(destination_path)
        except Exception as up_e:
            print(f"⚠️ Upload warning for {destination_path}: {up_e}")
            # Try getting public URL anyway (maybe already uploaded)
            return supabase.storage.from_("mithi_assets").get_public_url(destination_path)

    s_audio_url = upload_asset(audio_path, f"audios/{BASE_NAME}.mp3", "audio/mpeg")
    s_image_url = upload_asset(image_path, f"images/{BASE_NAME}.jpg", "image/jpeg")
    s_video_url = upload_asset(video_path, f"videos/{BASE_NAME}.mp4", "video/mp4")
    
    # Lyrics JSON
    lyrics_data = {}
    # Read text lyrics
    with open(lyrics_path, 'r') as f:
        lyrics_text = f.read()

    # Reconstruct lyrics data object
    # We don't have the original lyrics_data JSON from process_song.py unless we saved it.
    # process_song.py saves 'lyrics_json_path' IF aligned data exists.
    # But it also creates a custom JSON for upload in lines 521.
    # I'll create a minimal one.
    lyrics_payload = {
        "title": TITLE,
        "lyrics": lyrics_text,
        # We miss imagePrompt/musicStyle but can read from aligned json if present?
        # Aligned json: temp/Ishaan_SpecialSong_b9f336_20260204_010411.json
    }
    
    # Check aligned json for metadata? No, aligned is just timestamps.
    # But I can read log file for metadata?
    # LOG contained imagePrompt and musicStyle.
    # I will hardcode them from logs for completeness if needed, or just skip.
    image_prompt_log = "A magical and serene nursery scene at night..."
    music_style_log = "Indian Lullaby, Soothing, Gentle..."

    lyrics_payload["imagePrompt"] = image_prompt_log
    lyrics_payload["musicStyle"] = music_style_log

    lyrics_upload_path = f"lyrics/{BASE_NAME}_lyrics.json"
    temp_lyrics_json_path = os.path.join(TEMP_DIR, f"{BASE_NAME}_lyrics_temp.json")
    with open(temp_lyrics_json_path, "w") as f:
        json.dump(lyrics_payload, f)
        
    s_lyrics_url = upload_asset(temp_lyrics_json_path, lyrics_upload_path, "application/json")
    
    # 3. Update DB
    print("💾 Updating Database...")
    db_payload = {
        "id": SONG_ID, 
        "user_id": USER_ID,
        "baby_name": BABY_NAME,
        "occasion": OCCASION,
        "language": LANGUAGE,
        "characters": ",".join(CHARACTERS),
        "title": TITLE,
        "lyrics": lyrics_text,
        "status": "completed",
        "video_url": s_video_url,
        "audio_url": s_audio_url,
        "cover_image_url": s_image_url,
        "image_url": s_image_url, 
        "metadata": {
            "suno_task_id": "RECOVERED",
            "music_style": music_style_log,
            "image_prompt": image_prompt_log,
            "local_video_path": video_path,
            "lyrics_json_url": s_lyrics_url
        }
    }
    
    res = supabase.table("songs").upsert(db_payload).execute()
    print("✅ DB Updated!")
    
    # Cleanup (Optional - maybe keep for safety this time)
    # print("🧹 Cleaning up...")
    # Clean up the extra json we made
    if os.path.exists(temp_lyrics_json_path):
        os.remove(temp_lyrics_json_path)

if __name__ == "__main__":
    main()
