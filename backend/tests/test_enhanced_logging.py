#!/usr/bin/env python3
"""Test script to demonstrate enhanced logging with aligned lyrics details"""
import subprocess
import sys

cmd = [
    sys.executable, "-u", "process_song.py",
    "--song_id", "enhanced_log_test",
    "--baby_name", "Bani Kaur",
    "--language", "Punjabi",
    "--characters", "mummy,papa",
    "--occasion", "Lori",
    "--log_file", "api_logs/enhanced_log_test.md"
]

print("🎵 Testing Enhanced Logging")
print("="*60)
print("Logs will be in: api_logs/enhanced_log_test.md")
print("="*60 + "\n")

subprocess.run(cmd)

print("\n" + "="*60)
print("✅ Check api_logs/enhanced_log_test.md for detailed logs!")
print("="*60)
