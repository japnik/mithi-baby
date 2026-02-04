import requests
import json

API_KEY = "07776b4b0a27ef85581ac4b82b85d688"
TASK_ID = "62d030fc2d6e3a8eff4d562f6a817d84"
AUDIO_ID = "ff7a737d-bfcd-4e80-88a1-cdeb8dd436dd"

endpoints = [
    "https://api.kie.ai/api/v1/generate/lyrics",
    "https://api.kie.ai/api/v1/lyrics",
    "https://api.kie.ai/api/v1/get_lyrics",
    "https://api.kie.ai/api/v1/suno/lyrics"
]

print(f"🔎 Probing endpoints for Task: {TASK_ID}")

for url in endpoints:
    print(f"\n👉 Testing: {url}")
    try:
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={"taskId": TASK_ID, "audioId": AUDIO_ID},
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
    except Exception as e:
        print(f"failed: {e}")

