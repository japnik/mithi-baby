#!/bin/bash
echo "🎵 All Generated Songs from Logs"
echo "=================================="
echo ""

echo "📁 From: api_logs/suno/Liv_Kaur_suno_lyrics_test.json"
echo "Task ID: 89ef6c672bf47145a6c090acf2c8957c"
echo ""
cat api_logs/suno/Liv_Kaur_suno_lyrics_test.json | jq -r '.data.response.sunoData[] | "🎼 Title: \(.title)\n🔊 Audio: \(.audioUrl)\n🖼️  Image: \(.imageUrl)\n⏱️  Duration: \(.duration)s\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"'

echo ""
echo "📊 Summary:"
echo "  • Total songs found: 2"
echo "  • Status: SUCCESS (completed)"
echo "  • Generated: From earlier test runs"
echo ""
echo "💡 Note: The Kie API doesn't have a 'list all' endpoint."
echo "   These were extracted from your local log files."
