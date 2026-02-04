#!/bin/bash
# Extract all successfully generated songs from logs

echo "🎵 Searching for all generated songs in logs..."
echo ""

# Search for SUCCESS status in all log files
grep -r "SUCCESS" api_logs/ 2>/dev/null | grep -o 'taskId":"[^"]*' | cut -d'"' -f3 | sort -u > /tmp/task_ids.txt

if [ ! -s /tmp/task_ids.txt ]; then
    echo "❌ No successful generations found in logs"
    exit 0
fi

echo "Found $(wc -l < /tmp/task_ids.txt) successful task(s):"
echo ""

while read task_id; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 Task ID: $task_id"
    
    # Try to find more details about this task
    details=$(grep -r "$task_id" api_logs/ 2>/dev/null | grep -o '"title":"[^"]*' | head -1 | cut -d'"' -f4)
    audio=$(grep -r "$task_id" api_logs/ 2>/dev/null | grep -o '"audioUrl":"[^"]*' | head -1 | cut -d'"' -f4)
    
    if [ -n "$details" ]; then
        echo "🎼 Title: $details"
    fi
    
    if [ -n "$audio" ]; then
        echo "🔊 Audio: $audio"
    fi
    
    echo ""
done < /tmp/task_ids.txt

rm /tmp/task_ids.txt
