
import os
import sys
import requests
import json
import logging
from utils import youtube_upload

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add backend to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Metadata from Supabase
SONG_ID = "918ea4b2-fef4-4ab1-8ada-4cb3a7d8196c"
VIDEO_URL = "https://auth.mithi.baby/storage/v1/object/public/mithi_assets/videos/LivKaur_Lori_918ea4_20260211_005844.mp4"
BABY_NAME = "Liv Kaur "  # Note the trailing space in DB
TITLE = "प्यारी लिव कौर की लोरी"
LYRICS = """(Verse 1)
चंदा मामा आए हैं
मीठे सपने लाए हैं
आंखें बंद अब कर लो तुम
नदिया में जैसे लहरें गुम

(Chorus)
सो जा मेरी लिव कौर प्यारी
सपनों की दुनिया है न्यारी

(Verse 2)
मम्मी लोरी गाती हैं
प्यार से तुम्हें सुलाती हैं
पापा का साया है संग
खुशियों के हैं गहरे रंग

(Chorus)
सो जा मेरी लिव कौर प्यारी
सपनों की दुनिया है न्यारी

(Verse 3)
दादू दादी देते प्यार
नानू नानी का दुलार
सबकी दुआएं साथ हैं
सिर पर कोमल हाथ हैं

(Chorus)
सो जा मेरी लिव कौर प्यारी
सपनों की दुनिया है न्यारी

(Verse 4)
रात की चादर ओढ़ लो
चिंताओं को छोड़ दो
परियों के देश जाना है
सुख की नींद ही आना है"""
LANGUAGE = "Hindi"
OCCASION = "Lori"
CHARACTERS = "Papa,Mummy,Dadu,Dadi,Nanu,Nani"

def download_video(url, dest_path):
    logger.info(f"Downloading video from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    logger.info(f"Video downloaded to {dest_path}")

def upload_to_youtube(video_path):
    logger.info("Uploading to YouTube...")
    result = youtube_upload.upload_to_youtube(
        video_path=video_path,
        ai_title=TITLE,
        lyrics_text=LYRICS,
        baby_name=BABY_NAME.strip(),
        language=LANGUAGE,
        occasion=OCCASION,
        characters=CHARACTERS
    )
    return result

def main():
    video_filename = f"temp_{SONG_ID}.mp4"
    video_path = os.path.join(backend_dir, "temp", video_filename)
    
    # Ensure temp dir exists
    os.makedirs(os.path.join(backend_dir, "temp"), exist_ok=True)
    
    try:
        # 1. Download
        download_video(VIDEO_URL, video_path)
        
        # 2. Upload
        result = upload_to_youtube(video_path)
        
        if result.get("status") == "success":
            logger.info(f"✅ Success! YouTube URL: {result.get('video_url')}")
            print(f"YOUTUBE_URL_OUTPUT: {result.get('video_url')}")
        else:
            logger.error(f"❌ Upload failed: {result.get('message')}")
            sys.exit(1)
            
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
            logger.info("Cleaned up temp video file.")

if __name__ == "__main__":
    main()
