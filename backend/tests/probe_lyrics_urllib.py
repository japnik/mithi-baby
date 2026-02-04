import urllib.request
import json
import urllib.error

API_KEY = "07776b4b0a27ef85581ac4b82b85d688"
TASK_ID = "62d030fc2d6e3a8eff4d562f6a817d84"
AUDIO_ID = "ff7a737d-bfcd-4e80-88a1-cdeb8dd436dd"

endpoints = [
    "https://api.kie.ai/api/v1/generate/lyrics",
    "https://api.kie.ai/api/v1/lyrics"
]

print(f"🔎 Probing endpoints for Task: {TASK_ID}")

for url in endpoints:
    print(f"\n👉 Testing: {url}")
    try:
        data = json.dumps({"taskId": TASK_ID, "audioId": AUDIO_ID}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        })
        
        with urllib.request.urlopen(req) as response:
            print(f"✅ Status: {response.status}")
            print(f"Response: {response.read().decode('utf-8')[:500]}")
            
    except urllib.error.HTTPError as e:
        print(f"❌ Failed: {e.code} - {e.reason}")
    except Exception as e:
        print(f"❌ Error: {e}")

