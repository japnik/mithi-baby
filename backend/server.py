import http.server
import socketserver
import json
import os
import datetime
import subprocess
import subprocess
import sys
import uuid
from supabase import create_client, Client
import stripe
from utils.notifier import send_completion_email, send_payment_success_email
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# --- Stripe Setup ---
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

# --- Config & Supabase Setup ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


supabase: Client = None
if SUPABASE_URL and (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY):
    try:
        # Prioritize Service Role Key for backend operations
        key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
        supabase = create_client(SUPABASE_URL, key)
        print(f"✅ Supabase client initialized in Server ({'Service Role' if SUPABASE_SERVICE_ROLE_KEY else 'Anon'} Key)")

    except Exception as e:
        print(f"⚠️ Supabase Init Error: {e}")

PORT = int(os.getenv("PORT", 8080))
PORT = int(os.getenv("PORT", 8080))

# Path to backend (where this script resides)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(BASE_DIR, "api_logs")
os.makedirs(LOG_DIR, exist_ok=True)
SESSION_FILE = os.path.join(LOG_DIR, f"webapp_session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md")

# Path to frontend (relative to this script in backend/)
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "../frontend"))

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve from frontend directory by default
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def download_with_headers(self, url, path):
        import urllib.request
        req = urllib.request.Request(
            url, 
            data=None, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req) as response:
            with open(path, 'wb') as f:
                f.write(response.read())

    def do_GET(self):
        if self.path == '/api/songs':
             # List songs from Local + Supabase
             try:
                 songs_map = {} # Use dict to dedup by ID
                 
                 # ONLY Supabase (User Request)
                 if supabase:
                     try:
                         # Fetch completed songs only
                         response = supabase.table("songs").select("*").eq("status", "completed").order("created_at", desc=True).limit(50).execute()
                         remote_songs = response.data
                         
                         for r_song in remote_songs:
                             s_id = r_song.get("id")
                             if s_id not in songs_map:
                                 # Validate title
                                 if not r_song.get("title") or r_song.get("title") == "undefined":
                                     continue

                                 obj = {
                                     "song_id": s_id,
                                     "status": r_song.get("status", "completed"),
                                     "title": r_song.get("title"),
                                     "babyName": r_song.get("baby_name"),
                                     "occasion": r_song.get("occasion"),
                                     "language": r_song.get("language"),
                                     "lyrics": r_song.get("lyrics"),
                                     "characters": r_song.get("characters"),
                                     "date": r_song.get("created_at"),
                                     "video_url": r_song.get("video_url"),
                                     "audio_url": r_song.get("audio_url"),
                                     "image_url": r_song.get("image_url"), 
                                     "cover_image_url": r_song.get("cover_image_url"),
                                     "youtube_url": r_song.get("youtube_url"),
                                     "source": "cloud"
                                 }
                                 songs_map[s_id] = obj

                     except Exception as sbe:
                         print(f"Supabase Fetch Error: {sbe}")
                                 
                 # Convert to list and Sort
                 final_songs = list(songs_map.values())
                 
                 def get_sort_key(x):
                     return x.get('updated') or x.get('date') or '0000'
                     
                 final_songs.sort(key=get_sort_key, reverse=True)
                 
                 self.send_response(200)
                 self.send_header('Content-type', 'application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({"songs": final_songs}, default=str).encode())
             except Exception as e:
                 import traceback
                 traceback.print_exc()
                 self.send_response(500)
                 self.end_headers()
                 self.wfile.write(json.dumps({"error": str(e)}).encode())
                 
        elif self.path.startswith('/task_status/'):
            # Existing GET logic for status poller
            # Need to move it here from do_POST if it was there? 
            # WAIT. In previous view, `/task_status/` was in `do_POST`? 
            # Let me check the view again. 
            # Valid point. Polling usually implies GET. 
            # If `app.js` calls `fetch('/task_status/...')` it defaults to GET.
            # So `task_status` was likely BROKEN too if it was in `do_POST`.
            # Checking `app.js` -> `fetch(/task_status/${songId})` -> default GET.
            # So `do_POST` handling `task_status` was definitely wrong.
            # I will move `task_status` logic here too.
            song_id = self.path.split('/')[-1]
            videos_dir = os.path.join(BASE_DIR, "videos")
            status_file = os.path.join(videos_dir, f"{song_id}_status.json")
            
            if os.path.exists(status_file):
                with open(status_file, "r") as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            else:
                 video_path = os.path.join(videos_dir, f"{song_id}_HQ.mp4")
                 if os.path.exists(video_path):
                     self.send_response(200)
                     self.send_header('Content-type', 'application/json')
                     self.end_headers()
                     self.wfile.write(json.dumps({
                         "status": "completed", 
                         "video_url": f"videos/{song_id}_HQ.mp4", # Serve path relative to frontend/symlink
                         "message": "Video found (legacy)"
                     }).encode())
                 else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'{"status":"not_found"}')

        elif self.path == '/api/config.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "SUPABASE_URL": SUPABASE_URL,
                "SUPABASE_KEY": SUPABASE_KEY,
                "STRIPE_PUBLIC_KEY": STRIPE_PUBLIC_KEY,
                # Backend-only keys shouldn't be here
            }).encode())

        elif self.path.startswith('/api/payment_success'):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            session_id = query.get('session_id', [None])[0]
            
            if not session_id:
                self.send_error(400, "Missing session_id")
                return

            try:
                # Verify with Stripe
                session = stripe.checkout.Session.retrieve(session_id)
                if session.payment_status != 'paid':
                    self.send_response(200) # Process OK, but status failed
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "failed", "message": "Payment not completed"}).encode())
                    return
                
                # Check if already processed to avoid duplicates? 
                # Ideally DB check. simple check: metadata.song_id?
                # We haven't generated song_id yet. 
                # We can generate it now.
                
                # Extract metadata
                meta = session.metadata
                user_email = session.customer_details.email if session.customer_details else meta.get('email')
                
                # Trigger Generation
                song_id = self.trigger_generation_process({
                    "babyName": meta.get('babyName'),
                    "language": meta.get('language'),
                    "characters": meta.get('characters', '').split(','),
                    "occasion": meta.get('occasion'),
                    "user_email": user_email,
                    "user_id": meta.get('user_id'),
                    "autoYoutube": meta.get('autoYoutube') == 'true' or meta.get('autoYoutube') == 'True'
                })
                
                # Send "Queued" email
                if user_email:
                    send_payment_success_email(user_email, meta.get('babyName'))
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "started", 
                    "song_id": song_id,
                    "message": "Payment verified, song generation started"
                }).encode())
                
            except Exception as e:
                print(f"Payment Verify Error: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        else:
            # Check if this is a static file request
            filepath = os.path.join(FRONTEND_DIR, self.path.lstrip('/'))
            if not os.path.exists(filepath):
                # Try relative to BASE_DIR/../frontend just in case
                alt_path = os.path.join(BASE_DIR, "..", "frontend", self.path.lstrip('/'))
                if os.path.exists(alt_path):
                    filepath = alt_path
            
            if os.path.isfile(filepath):
                # If it's a directory or missing, let super handle it (or 404)
                return super().do_GET()
            else:
                print(f"⚠️ 404: {self.path} not found at {filepath}")
                return super().do_GET()

    def do_POST(self):
        if self.path == '/api/log':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                entry = json.loads(post_data.decode('utf-8'))
                self.log_to_file(entry)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except Exception as e:
                print(f"Log Error: {e}")
                self.send_response(500)
                self.end_headers()
                
        elif self.path == '/api/upload_youtube':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Check for dependencies
                from utils import youtube_upload
                
                # Handle both 'id' and 'song_id'
                song_id = data.get('song_id') or data.get('id')
                
                # Check absolute paths
                video_path = os.path.join(BASE_DIR, "videos", f"{song_id}_HQ.mp4")
                if not os.path.exists(video_path):
                     video_path = os.path.join(BASE_DIR, "videos", f"{song_id}.mp4")
                
                # If STILL missing, try downloading from the provided videoUrl (Supabase)
                if not os.path.exists(video_path) and data.get('videoUrl'):
                    print(f"Local file missing. Downloading from cloud: {data.get('videoUrl')}")
                    os.makedirs(os.path.join(BASE_DIR, "videos"), exist_ok=True)
                    self.download_with_headers(data.get('videoUrl'), video_path)
                
                if not os.path.exists(video_path):
                     raise FileNotFoundError(f"Video file not found for {song_id}. No local file and no URL.")
                      
                # Format Lyrics for professional look
                lyrics_raw = data.get('lyrics', '').replace('\\n', '\n')
                lyrics_lines = lyrics_raw.split('\n')
                formatted_lyrics = []
                verse_num = 1
                
                # Simple heuristic to split into sections if labels are missing
                chunks = lyrics_raw.split('\n\n')
                for chunk in chunks:
                    chunk = chunk.strip()
                    if not chunk: continue
                    if any(x in chunk.lower() for x in ['verse', 'chorus', 'intro', 'outro']):
                        formatted_lyrics.append(chunk)
                    else:
                        # Heuristic: if it contains the baby's name or "So ja", it's likely a chorus
                        if "so ja" in chunk.lower() or "ਸੋ ਜਾ" in chunk:
                            formatted_lyrics.append(f"(Chorus)\n{chunk}")
                        else:
                            formatted_lyrics.append(f"Verse {verse_num}:\n{chunk}")
                            verse_num += 1
                
                lyrics_text = "\n\n".join(formatted_lyrics)

                # Perform branded upload
                result = youtube_upload.upload_to_youtube(
                    video_path,
                    lyrics_title,
                    lyrics_text,
                    baby_name=data.get('babyName'),
                    language=data.get('language'),
                    occasion=data.get('occasion'),
                    characters=data.get('characters')
                )

                
                # If success, update Supabase so it's tracked
                if result.get('status') == 'success' and supabase:
                    yt_url = result.get('video_url')
                    try:
                        supabase.table("songs").update({"youtube_url": yt_url}).eq("id", song_id).execute()
                        print(f"✅ Supabase updated with YouTube URL: {yt_url}")
                    except Exception as sbe:
                        print(f"⚠️ Error updating Supabase with YT URL: {sbe}")

                print(f"YouTube Upload Result: {result}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())

        elif self.path == '/api/create_checkout_session':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Check for Promo Code (Free Testing)
                promo_code = data.get('promoCode', '').strip()
                test_promo = os.getenv("TEST_PROMO_CODE", "LivMithiFree")
                
                print(f"🔍 Debug: Received Promo Code: '{promo_code}'")
                print(f"🔍 Debug: Expected Promo Code: '{test_promo}'")
                
                if promo_code.lower() == test_promo.lower():
                    print(f"🎟️ Valid Promo Code used: {promo_code}. Bypassing Stripe.")
                    # Trigger generation directly
                    user_email = data.get('email')
                    baby_name = data.get('babyName', 'Baby')
                    
                    song_id = self.trigger_generation_process({
                        "babyName": baby_name,
                        "language": data.get('language'),
                        "characters": data.get('characters', []),
                        "occasion": data.get('occasion'),
                        "user_email": user_email,
                        "user_id": data.get('user_id'),
                        "autoYoutube": data.get('autoYoutube') is True or data.get('autoYoutube') == 'true'
                    })
                    
                    # Send immediate "Queued" email
                    if user_email:
                        send_payment_success_email(user_email, baby_name)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "payment_skipped", "song_id": song_id}).encode())
                    return

                # Create Stripe Session
                    # Determine callback URL dynamically (Localhost vs Cloud Run)
                    base_url = self.headers.get('Origin')
                    if not base_url:
                        base_url = self.headers.get('Referer')
                        if base_url and base_url.endswith('/'):
                            base_url = base_url[:-1]
                    
                    if not base_url:
                        base_url = f"http://localhost:{PORT}" # Fallback
                        
                    checkout_session = stripe.checkout.Session.create(
                        payment_method_types=['card'],
                        line_items=[{
                            'price_data': {
                                'currency': 'usd',
                                'product_data': {
                                    'name': 'Mithi Baby Personalized Song',
                                    'description': f"Personalized Lori for {data.get('babyName')} ({data.get('language')})",
                                },
                                'unit_amount': 100, # $1.00
                            },
                            'quantity': 1,
                        }],
                        mode='payment',
                        success_url=f"{base_url}/?session_id={{CHECKOUT_SESSION_ID}}", # Redirect back to frontend
                        cancel_url=f"{base_url}/",
                    metadata={
                        'babyName': data.get('babyName'),
                        'language': data.get('language'),
                        'characters': ",".join(data.get('characters', [])),
                        'occasion': data.get('occasion', 'Lori'),
                        'email': data.get('email'),
                        'user_id': data.get('user_id'),
                        'autoYoutube': str(data.get('autoYoutube', 'True'))
                    }
                )
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'id': checkout_session.id}).encode())
                
            except Exception as e:
                print(f"Stripe Error: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        elif self.path == '/api/generate_song':
             # LEGACY/DEBUG Endpoint (Still works directly if desired, or disable)
             # Let's keep it but ideally frontend doesn't call it directly anymore
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                song_id = self.trigger_generation_process(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "started",
                    "song_id": song_id,
                    "message": "Background process started"
                }).encode())
            except Exception as e:
                self.send_error(500, str(e))

        elif self.path.startswith('/api/check_video'):
            self.send_error(404)
                
        else:
            self.send_error(404)

    def log_to_file(self, entry):
        timestamp = entry.get('timestamp', datetime.datetime.now().isoformat())
        msg = entry.get('message', '')
        data = entry.get('data', None)
        type_ = entry.get('type', 'INFO')
        
        with open(SESSION_FILE, 'a') as f:
            f.write(f"\n## [{type_}] {msg}\n")
            f.write(f"**Time**: {timestamp}\n")
            if data:
                f.write("### Data\n")
                f.write(f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```\n")
            f.write("---\n")
            
    # Disable default console logging to keep terminal clean
    def log_message(self, format, *args):
        pass

    # Helper to launch process_song.py
    def trigger_generation_process(self, data):
        song_id = str(uuid.uuid4())
        
        videos_dir = os.path.join(BASE_DIR, "videos")
        os.makedirs(videos_dir, exist_ok=True)
        status_file = os.path.join(videos_dir, f"{song_id}_status.json")
        
        with open(status_file, "w") as f:
            json.dump({
                "status": "pending",
                "message": "Initializing...",
                "updated": str(datetime.datetime.now())
            }, f)
        
        python_bin = sys.executable 
        script_path = os.path.join(BASE_DIR, "process_song.py")
        
        # Parse characters list if needed
        chars = data.get('characters', [])
        if isinstance(chars, str): chars = [chars]

        cmd = [
            python_bin, "-u", script_path, 
            "--song_id", song_id,
            "--baby_name", data.get('babyName', ''),
            "--language", data.get('language', 'Punjabi'),
            "--characters", ",".join(chars),
            "--occasion", data.get('occasion', 'Lori'),
            "--log_file", SESSION_FILE
        ]

        if data.get('user_id'):
            cmd.extend(["--user_id", data.get('user_id')])
        
        if data.get('user_email'):
            cmd.extend(["--user_email", data.get('user_email')])
        
        if data.get('autoYoutube'):
            cmd.append("--auto_youtube")
        # We can store it in env or passed as arg if we update process_song.
        # For now, we just launch it.
        
        print(f"🚀 Launching background task for {song_id}")
        subprocess.Popen(cmd, cwd=BASE_DIR) 
        return song_id

print(f"🚀 Serving at http://localhost:{PORT}")
print(f"📂 BASE_DIR: {BASE_DIR}")
print(f"📂 FRONTEND_DIR: {FRONTEND_DIR}")
print(f"📝 Logging to {SESSION_FILE}")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

with ThreadedTCPServer(("", PORT), CustomHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Server Error: {e}")
