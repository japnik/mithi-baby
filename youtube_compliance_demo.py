
import os
import sys
import datetime

# Add backend to path to import our utility
sys.path.append(os.path.join(os.getcwd(), "backend"))
from utils import youtube_upload

def run_compliance_demo():
    print("🚀 Mithi Baby - YouTube API Compliance Demonstration")
    print("==================================================")
    print("This script demonstrates the automated video upload process for Mithi Baby.")
    print("It uses the YouTube Data API v3 to upload a personalized baby song.")
    print("-" * 50)

    # 1. Prepare Metadata (Simulating the output from our generation pipeline)
    baby_name = "Ishaan"
    language = "Punjabi"
    occasion = "Lori"
    lyrics_text = """(Chorus)
Suraan de vich tera naam, Ishaan mere pyare
Suraan de vich tera naam, Ishaan mere pyare

Verse 1
Chann diyaan rashmaan, thandi hawa
Mummy di godi, rab di dua
Soun ja Ishaan, akhiyaan band kar
Mummy hai kol, na koi darr"""
    
    # This matches how process_song.py prepares the upload
    video_path = "backend/videos/125b8426-7fbb-4f39-9b70-2fec40420a09.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Error: Sample video not found at {video_path}")
        print("Please ensure you have a valid mp4 file for the demo.")
        return

    print(f"📦 Prepared Video: {video_path}")
    print(f"📝 Metadata: Baby Name: {baby_name}, Language: {language}, Occasion: {occasion}")
    print("-" * 50)

    # 2. Upload Process
    print("📡 Starting YouTube Upload...")
    
    # We use our branded wrapper 'upload_to_youtube' which handles:
    # - Dynamic Title Generation ([Name] — Personalized [Lang] [Occ])
    # - Dynamic Description (Heritage focused, includes lyrics)
    # - Tags (Mithi Baby, Lori, etc.)
    # - Category (Music)
    # - Made for Kids (True)
    
    try:
        # Note: Set privacy_status='unlisted' or 'private' for the demo if you don't want it public
        # but the actual app uses 'public' as configured in youtube_upload.py
        
        result = youtube_upload.upload_to_youtube(
            video_path=video_path,
            ai_title=f"{baby_name}'s Special Song", # This is overridden by the wrapper's branded title
            lyrics_text=lyrics_text,
            baby_name=baby_name,
            language=language,
            occasion=occasion
        )

        if result.get("status") == "success":
            print(f"\n✅ SUCCESS!")
            print(f"🎥 Video URL: {result.get('video_url')}")
            print(f"🆔 Video ID: {result.get('video_id')}")
        else:
            print(f"\n❌ FAILED: {result.get('message')}")
            
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")

if __name__ == "__main__":
    run_compliance_demo()
