#!/usr/bin/env python3
"""
Simple test script to generate a song directly without the frontend.
Usage: python3 test_song_generation.py
"""

import subprocess
import sys
import time
import json
import os

def test_song_generation():
    """Generate a test song for Bani Kaur"""
    
    song_id = f"test_bani_{int(time.time())}"
    log_file = f"api_logs/test_bani_{int(time.time())}.md"
    
    # Ensure log directory exists
    os.makedirs("api_logs", exist_ok=True)
    
    print("=" * 60)
    print("TESTING SONG GENERATION")
    print("=" * 60)
    print(f"\nSong ID: {song_id}")
    print(f"Log File: {log_file}")
    print("Baby Name: Bani Kaur")
    print("Language: Punjabi")
    print("Characters: mummy, papa")
    print("Occasion: Lori")
    print("\n" + "=" * 60)
    
    # Build command
    cmd = [
        sys.executable,  # Use same Python interpreter
        "-u",  # Unbuffered output
        "process_song.py",
        "--song_id", song_id,
        "--baby_name", "Bani Kaur",
        "--language", "Punjabi",
        "--characters", "mummy,papa",
        "--occasion", "Lori",
        "--log_file", log_file
    ]
    
    print(f"\nRunning command:")
    print(" ".join(cmd))
    print("\n" + "=" * 60)
    print("LIVE OUTPUT:")
    print("=" * 60 + "\n")
    
    # Run the process with live output
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Print output in real-time
    for line in process.stdout:
        print(line, end='')
    
    # Wait for completion
    process.wait()
    
    print("\n" + "=" * 60)
    print("PROCESS COMPLETED")
    print("=" * 60)
    
    # Check status file
    status_file = f"videos/{song_id}_status.json"
    if os.path.exists(status_file):
        print(f"\n✅ Status file created: {status_file}")
        with open(status_file, 'r') as f:
            status = json.load(f)
        print("\nFinal Status:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        print(f"\n❌ Status file not found: {status_file}")
    
    return process.returncode

if __name__ == "__main__":
    exit_code = test_song_generation()
    sys.exit(exit_code)
