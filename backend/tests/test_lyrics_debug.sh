#!/bin/bash
API_KEY="07776b4b0a27ef85581ac4b82b85d688"
TASK_ID="62d030fc2d6e3a8eff4d562f6a817d84"
AUDIO_ID="ff7a737d-bfcd-4e80-88a1-cdeb8dd436dd"

echo "🔍 Testing: https://api.kie.ai/api/v1/generate/lyrics"
curl -v -X POST "https://api.kie.ai/api/v1/generate/lyrics" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{ \"taskId\": \"$TASK_ID\", \"audioId\": \"$AUDIO_ID\" }"

echo ""
echo "------------------------------------------------"
echo "🔍 Testing: https://api.kie.ai/api/v1/get_lyrics"
curl -v -X POST "https://api.kie.ai/api/v1/get_lyrics" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{ \"taskId\": \"$TASK_ID\", \"audioId\": \"$AUDIO_ID\" }"
