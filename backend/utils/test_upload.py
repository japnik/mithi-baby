
import os
import sys

# Ensure we can import from utils (local directory)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from moviepy import ColorClip
    from utils import youtube_upload
except ImportError as e:
    print(f"❌ Error: Missing dependencies. {e}")
    print("Run: venv/bin/pip install moviepy google-api-python-client google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

def create_dummy_video(filename="test_video_2s.mp4"):
    print(f"🎥 Generating 2-second test video: {filename}")
    # Create a 2-second red clip, 720p
    clip = ColorClip(size=(1280, 720), color=(255, 0, 0), duration=2)
    clip.write_videofile(filename, fps=24, logger=None)
    print("✅ Video generated.")
    return filename

def test_upload():
    print("\n🚀 Starting Test Upload...")
    
    # Check for secrets
    if not os.path.exists("api/client_secrets.json"):
        print("❌ Error: 'api/client_secrets.json' is missing!")
        print("Please download it from Google Cloud Console and save it first.")
        return

    video_file = create_dummy_video()
    
    try:
        title = "Mithi Baby - Test Integration Video"
        desc = "This is a 2-second test upload to verify API integration. #Test"
        
        print(f"📤 Uploading '{title}'...")
        result = youtube_upload.upload_video(
            file_path=video_file,
            title=title,
            description=desc,
            privacy_status='private' # Safest for testing
        )
        
        if result.get('status') == 'success':
            print(f"\n✨ Test PASSED! Video URL: {result['video_url']}")
            print("Check your YouTube Studio Content tab (it may be Private).")
        else:
            print(f"\n❌ Test FAILED: {result.get('message')}")
            
    except Exception as e:
        print(f"\n❌ Exception during test: {e}")
    finally:
        # Cleanup
        if os.path.exists(video_file):
            os.remove(video_file)
            print("🧹 Cleaned up test video file.")

if __name__ == "__main__":
    test_upload()
