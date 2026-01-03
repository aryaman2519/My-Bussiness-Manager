
import os
import time

files = ["credentials.db", "smartstock.db"]

print("Attempting to delete databases...")
for f in files:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"✅ Deleted {f}")
        except Exception as e:
            print(f"❌ Failed to delete {f}: {e}")
    else:
        print(f"⚠️ {f} not found.")
