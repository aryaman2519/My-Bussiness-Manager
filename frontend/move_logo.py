
import shutil
import os

src = r"C:\Users\Aryaman\.gemini\antigravity\brain\366d26df-c671-483f-9845-003032914c39\uploaded_image_1766770294869.png"
dst = r"c:\Users\Aryaman\OneDrive\Documents\bussiness_Management\frontend\src\assets\logo.png"

try:
    if not os.path.exists(os.path.dirname(dst)):
        os.makedirs(os.path.dirname(dst))
    shutil.copy2(src, dst)
    print("✅ Logo copied successfully")
except Exception as e:
    print(f"❌ Failed to copy logo: {e}")
