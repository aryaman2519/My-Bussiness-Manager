import resend
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

if settings.resend_api_key:
    resend.api_key = settings.resend_api_key

def send_welcome_email(to_email: str, username: str, password: str, security_code: str):
    """
    Sends a welcome email to the newly registered owner with their credentials.
    Using Resend API.
    """
    if not settings.resend_api_key:
        logger.warning("Resend API Key not configured. Skipping welcome email.")
        return

    try:
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #2563eb;">Welcome to SmartStock 360!</h2>
                    <p>Dear {username},</p>
                    <p>Your account has been successfully created. We are excited to have you on board to manage your business inventory smarter and faster.</p>
                    
                    <div style="background-color: #f8fafc; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #475569;">Your Login Credentials</h3>
                        <p><strong>Username:</strong> {username}</p>
                        <p><strong>Password:</strong> {password}</p>
                        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 10px 0;">
                        <p><strong>Security Code:</strong> <span style="font-family: monospace; font-size: 1.2em; color: #ea580c;">{security_code}</span></p>
                        <p style="font-size: 0.9em; color: #64748b;">Keep this code safe! You will need it for password resets and identity verification.</p>
                    </div>
                    
                    <p style="color: #dc2626; font-size: 0.9em;">
                        <strong>Security Note:</strong> For your security, please change your password immediately after your first login.
                    </p>
                    
                    <p>Best Regards,<br>The SmartStock 360 Team</p>
                </div>
            </body>
        </html>
        """

        resend.Emails.send({
            "from": settings.from_email, # e.g. "SmartStock <onboarding@resend.dev>"
            "to": to_email,
            "subject": "Welcome to SmartStock 360 🚀",
            "html": html_content
        })
        logger.info(f"📧 Welcome email sent to {to_email}")

    except Exception as e:
        print(f"❌ EMAIL FAILED DEBUG: {str(e)}")
        if hasattr(e, 'response'):
             print(f"HTTP Response: {e.response}")
        logger.error(f"❌ Email failed: {e}")

def send_password_change_email(to_email: str, username: str, new_password: str):
    """Sends confirmation email after password change."""
    if not settings.resend_api_key:
        return

    try:
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #2563eb;">Password Changed</h2>
                    <p>Dear {username},</p>
                    <p>Your password was successfully changed using your Security Code authentication.</p>
                    <div style="background-color: #f8fafc; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p><strong>Username:</strong> {username}</p>
                        <p><strong>New Password:</strong> {new_password}</p>
                    </div>
                    <p>If you did not make this change, please contact support immediately.</p>
                </div>
            </body>
        </html>
        """

        resend.Emails.send({
            "from": settings.from_email,
            "to": to_email,
            "subject": "Your password has been updated",
            "html": html_content
        })
        logger.info(f"📧 Password change email sent to {to_email}")

    except Exception as e:
        logger.error(f"❌ Email failed: {e}")

def send_low_stock_alert(product_name: str, company_name: str, current_quantity: int, recipients: list[str]):
    """Sends a low stock alert to a list of recipients."""
    if not settings.resend_api_key or not recipients:
        return

    try:
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; border-left: 5px solid #dc2626;">
                    <h2 style="color: #dc2626;">Low Stock Warning</h2>
                    <p>The product <strong>{product_name}</strong> ({company_name}) has reached its low-stock limit.</p>
                    
                    <div style="background-color: #fee2e2; padding: 15px; margin: 20px 0; border-radius: 5px; color: #991b1b;">
                        <p style="margin: 0; font-size: 1.2em;">Remaining Quantity: <strong>{current_quantity}</strong></p>
                    </div>
                    
                    <p>Please restock this item soon to maintain inventory levels.</p>
                    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                    <p style="font-size: 0.9em; color: #64748b;">This is an automated alert from MY STORE MANAGER.</p>
                </div>
            </body>
        </html>
        """

        # Resend supports multiple recipients, but iterating ensures individual tracking/logs if needed.
        # Can also pass list to "to".
        # Let's iterate as per previous logic or use batch? Resend batch is separate endpoint.
        # Simple "to": ["a", "b"] works for getting same email.
        
        # Filter valid emails
        valid_recipients = [email for email in recipients if email]
        if not valid_recipients:
            return

        resend.Emails.send({
            "from": settings.from_email,
            "to": valid_recipients,
            "subject": f"ALERT: {product_name} is running low!",
            "html": html_content
        })
        logger.info(f"Low stock alert sent to {len(valid_recipients)} recipients")

    except Exception as e:
        logger.error(f"Failed to send low stock alert: {e}")

def send_customer_invoice_email(
    to_email: str, 
    customer_name: str, 
    business_name: str, 
    invoice_number: str, 
    pdf_bytes: bytes,
    reply_to_email: str = None
):
    """Sends the invoice PDF to the customer using Resend."""
    if not settings.resend_api_key:
        return

    try:
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #2563eb;">Invoice from {business_name}</h2>
                    <p>Dear {customer_name},</p>
                    <p>Thank you for shopping at <strong>{business_name}</strong>. Please find your digital invoice attached to this email.</p>
                    
                    <div style="background-color: #f8fafc; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 0;"><strong>Invoice Number:</strong> {invoice_number}</p>
                    </div>
                    
                    <p>We appreciate your business!</p>
                    
                    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                    <p style="font-size: 0.9em; color: #64748b;">This email was sent automatically by {business_name}.</p>
                </div>
            </body>
        </html>
        """

        # Prepare attachments
        # Resend expects list of dicts: {"content": list of ints, "filename": str}
        # pdf_bytes to list of ints
        pdf_content = list(pdf_bytes)

        params = {
            "from": f"{business_name} <{settings.from_email}>",
            "to": to_email,
            "subject": f"Invoice #{invoice_number} from {business_name}",
            "html": html_content,
            "attachments": [
                {
                    "content": pdf_content,
                    "filename": f"Invoice_{invoice_number}.pdf"
                }
            ]
        }
        
        if reply_to_email:
            params["reply_to"] = reply_to_email

        resend.Emails.send(params)
        logger.info(f"Invoice email sent to {to_email}")

    except Exception as e:
        logger.error(f"Failed to send invoice email to {to_email}: {e}")

def send_invoice_copy_email(
    to_email: str, 
    customer_name: str, 
    business_name: str, 
    invoice_number: str, 
    pdf_bytes: bytes
):
    """Sends a COPY of the invoice to the staff/owner using Resend."""
    if not settings.resend_api_key:
        return

    try:
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; border-left: 5px solid #8b5cf6;">
                    <h2 style="color: #8b5cf6;">Invoice Copy</h2>
                    <p>Hello,</p>
                    <p>This is a copy of the invoice generated for Customer: <strong>{customer_name}</strong>.</p>
                    
                    <div style="background-color: #f8fafc; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 0;"><strong>Invoice Number:</strong> {invoice_number}</p>
                        <p style="margin: 5px 0 0 0;"><strong>Generated By:</strong> {business_name}</p>
                    </div>
                    
                    <p>The invoice PDF is attached for your records.</p>
                    
                    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                    <p style="font-size: 0.9em; color: #64748b;">Internal Record - SmartStock 360</p>
                </div>
            </body>
        </html>
        """

        pdf_content = list(pdf_bytes)

        resend.Emails.send({
            "from": f"{business_name} (Record) <{settings.from_email}>",
            "to": to_email,
            "subject": f"[Copy] Invoice #{invoice_number} - {customer_name}",
            "html": html_content,
            "attachments": [
                {
                    "content": pdf_content,
                    "filename": f"Invoice_{invoice_number}.pdf"
                }
            ]
        })
        logger.info(f"Invoice RECORD copy sent to {to_email}")

    except Exception as e:
        logger.error(f"Failed to send invoice copy to {to_email}: {e}")
