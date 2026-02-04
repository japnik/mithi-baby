#!/bin/bash

# Recover Video Generation for Diwali Song
# Audio: https://musicfile.kie.ai/NTgzYjMyNWUtMTM2MS00YzhiLTgxNGItOWFjNjU1Nzc2MGUw.mp3
# Audio: https://musicfile.kie.ai/NTgzYjMyNWUtMTM2MS00YzhiLTgxNGItOWFjNjU1Nzc2MGUw.mp3
# ID: 583b325e-1361-4c8b-814b-9ac6557760e0
# TaskID: 1b7ac3c75ab36083684db7aafb5d0fba

API_KEY="07776b4b0a27ef85581ac4b82b85d688"
BASE_URL="https://api.kie.ai"
AUDIO_ID="583b325e-1361-4c8b-814b-9ac6557760e0"
TASK_ID_ORIG="1b7ac3c75ab36083684db7aafb5d0fba"

echo "============================================================"
echo "🎬 RECOVERING VIDEO GENERATION"
echo "============================================================"
echo "Audio ID: $AUDIO_ID"
echo "Original Task ID: $TASK_ID_ORIG"
echo ""

# 1. Start Video Generation
echo "Requesting video generation..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/mp4/generate" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"taskId\": \"$TASK_ID_ORIG\",
    \"audioId\": \"$AUDIO_ID\",
    \"domainName\": \"mylori.app\",
    \"callBackUrl\": \"https://example.com/callback\"
  }")

# Check response
echo "Response: $RESPONSE"
TASK_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['taskId'])" 2>/dev/null)

if [ -z "$TASK_ID" ] || [ "$TASK_ID" == "None" ]; then
    echo "❌ Failed to start video generation"
    exit 1
fi

echo "✅ Video generation started! Task ID: $TASK_ID"
echo "Waiting for completion (polling every 5s)..."
echo ""

# 2. Poll for Completion
for i in {1..30}; do
    STATUS_RES=$(curl -s -X GET "$BASE_URL/api/v1/mp4/record-info?taskId=$TASK_ID" \
      -H "Authorization: Bearer $API_KEY")
    
    # Check status
    STATUS=$(echo "$STATUS_RES" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('successFlag', 'PENDING'))" 2>/dev/null)
    VIDEO_URL=$(echo "$STATUS_RES" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('response', {}).get('videoUrl', ''))" 2>/dev/null)

    echo "Attempt $i: Status = $STATUS"

    if [ "$STATUS" == "SUCCESS" ] && [ ! -z "$VIDEO_URL" ]; then
        echo ""
        echo "🎉 VIDEO GENERATED SUCCESSFULLY!"
        echo "Video URL: $VIDEO_URL"
        echo ""
        
        # Save to file
        OUTPUT_FILE="videos/Liv_Kaur_Diwali_Lullaby.mp4"
        echo "Downloading to $OUTPUT_FILE..."
        mkdir -p videos
        curl -L "$VIDEO_URL" -o "$OUTPUT_FILE"
        echo "✅ Saved to $OUTPUT_FILE"
        exit 0
    fi

    if [ "$STATUS" == "FAILED" ]; then
        echo "❌ Video generation FAILED response:"
        echo "$STATUS_RES"
        exit 1
    fi

    sleep 5
done

echo "⚠️ Timeout waiting for video generation"
exit 1
