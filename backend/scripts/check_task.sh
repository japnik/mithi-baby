#!/bin/bash
# Check Suno task status via Kie API

if [ -z "$1" ]; then
    echo "Usage: ./check_task.sh <task_id>"
    echo ""
    echo "Example task IDs from your logs:"
    echo "  89ef6c672bf47145a6c090acf2c8957c"
    echo "  c2ec43399bc6182850116dc2262d46c9"
    exit 1
fi

TASK_ID="$1"
API_KEY="07776b4b0a27ef85581ac4b82b85d688"

echo "🔍 Checking task: $TASK_ID"
echo ""

curl -s -X GET \
  "https://api.kie.ai/api/v1/generate/record-info?taskId=$TASK_ID" \
  -H "Authorization: Bearer $API_KEY" | jq '.'

