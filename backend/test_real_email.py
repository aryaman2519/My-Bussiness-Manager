import os
import sys

# Ensure we can import app modules
sys.path.append(os.getcwd())

from app.config import get_settings
import resend

try:
    settings = get_settings()
    
    print(f"--- Real Email Test ---")
    print(f"From: {settings.from_email}")
    
    if not settings.resend_api_key:
        print("❌ ERROR: No API Key found.")
        sys.exit(1)

    resend.api_key = settings.resend_api_key

    # Target Email - inferred from previous error logs
    target_email = "aryamansaraf2@gmail.com" 
    
    print(f"Attempting to send to: {target_email}")
    print("If this fails with 403, it means this email is NOT the one registered with Resend.")

    try:
        r = resend.Emails.send({
            "from": settings.from_email,
            "to": target_email, 
            "subject": "SmartStock Real Test",
            "html": "<p>If you see this, email is working for your account!</p>"
        })
        print(f"✅ Email Sent Successfully! ID: {r.get('id')}")
        print("👉 Check your inbox (and spam folder) for 'aryamansaraf2@gmail.com'")
    except Exception as e:
        print(f"❌ Failed to send: {e}")
        if hasattr(e, 'response'):
             print(f"HTTP Response: {e.response}")

except Exception as e:
    print(f"\n❌ Script Error: {e}")
