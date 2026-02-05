import os
import json
import time
import requests
import argparse
import datetime
import subprocess
import sys
import re
import random
from supabase import create_client, Client
from dotenv import load_dotenv

# Check for utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import utils
from utils import notifier, youtube_upload

# Load env
load_dotenv()

# --- Configuration & Setup ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUNO_API_KEY = os.getenv("SUNO_API_KEY")
SUNO_BASE_URL = os.getenv("SUNO_BASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


supabase: Client = None

def get_supabase_client():
    """Lazy initialization of Supabase client to avoid blocking at module load"""
    global supabase
    # Use Service Role Key for backend operations (to bypass RLS)
    key_to_use = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
    if supabase is None and SUPABASE_URL and key_to_use:
        try:
            print(f"Initializing Supabase client (using {'Service Role' if SUPABASE_SERVICE_ROLE_KEY else 'Anon'} key)...")
            supabase = create_client(SUPABASE_URL, key_to_use)
            print("✅ Supabase client initialized")
        except Exception as e:
            print(f"⚠️  Supabase Init Error: {e}")
            print("Continuing without Supabase...")

    return supabase

STATUS_DIR = "videos"
os.makedirs(STATUS_DIR, exist_ok=True)
os.makedirs("lyrics", exist_ok=True)

# --- Logging ---
LOG_FILE = None

def log(message, data=None, type_="INFO"):
    print(f"[{type_}] {message}")
    if LOG_FILE:
        try:
            timestamp = datetime.datetime.now().isoformat()
            with open(LOG_FILE, 'a') as f:
                f.write(f"\n## [{type_}] {message}\n")
                f.write(f"**Time**: {timestamp}\n")
                if data:
                    f.write("### Data\n")
                    f.write(f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```\n")
                f.write("---\n")
        except Exception as e:
            print(f"Log Error: {e}")

# --- Status Reporting ---

def write_status(song_id, status, message, data=None, error=None):
    status_file = os.path.join(STATUS_DIR, f"{song_id}_status.json")
    
    # Log significant status changes
    log_type = "ERROR" if status == "failed" else "INFO"
    log_data = data if data else {}
    if error: log_data["error"] = str(error)
    
    log(f"Status Update [{song_id}]: {status} - {message}", data=log_data, type_=log_type)
    
    # Read existing to preserve data if needed (merged)
    current_data = {}
    if os.path.exists(status_file):
        try:
            with open(status_file, "r") as f:
                current_data = json.load(f)
        except: pass
        
    timestamp = datetime.datetime.now().isoformat()
    update_payload = {
        "status": status,
        "message": message,
        "updated": timestamp
    }
    
    # Merge existing data (like lyrics, audio_url etc)
    final_data = {**current_data, **update_payload}
    
    if data:
        final_data.update(data)
        
    if error:
        final_data["error"] = str(error)
        
    # Write to local status file (legacy/backup)
    with open(status_file, "w") as f:
        json.dump(final_data, f, indent=2)

    # --- PUSH TO SUPABASE ---
    global supabase
    if not supabase: get_supabase_client() # Ensure initialized
    
    if supabase:
        try:
            # We want to strictly update status/metadata without overwriting other fields if possible
            # But 'upsert' works well if we have the ID.
            # Ideally we check if it exists or we just PATCH.
            # Supabase-py 'update' is cleaner for existing rows.
            
            # Construct metadata update
            # careful not to overwrite existing metadata completely if we can avoid it, 
            # but upsert usually replaces. 
            # Let's read current DB state? No, that's too slow.
            # We will assume we can merge into metadata.
            
            # Actually, let's just push "last_status_message" and "current_stage" to metadata
            # So we don't wipe potentially other keys if we were doing a full replace.
            # But here we probably want to update the 'status' column and 'metadata' column.
            
            # Simple approach: Update 'status' column + append to 'progress_history' in metadata?
            # Or just update a 'last_message' field in metadata.
            
            db_update = {
                "status": "processing" if status == "processing" else status, # Keep as processing until complete/fail
                # We can't easily deep-merge JSONB in a single 'update' call without a stored proc or raw SQL.
                # So we will just write what we know to specific keys in metadata if possible, 
                # OR we accept that we might be overwriting metadata. 
                # HOWEVER, process_song is the primary writer.
                
                # Let's try to just update specific fields if we are ensuring we don't lose data.
            }
            
            # For now, let's just log the key info to metadata
            # We will fetch the current row first to be safe about metadata merging?
            # No, that's an extra RTT.
            # Let's just UPSERT with the critical fields we want to track.
            
            # Actually, `status` column is likely an ENUM or text.
            
            # Status mapping
            db_status = status
            if status == "processing" and "music" in message.lower(): db_status = "generating_music"
            elif status == "processing" and "video" in message.lower(): db_status = "rendering_video"
            
            # But the DB constraint might be simple. Let's stick to existing "processing", "completed", "failed"
            # and put details in metadata.
            
            meta_update = {
                "last_update": timestamp,
                "current_message": message,
                "current_stage": log_data.get("stage", "unknown"),
                "progress": log_data.get("progress", 0)
            }
            
            if error: meta_update["error"] = str(error)
            
            # Safe Update: Fetch current metadata first to merge
            # This prevents us from wiping 'suno_task_id' if we wrote it earlier
            res = supabase.table("songs").select("metadata").eq("id", song_id).execute()
            current_meta_db = {}
            if res.data and len(res.data) > 0:
                current_meta_db = res.data[0].get("metadata", {}) or {}
            
            # History Logic: Append to existing list
            history = current_meta_db.get("history", [])
            # Only append if message is different from last to avoid noise? 
            # User wants visibility, so capturing stage changes is key.
            # Let's append if it's a new message or status change.
            last_entry = history[-1] if history else {}
            if last_entry.get("message") != message or last_entry.get("status") != status:
                 history.append({
                    "timestamp": timestamp,
                    "status": status,
                    "message": message,
                    "stage": log_data.get("stage", "unknown")
                })
            
            meta_update["history"] = history
                
            merged_meta = {**current_meta_db, **meta_update}
            
            supabase.table("songs").update({
                "status": status, # 'processing', 'failed', 'completed'
                "metadata": merged_meta
            }).eq("id", song_id).execute()
            
            # log("✨ Pushed status to Supabase DB") # Too noisy
            
        except Exception as db_e:
            log(f"⚠️ Failed to push status to DB: {db_e}", type_="WARNING")

# --- API Clients ---

def generate_lyrics(baby_name, language, characters, occasion):
    log(f"Generating lyrics for {baby_name} ({language})...", data={"characters": characters, "occasion": occasion})
    
    # Handle Random occasion (Ported from gemini-api.js)
    if occasion == "Random":
        random_occasions = ['Playtime', 'Good Morning', 'Sweet Dreams', 'Bath Time', 'Tummy Time', 'Happy Moments']
        original_occasion = occasion
        occasion = random.choice(random_occasions)
        log(f"Random Occasion Selected: {occasion} (was {original_occasion})")

    script_names = {
        'Punjabi': 'Gurmukhi (ਪੰਜਾਬੀ)',
        'Hindi': 'Devanagari (हिन्दी)',
        'Hinglish': 'Latin (English)'
    }
    
    # Specific instruction for Hindi to match the strictness of Punjabi
    script_check = ""
    if language == "Hindi":
        script_check = "- IF HINDI: Use DEVANAGARI script (e.g. सो जा). DO NOT use Roman (English) characters."
    elif language == "Punjabi":
        script_check = "- IF PUNJABI: Use GURMUKHI script (e.g. ਸੋ ਜਾ). DO NOT use Roman (English) characters."
    
    mood_requirements = f"""
- Tone: Soothing, gentle, slow, and calm (Sleep inducing lullaby)
- Themes: Sleep, sweet dreams, moon, stars, protection, warmth
- Context: {occasion} (Weave in {occasion} themes )
- Rhythm: Slow, rocking lullaby style, melodic"""

    visual_style = "Soft lighting, dreamy, night time, stars, peaceful, cozy, magical glow, aesthetics"

    characters_text = ", ".join(characters)
    
    prompt = f"""Create a {occasion} song in {language} for baby {baby_name}.

The song should mention and celebrate these people as important in the baby's life: {characters_text}.

CRITICAL LANGUAGE REQUIREMENTS:
- CRITICAL: SCRIPT must be {script_names.get(language, 'Latin')}.
{script_check}
- DO NOT use English or romanized text (unless language is Hinglish)
- Use authentic {language} vocabulary and grammar

Requirements:
{mood_requirements}
- Culturally appropriate for {language} families
- 4-6 short verses (each verse 2-4 lines)
- Include baby's name "{baby_name}" naturally in the lyrics
- Mention each of these people lovingly: {characters_text}
- Use {language} script throughout
- Make it warm, loving, and comforting
- Include a repeating chorus that's easy to remember

            Please provide:
1. A beautiful title for the song (MUST include "{baby_name}" and "{occasion}")
2. The complete lyrics
3. A detailed prompt for generating a cover image for this song.
   - CRITICAL: The image prompt must describe a SCENE WITHOUT ANY HUMANS OR PEOPLE.
   - ABSOLUTELY NO babies, children, parents, faces, or any human figures whatsoever.
   - FORBIDDEN: Do not include any person, baby, child, adult, or human body parts.
   - Focus ONLY on: the occasion, atmosphere, magical elements, toys, nature, objects, or abstract representations of the mood.
   - Examples of good elements: empty cradle, toys, moon, stars, nature, magical lights, nursery items.
   - Style: Digital Art, {visual_style}, Magical, Dreamy.
   - Elements: Include specific elements for {occasion} if applicable.
4. A detailed music style description (tags) for the AI music generator.
   - CRITICAL: Always a LULLABY.
   - FOCUS: Traditional Instruments (Bansuri/Flute, Sitar, Santoor, Harmonium, Soft Tabla, Sarangi).
   - KEYWORDS: "lullaby, soft, gentle, soothing, female vocals, traditional, peaceful, calming, acoustic, slow tempo".
   - Match the cultural vibe of the language.

Format your response as JSON:
{{
  "title": "Song Title",
  "lyrics": "Full lyrics here...",
  "image_prompt": "Image generation prompt here...",
  "musicStyle": "Music style tags here"
}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string", 
                        "description": "Title of the song in the target language"
                    },
                    "lyrics": {
                        "type": "string", 
                        "description": "Complete lyrics with proper line breaks using \\n"
                    },
                    "musicStyle": {
                        "type": "string", 
                        "description": "Elaborate music style string."
                    },
                    "imagePrompt": {
                        "type": "string", 
                        "description": "Prompt for generating cover art"
                    }
                },
                "required": ["title", "lyrics", "imagePrompt", "musicStyle"]
            }
        }
    }
    
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Gemini API Error: {resp.text}")
        
    result = resp.json()
    try:
        content_text = result['candidates'][0]['content']['parts'][0]['text']
        return json.loads(content_text)
    except (KeyError, json.JSONDecodeError) as e:
        raise Exception(f"Failed to parse Gemini response: {e}")

def generate_music(lyrics, title, style):
    log("Generating music...", data={"title": title, "style": style})
    url = f"{SUNO_BASE_URL}/api/v1/generate"
    headers = {"Authorization": f"Bearer {SUNO_API_KEY}", "Content-Type": "application/json"}
    
    # Fallback style if Gemini is empty
    if not style or not style.strip():
        style = f"lullaby, soft, gentle, soothing, female vocals, traditional, peaceful, calming, tender, baby song"
        log("Warning: Using fallback music style.")

    payload = {
        "prompt": lyrics,
        "customMode": True,
        "style": style,
        "title": title,
        "model": "V5",
        "instrumental": False,
        "vocalGender": "f", # Restored from suno-api.js
        "callBackUrl": "https://example.com/callback" # Required by API now
    }
    
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Suno Init Error: {resp.text}")
        
    response_data = resp.json()
    # Log raw response to debug NoneType error
    log("Suno Init Response", data=response_data)

    if not response_data.get('data'):
         raise Exception(f"Suno API returned no data: {response_data}")

    task_id = response_data['data']['taskId']
    log(f"Music Task ID: {task_id}")
    
    # Poll
    for i in range(120): # 10 mins max
        time.sleep(5)
        poll_url = f"{SUNO_BASE_URL}/api/v1/generate/record-info?taskId={task_id}"
        poll_resp = requests.get(poll_url, headers=headers, timeout=30)
        data = poll_resp.json()
        
        status = data.get('data', {}).get('status')
        if status == 'SUCCESS':
            track = data['data']['response']['sunoData'][0]
            track['taskId'] = task_id
            return track
        elif status == 'FAILED':
            raise Exception("Suno Generation Failed")
            
    raise Exception("Suno Timeout")

def get_aligned_lyrics(task_id, audio_id, headers):
    log(f"Fetching aligned lyrics for Task: {task_id}...")
    url = f"{SUNO_BASE_URL}/api/v1/generate/get-timestamped-lyrics"
    
    payload = {
        "taskId": task_id,
        "audioId": audio_id
    }
    
    for i in range(12): # 60s max
        if i > 0: time.sleep(5)
        
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            data = resp.json()
            
            if data.get('code') == 200 and data.get('data') and data['data'].get('alignedWords'):
                aligned_words = data['data']['alignedWords']
                word_count = len(aligned_words)
                sample_words = aligned_words[:3] if len(aligned_words) >= 3 else aligned_words
                
                log("Aligned lyrics fetched successfully", data={
                    "wordCount": word_count,
                    "sample": sample_words
                })
                log("Timestamps received", data=data)
                return data # Return full data structure as required by generate_video_task.py
            else:
                log(f"Lyrics not ready yet (Attempt {i+1}/12)")
                
        except Exception as e:
            log(f"Lyrics poll error: {e}")
            
    return None

def generate_image(prompt):
    log("Generating image...", data={"prompt": prompt})
    url = f"{SUNO_BASE_URL}/api/v1/jobs/createTask"
    headers = {"Authorization": f"Bearer {SUNO_API_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "model": "z-image",
        "input": {"prompt": prompt, "aspect_ratio": "1:1"},
        "callBackUrl": "https://example.com/callback"
    }
    
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"Image Init Warning: {resp.text}")
        return None
        
    task_id = resp.json()['data']['taskId']
    
    # Poll
    for i in range(30): # 60s max
        time.sleep(2)
        poll_url = f"{SUNO_BASE_URL}/api/v1/jobs/recordInfo?taskId={task_id}"
        poll_resp = requests.get(poll_url, headers=headers, timeout=30)
        data = poll_resp.json()
        
        state = data.get('data', {}).get('state')
        if state == 'success':
            try:
                res = json.loads(data['data']['resultJson'])
                return res['resultUrls'][0]
            except: return None
        elif state == 'fail':
            print("Image Task Failed")
            return None
            
    return None

def download_file(url, path):
    log(f"Downloading {url} to {path}...")
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        with requests.get(url, stream=True, headers=headers, timeout=60) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

# --- Orchestrator ---

def main():
    print("DEBUG: main() called")
    global LOG_FILE
    parser = argparse.ArgumentParser()
    parser.add_argument("--song_id", required=True)
    parser.add_argument("--baby_name", required=True)
    parser.add_argument("--language", default="Punjabi")
    parser.add_argument("--characters", required=True)
    parser.add_argument("--occasion", default="Lori")
    parser.add_argument("--log_file", help="Path to log file")
    parser.add_argument("--user_id", help="Supabase User ID", default=None)
    parser.add_argument("--user_email", help="User Email for notification", default=None)
    parser.add_argument("--auto_youtube", action="store_true", help="Auto upload to YouTube")
    
    args = parser.parse_args()
    
    song_id = args.song_id
    if args.log_file:
        LOG_FILE = args.log_file

    # Sanitize for filenames
    def sanitize(text):
        return re.sub(r'[^a-zA-Z0-9]', '', text)

    baby_clean = sanitize(args.baby_name)
    occ_clean = sanitize(args.occasion)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{baby_clean}_{occ_clean}_{song_id[:6]}_{timestamp}" # e.g. Japnik_Lori_a1b2c3_20231010_120000
    
    log(f"Processing with base name: {base_name}")
    
    # --- FIX: Initialize DB Row immediately for Visibility ---
    sb_init = get_supabase_client()
    if sb_init:
        try:
            # Create minimal entry to allow updates
            init_payload = {
                "id": song_id,
                "baby_name": args.baby_name,
                "status": "processing",
                "occasion": args.occasion,
                "metadata": {
                    "history": [],
                    "last_update": datetime.datetime.now().isoformat(), 
                    "started_at": datetime.datetime.now().isoformat()
                }
            }
            # Only set user_id if present to avoid key errors? Supabase should handle nulls if schema allows.
            if args.user_id: init_payload["user_id"] = args.user_id
            
            sb_init.table("songs").upsert(init_payload).execute()
            log("✅ Initialized Supabase row for visibility")
        except Exception as e:
            log(f"⚠️ Failed to init DB row: {e}", type_="WARNING")
    # ---------------------------------------------------------

    try:
        # 1. Lyrics
        write_status(song_id, "processing", "Writing lyrics...", data={"stage": 1, "progress": 10})
        lyrics_data = generate_lyrics(args.baby_name, args.language, args.characters.split(','), args.occasion)
        
        # FIX: Post-process lyrics to prevent video overflow
        # Split long lines by replacing comma+space with comma+newline
        if lyrics_data.get('lyrics'):
            log("formatting lyrics... adding newlines after commas")
            lyrics_data['lyrics'] = lyrics_data['lyrics'].replace(', ', ',\n').replace(',', ',\n')
            # Normalize double newlines just in case
            lyrics_data['lyrics'] = lyrics_data['lyrics'].replace('\n \n', '\n').replace('\n\n\n', '\n\n')
        
        # 2. Music & Image
        write_status(song_id, "processing", "Composing music & painting art...", data={
            "stage": 2, 
            "progress": 30,
            "lyrics": lyrics_data['lyrics'],
            "title": lyrics_data['title'],
            "musicStyle": lyrics_data['musicStyle'],
            "imagePrompt": lyrics_data['imagePrompt']
        })
        
        music_track = generate_music(lyrics_data['lyrics'], lyrics_data['title'], lyrics_data['musicStyle'])
        
        # 2b. Aligned Lyrics (Critical for Video)
        headers = {"Authorization": f"Bearer {SUNO_API_KEY}", "Content-Type": "application/json"}
        aligned_data = get_aligned_lyrics(music_track['taskId'], music_track['id'], headers)
        
        image_url = generate_image(lyrics_data['imagePrompt'])
        
        remote_audio_url = music_track['audioUrl']
        
        # Fallback image
        if not image_url:
            image_url = music_track['imageUrl']
            
        write_status(song_id, "processing", "Downloading assets...", data={
            "stage": 2,
            "progress": 60,
            "audioUrl": remote_audio_url,
            "imageUrl": image_url,
            "duration": music_track['duration']
        })

        # 3. Download Assets (Descriptive Names)
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        audio_path = os.path.join(temp_dir, f"{base_name}.mp3")
        image_path = os.path.join(temp_dir, f"{base_name}.jpg")
        lyrics_path = os.path.join(temp_dir, f"{base_name}.txt")
        video_path = os.path.join(temp_dir, f"{base_name}.mp4")
        
        # Save lyrics locally (temp)
        with open(lyrics_path, "w") as f:
            f.write(lyrics_data['lyrics'])
            
        # Save aligned lyrics just in case (though we pass to video gen via args? No, video gen reads file?)
        # generate_video_task.py reads --lyrics (txt).
        # We also need to save json for upload?
        if aligned_data:
             lyrics_json_path = os.path.join(temp_dir, f"{base_name}.json")
             with open(lyrics_json_path, "w") as f:
                 json.dump(aligned_data, f)
        
        if not download_file(remote_audio_url, audio_path):
             raise Exception("Failed to download audio")
        if not download_file(image_url, image_path):
             raise Exception("Failed to download image")
            
        # 4. Generate Video
        write_status(song_id, "processing", "Rendering final video...", data={"stage": 3, "progress": 70})
        
        cmd = [
            sys.executable, "generate_video_task.py",
            song_id,
            "--title", lyrics_data['title'],
            "--audio", audio_path,
            "--image", image_path,
            "--lyrics", lyrics_path,
            "--output", video_path,
            "--log_file", LOG_FILE or "",
            "--language", args.language
        ]
        
        subprocess.check_call(cmd)
        
        # Merge status (Video is ready locally)
        final_video_status_path = f"videos/{song_id}_status.json"
        
        # 5. Supabase Upload & DB Save
        sb_client = get_supabase_client()
        if sb_client:
            try:
                write_status(song_id, "processing", "Uploading to cloud...")
                log("☁️ Uploading assets to Supabase...")

                # Upload Files
                def upload_asset(local_path, destination_path, content_type):
                    try:
                        with open(local_path, 'rb') as f:
                            sb_client.storage.from_("mithi_assets").upload(
                                path=destination_path,
                                file=f,
                                file_options={"content-type": content_type, "upsert": "true"}
                            )
                        return sb_client.storage.from_("mithi_assets").get_public_url(destination_path)
                    except Exception as up_e:
                        log(f"Upload warning for {destination_path}: {up_e}", type_="WARNING")
                        return None

                s_audio_url = upload_asset(audio_path, f"audios/{base_name}.mp3", "audio/mpeg")
                
                # Image
                s_image_url = upload_asset(image_path, f"images/{base_name}.jpg", "image/jpeg")
                s_cover_url = s_image_url 

                # Video
                s_video_url = upload_asset(video_path, f"videos/{base_name}.mp4", "video/mp4")

                # Lyrics: Upload as JSON
                try:
                    lyrics_filename = f"{base_name}_lyrics.json"
                    lyrics_local_path = os.path.join(temp_dir, lyrics_filename)
                    with open(lyrics_local_path, "w") as lf:
                        json.dump(lyrics_data, lf, indent=2, ensure_ascii=False)
                    
                    s_lyrics_url = upload_asset(lyrics_local_path, f"lyrics/{lyrics_filename}", "application/json")
                    log(f"📝 Lyrics uploaded to: {s_lyrics_url}")
                except Exception as le:
                    log(f"Lyrics upload failed: {le}", type_="WARNING")
                    s_lyrics_url = None

                # Insert into DB
                db_payload = {
                    "id": song_id, 
                    "user_id": args.user_id,
                    "baby_name": args.baby_name,
                    "occasion": args.occasion,
                    "language": args.language,
                    "characters": args.characters,
                    "title": lyrics_data['title'],
                    "lyrics": lyrics_data['lyrics'],
                    "status": "completed",
                    "video_url": s_video_url,
                    "audio_url": s_audio_url,
                    "cover_image_url": s_cover_url,
                    "image_url": s_image_url, 
                    "metadata": {
                        "suno_task_id": music_track.get('id'),
                        "music_style": lyrics_data.get('musicStyle'),
                        "image_prompt": lyrics_data.get('imagePrompt'),
                        "local_video_path": video_path, # Legacy
                        "lyrics_json_url": s_lyrics_url
                    }
                }
                
                sb_client.table("songs").upsert(db_payload).execute()
                log("✅ Saved to Supabase Database!")

                # Update status file with CLOUD URL
                write_status(song_id, "completed", "Video generated & Saved to Cloud!", data={"video_url": s_video_url})
                
                
                # 6. Optional YouTube Upload
                youtube_url = None
                if args.auto_youtube:
                    log("🎥 Auto-upload to YouTube enabled. Waiting 4 seconds...")
                    time.sleep(4)
                    try:
                        yt_result = youtube_upload.upload_to_youtube(
                            video_path, 
                            lyrics_data['title'], 
                            lyrics_data['lyrics'],
                            baby_name=args.baby_name,
                            language=args.language,
                            occasion=args.occasion,
                            characters=args.characters
                        )
                        if yt_result and yt_result.get('status') == 'success':
                            youtube_url = yt_result['video_url']
                            log(f"✅ YouTube Upload Success: {youtube_url}")
                            
                            # Update Supabase with YouTube URL
                            if sb_client:
                                try:
                                    sb_client.table("songs").update({"youtube_url": youtube_url}).eq("id", song_id).execute()
                                    log(f"✅ Supabase updated with YouTube URL: {youtube_url}")
                                except Exception as sbe:
                                    log(f"⚠️ Error updating Supabase with YT URL: {sbe}", type_="WARNING")

                    except Exception as yt_err:
                        log(f"YouTube Upload Error: {yt_err}", type_="WARNING")

                # 7. Notify User via Email (with 3-minute delay)
                if args.user_email:
                    log("⏳ Waiting 3 minutes before sending final notification...")
                    time.sleep(180) # 3 minutes
                    
                    log(f"📧 Sending completion email to {args.user_email}...")
                    success = notifier.send_completion_email(
                        user_email=args.user_email,
                        baby_name=args.baby_name,
                        song_title=lyrics_data['title'],
                        video_url=s_video_url,
                        youtube_url=youtube_url
                    )
                    if success:
                        log(f"✅ Email sent successfully to {args.user_email}")
                    else:
                        log(f"❌ Failed to send email to {args.user_email}", type_="ERROR")

                # Cleanup Temp Files (Moved to end)
                log("🧹 Cleaning up temp files...")
                for p in [audio_path, image_path, video_path, lyrics_path]:
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                            log(f"Deleted {p}")
                        except: pass
            except Exception as sb_ex:
                log(f"❌ Supabase Error: {sb_ex}", type_="ERROR")

    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # Friendly Error Messages
        error_msg = str(e)
        if isinstance(e, requests.exceptions.Timeout):
            error_msg = "External API timed out (30s limit). Please try again."
        elif isinstance(e, requests.exceptions.ConnectionError):
            error_msg = "Network connection failed."
            
        write_status(song_id, "failed", "Process failed", error=error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
