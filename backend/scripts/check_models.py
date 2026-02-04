import requests
import json
import os

try:
    with open("api/config.json") as f:
        key = json.load(f)["GEMINI_API_KEY"]
except:
    print("No config found")
    exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
resp = requests.get(url)
print(json.dumps(resp.json(), indent=2))
