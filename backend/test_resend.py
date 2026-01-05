import os
import sys

# Ensure we can import app modules
sys.path.append(os.getcwd())

from app.config import get_settings
import resend

try:
    settings = get_settings()
    
    print(f"--- Resend Test Configuration ---")
    print(f"API Key Loaded: {bool(settings.resend_api_key)}")
    print(f"Configured From: {settings.from_email}")
    
    if not settings.resend_api_key:
        print("❌ ERROR: No API Key found in settings/env.")
        sys.exit(1)

    resend.api_key = settings.resend_api_key

    # Attempt 1: Send with configured From address
    print(f"\n[Test 1] Attempting to send from '{settings.from_email}'...")
    try:
        r = resend.Emails.send({
            "from": settings.from_email,
            "to": "delivered@resend.dev", # Safe sink address
            "subject": "SmartStock Test (Configured)",
            "html": "<p>Test from configured address.</p>"
        })
        print(f"✅ Success! ID: {r.get('id')}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Attempt 2: Send with Default Resend Test Address (if Attempt 1 failed likely)
    print(f"\n[Test 2] Attempting to send from 'onboarding@resend.dev' (Fallback)...")
    try:
        r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": "delivered@resend.dev", 
            "subject": "SmartStock Test (Fallback)",
            "html": "<p>Test from onboarding address.</p>"
        })
        print(f"✅ Success! ID: {r.get('id')}")
    except Exception as e:
        print(f"❌ Failed: {e}")

except Exception as e:
    print(f"\n❌ Script Error: {e}")
