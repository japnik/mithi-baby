#!/usr/bin/env python3
"""
Simple test script to verify backend dependencies and basic functionality
"""
import sys
import json

print("=" * 60)
print("BACKEND DEPENDENCY TEST")
print("=" * 60)

# Test 1: Import all required modules
print("\n1. Testing imports...")
try:
    import os
    import time
    import requests
    import argparse
    import datetime
    import subprocess
    import re
    import random
    print("   ✅ Standard library imports OK")
except ImportError as e:
    print(f"   ❌ Standard library import failed: {e}")
    sys.exit(1)

try:
    from supabase import create_client, Client
    print("   ✅ Supabase import OK")
except ImportError as e:
    print(f"   ❌ Supabase import failed: {e}")
    sys.exit(1)

# Test 2: Load config
print("\n2. Testing config loading...")
try:
    with open("api/config.json", "r") as f:
        config = json.load(f)
    print("   ✅ Config loaded")
    
    required_keys = ["GEMINI_API_KEY", "SUNO_API_KEY", "SUNO_BASE_URL", "SUPABASE_URL", "SUPABASE_KEY"]
    missing = [k for k in required_keys if not config.get(k)]
    if missing:
        print(f"   ⚠️  Missing config keys: {missing}")
    else:
        print("   ✅ All required config keys present")
except Exception as e:
    print(f"   ❌ Config loading failed: {e}")
    sys.exit(1)

# Test 3: Test Supabase connection (with timeout handling)
print("\n3. Testing Supabase connection...")
print("   NOTE: Skipping Supabase client creation (can hang)")
print("   Will test during actual song generation")

# Test 4: Check file structure
print("\n4. Checking file structure...")
required_dirs = ["videos", "api_logs", "api"]
for d in required_dirs:
    if os.path.exists(d):
        print(f"   ✅ {d}/ exists")
    else:
        print(f"   ❌ {d}/ missing")

print("\n" + "=" * 60)
print("DEPENDENCY TEST COMPLETE")
print("=" * 60)
print("\nAll critical dependencies are installed.")
print("Ready to test song generation.")
