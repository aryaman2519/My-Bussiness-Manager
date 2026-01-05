import requests
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def send_whatsapp_message(to_number: str, message_text: str = None, template_name: str = None, template_language: str = "en_US"):
    """
    Sends a WhatsApp message using the Meta Cloud API.
    
    Args:
        to_number (str): The recipient's phone number (with country code, e.g., '919876543210').
        message_text (str, optional): The text content for a freeform message. 
                                      Note: Only allowed if a user-initiated conversation is open (24h window).
        template_name (str, optional): The name of the approved template to send.
        template_language (str, optional): Language code for the template.
    """
    
    if not settings.whatsapp_phone_number_id or not settings.whatsapp_access_token:
        logger.warning("⚠️ WhatsApp configuration missing. Message not sent.")
        return None

    url = f"https://graph.facebook.com/v17.0/{settings.whatsapp_phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }

    # Default payload structure
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
    }

    if template_name:
        # Template Message (Initiating conversation)
        payload["type"] = "template"
        payload["template"] = {
            "name": template_name,
            "language": {"code": template_language}
        }
    elif message_text:
        # Text Message (Response within 24h window)
        payload["type"] = "text"
        payload["text"] = {"body": message_text}
    else:
        logger.error("❌ Send WhatsApp Error: Must provide either 'message_text' or 'template_name'.")
        return None

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"✅ WhatsApp sent to {to_number}: {data}")
        return data
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ WhatsApp API Error: {e.response.text}")
        print(f"WHATSAPP API ERROR: {e.response.text}") # Print for Render logs
        return None
    except Exception as e:
        logger.error(f"❌ WhatsApp Connection Failed: {e}")
        print(f"WHATSAPP CONNECTION ERROR: {e}")
        return None

def send_welcome_whatsapp(to_number: str, business_name: str, username: str):
    """
    Sends a welcome message via WhatsApp.
    Currently uses the standard 'hello_world' template for testing/sandbox.
    """
    # For Sandbox, we often only have 'hello_world' approved.
    # In Production, create a template named 'welcome_message' with variables.
    
    # Fallback/Test: hello_world
    return send_whatsapp_message(to_number, template_name="hello_world")

    # Future Production Implementation (Example):
    # return send_whatsapp_message(to_number, template_name="welcome_business", ...)

def send_low_stock_whatsapp(to_number: str, product_name: str, current_quantity: int):
    """
    Sends a low stock alert via WhatsApp.
    """
    # Ideally use a template: 'low_stock_alert'
    # For now, we might try text if the 24h window is open, or use a template.
    
    # NOTE: You cannot send freeform text (message_text) to a user who hasn't messaged you in 24h.
    # You MUST use a Template.
    
    # Placeholder: Using 'hello_world' as a signal, or assuming a template exists.
    # Since we can't create templates via API, we advise the user to create one.
    
    # Attempting to send a template if it existed, otherwise logging the intent.
    logger.info(f"🔔 (Mock) Low Stock WhatsApp to {to_number}: {product_name} is low ({current_quantity})")
    
    # Real call (Assuming template 'low_stock_alert' exists):
    # return send_whatsapp_message(to_number, template_name="low_stock_alert")
    
    # Verification Hack: Use hello_world just to prove connectivity
    return send_whatsapp_message(to_number, template_name="hello_world")
