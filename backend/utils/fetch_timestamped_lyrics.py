import urllib.request
import json
import os

# Configuration from previous successful run
API_KEY = "07776b4b0a27ef85581ac4b82b85d688"
TASK_ID = "62d030fc2d6e3a8eff4d562f6a817d84"
AUDIO_ID = "ff7a737d-bfcd-4e80-88a1-cdeb8dd436dd"
SONG_ID = "1769460898657"

ENDPOINT = "https://api.kie.ai/api/v1/generate/get-timestamped-lyrics"

print(f"🎵 Fetching Timestamped Lyrics for Song {SONG_ID}")
print(f"Task ID: {TASK_ID}")
print(f"Audio ID: {AUDIO_ID}")
print("-" * 50)

try:
    payload = json.dumps({
        "taskId": TASK_ID,
        "audioId": AUDIO_ID
    }).encode('utf-8')

    req = urllib.request.Request(ENDPOINT, data=payload, headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    })

    with urllib.request.urlopen(req) as response:
        if response.status == 200:
            data = json.loads(response.read().decode('utf-8'))
            print("✅ Success! Timestamped data received.")
            
            # Save to file
            output_file = f"lyrics/{SONG_ID}.json"
            os.makedirs("lyrics", exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved to {output_file}")
            print("-" * 50)
            
            # Show preview
            if "data" in data and "alignedWords" in data["data"]:
                words = data["data"]["alignedWords"]
                print(f"Found {len(words)} aligned words.")
                print("First 5 items:")
                for w in words[:5]:
                    print(f"  [{w.get('startS')}s - {w.get('endS')}s] {w.get('word')}")
            else:
                print("⚠️ Unexpected response format:")
                print(json.dumps(data, indent=2)[:500])
        else:
            print(f"❌ Failed: HTTP {response.status}")

except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error: {e.code} - {e.reason}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"❌ Error: {e}")
