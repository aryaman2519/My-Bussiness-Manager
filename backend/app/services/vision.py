import logging
import base64
import asyncio
import os
import json
import re
import warnings

# Suppress the "switch to google.genai" warning for now to keep logs clean
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Use Gemini 2.5 Pro as it's available in your system
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

async def analyze_invoice_image(image_bytes: bytes) -> tuple[str, dict]:
    if not api_key:
        return "API Key Missing", {"status": "error"}

    try:
        # Step 1: Use a verified model from your list
        model = genai.GenerativeModel('gemini-2.0-flash') # Flash is faster for vision tasks

        prompt = """
        Return ONLY a JSON object. Do not include markdown formatting or backticks.
        
        Analyze this invoice image and extract the following:
        1. header_fields: Key-value pairs like Party Name, Mobile No, Date found in the top sections.
        2. item_table: The bounding box [ymin, xmin, ymax, xmax] of the main particulars table and its columns.
        
        Rules:
        - Coordinates must be normalized 0-1000.
        - Labels must be EXACTLY as written (e.g., 'IMEI NO.', 'BATTERY No.').
        
        JSON Structure:
        {
          "header_fields": [{"name": "id", "label": "Text", "box_2d": [ymin, xmin, ymax, xmax]}],
          "item_table": {
            "box_2d": [ymin, xmin, ymax, xmax],
            "columns": [{"name": "id", "label": "Column Text", "box_2d": [ymin, xmin, ymax, xmax]}]
          }
        }
        """

        # Step 2: Call the API
        response = await asyncio.to_thread(
            model.generate_content,
            [prompt, {"mime_type": "image/jpeg", "data": image_bytes}]
        )
        
        # Step 3: Clean response text (Remove ```json ... ```)
        clean_text = re.sub(r'```json|```', '', response.text).strip()
        mapping = json.loads(clean_text)
        
        # We return the base64 of the image as preview_html so the frontend can show the overlay
        preview_img_base64 = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"

        return preview_img_base64, {
            "status": "success",
            "mapping": mapping
        }

    except Exception as e:
        logging.error(f"Vision Error: {str(e)}")
        return f"Error: {str(e)}", {"status": "error"}