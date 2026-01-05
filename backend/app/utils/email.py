import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("uvicorn")

def send_email_smtp(to_email: str, subject: str, html_content: str, attachment: dict = None):
    """
    Core function to send emails via Gmail SMTP.
    """
    if not settings.smtp_username or not settings.smtp_password:
        logger.warning("⚠️  SMTP details missing. Email not sent.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.from_email if settings.from_email else settings.smtp_username
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html_content, "html"))

        if attachment:
            # Expects attachment = {"filename": "invoice.pdf", "content": bytes}
            part = MIMEApplication(attachment["content"], Name=attachment["filename"])
            part['Content-Disposition'] = f'attachment; filename="{attachment["filename"]}"'
            msg.attach(part)

        # Connect to Gmail SMTP with Robust IP Failover
        import socket
        import ssl
        
        server = None
        last_error = None
        
        # 1. Resolve ALL IPv4 addresses
        try:
            # AF_INET = IPv4, SOCK_STREAM = TCP
            addr_info = socket.getaddrinfo(settings.smtp_server, settings.smtp_port, socket.AF_INET, socket.SOCK_STREAM)
            # addr_info is list of (family, type, proto, canonname, sockaddr)
            # sockaddr is (ip, port)
            ips = list(set([info[4][0] for info in addr_info])) # Deduplicate IPs
            logger.info(f"Resolved Gmail IPs: {ips}")
        except Exception as e:
            logger.error(f"DNS Resolution failed: {e}")
            ips = [settings.smtp_server] # Fallback to hostname

        # 2. Prepare SSL Context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # 3. Try connecting to each IP
        for ip in ips:
            try:
                logger.info(f"Attempting connection to {ip}:{settings.smtp_port}...")
                if settings.smtp_port == 465:
                    server = smtplib.SMTP_SSL(ip, settings.smtp_port, context=context, timeout=10)
                else:
                    server = smtplib.SMTP(ip, settings.smtp_port, timeout=10)
                    server.starttls(context=context)
                
                # If we get here, connection successful
                logger.info(f"✅ Connected to {ip}")
                last_error = None
                break
            except Exception as e:
                logger.warning(f"Failed to connect to {ip}: {e}")
                last_error = e
                continue
        
        if server is None:
             raise Exception(f"Could not connect to any Gmail IP. Last error: {last_error}")

        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Email sent to {to_email}")

    except Exception as e:
        logger.error(f"❌ SMTP Email Failed: {e}")
        print(f"SMTP ERROR: {e}") # Print to logs for Render dashboard visibility

def send_welcome_email(to_email: str, username: str, password: str, security_code: str):
    """
    Sends a welcome email with credentials to a new owner.
    """
    subject = "Welcome to SmartStock 360 🚀"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #6366f1; text-align: center;">Welcome to SmartStock 360!</h2>
        <p>Hi {username},</p>
        <p>Your business account has been successfully created. Here are your login details:</p>
        
        <div style="background-color: #f3f4f6; padding: 15px; border-radius: 6px; margin: 20px 0;">
            <p><strong>Username:</strong> {username}</p>
            <p><strong>Password:</strong> {password}</p>
            <p><strong>Security Code:</strong> <span style="font-family: monospace; font-size: 1.2em; color: #d946ef;">{security_code}</span></p>
        </div>

        <p><strong>Important:</strong> Please keep your Security Code safe. You will need it to reset your password if you forget it.</p>
        
        <a href="https://my-bussiness-manager.vercel.app/login" style="display: block; width: 200px; margin: 20px auto; padding: 12px; background-color: #6366f1; color: white; text-align: center; text-decoration: none; border-radius: 6px; font-weight: bold;">Login to Dashboard</a>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 12px; color: #666; text-align: center;">SmartStock 360 - Intelligent Inventory Management</p>
    </div>
    """
    send_email_smtp(to_email, subject, html_content)


def send_password_change_email(to_email: str, username: str, new_password: str):
    """
    Sends notification when password is changed.
    """
    subject = "Your password has been updated"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">Password Updated</h2>
        <p>Hello {username},</p>
        <p>Your password for SmartStock 360 has been successfully changed.</p>
        
        <p>Your new password is: <strong>{new_password}</strong></p>
        
        <p>If you did not make this change, please contact support immediately.</p>
    </div>
    """
    send_email_smtp(to_email, subject, html_content)


def send_low_stock_alert(product_name: str, company_name: str, current_quantity: int, recipients: list):
    """
    Sends an alert when stock is running low.
    """
    if not recipients:
        logger.warning(f"⚠️ Low Stock Alert: No recipients found for {product_name}")
        return

    subject = f"⚠️ Low Stock Alert: {product_name}"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ef4444; border-radius: 8px;">
        <h2 style="color: #ef4444;">⚠️ Low Stock Alert</h2>
        <p><strong>Product:</strong> {product_name}</p>
        <p><strong>Company:</strong> {company_name}</p>
        <p><strong>Current Quantity:</strong> {current_quantity}</p>
        <br>
        <p>Please restock immediately.</p>
        <a href="https://my-bussiness-manager.vercel.app/stock" style="background-color: #ef4444; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Update Stock Now</a>
    </div>
    """
    
    for email in recipients:
        try:
            send_email_smtp(email, subject, html_content)
        except Exception as e:
            logger.error(f"Failed to send low stock alert to {email}: {e}")
            print(f"DEBUG: Failed to send to {email}: {e}")

def send_customer_invoice_email(to_email: str, customer_name: str, business_name: str, invoice_number: str, pdf_bytes: bytes):
    """
    Sends the invoice PDF to the customer.
    """
    subject = f"Invoice #{invoice_number} from {business_name}"
    html_content = f"""
    <p>Dear {customer_name},</p>
    <p>Please find attached your invoice <strong>#{invoice_number}</strong> from <strong>{business_name}</strong>.</p>
    <p>Thank you for your business!</p>
    """
    
    attachment = {
        "filename": f"Invoice_{invoice_number}.pdf",
        "content": pdf_bytes
    }
    
    send_email_smtp(to_email, subject, html_content, attachment)

def send_invoice_copy_email(to_email: str, customer_name: str, business_name: str, invoice_number: str, pdf_bytes: bytes):
    """
    Sends a copy of the invoice to the business owner for records.
    """
    subject = f"[Copy] Invoice #{invoice_number} - {customer_name}"
    html_content = f"""
    <p><strong>Invoice Record</strong></p>
    <p>Attached is the invoice generated for <strong>{customer_name}</strong>.</p>
    <p>Invoice #: {invoice_number}</p>
    """

    attachment = {
        "filename": f"Invoice_{invoice_number}_Copy.pdf",
        "content": pdf_bytes
    }
    
    send_email_smtp(to_email, subject, html_content, attachment)
