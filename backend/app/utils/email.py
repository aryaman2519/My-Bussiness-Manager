import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

def send_welcome_email(to_email: str, username: str, password: str, security_code: str):
    """
    Sends a welcome email to the newly registered owner with their credentials.
    This function should be called as a background task.
    """
    if not settings.smtp_username or not settings.smtp_password:
        logger.warning("SMTP credentials not configured. Skipping welcome email.")
        return

    try:
        subject = "Welcome to SmartStock 360 Management!"
        
        # HTML Body
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

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.smtp_from_email
        message["To"] = to_email

        message.attach(MIMEText(html_content, "html"))

        # Connect and Send
        # Connect and Send
        try:
            if settings.smtp_port == 465:
                # Use SSL for port 465
                with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port, timeout=10) as server:
                    server.login(settings.smtp_username, settings.smtp_password)
                    server.send_message(message)
            else:
                # Use STARTTLS for port 587 (or others)
                with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(settings.smtp_username, settings.smtp_password)
                    server.send_message(message)
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP Authentication Error: Check your username and password.")
            raise
        except Exception as e:
            logger.error(f"SMTP Connection Error: {e}")
            raise
            
        logger.info(f"Welcome email sent successfully to {to_email}")

    except Exception as e:
        logger.error(f"Failed to send welcome email into {to_email}: {str(e)}")

def send_password_change_email(to_email: str, username: str, new_password: str):
    """Sends confirmation email after password change."""
    if not settings.smtp_username or not settings.smtp_password:
        return

    try:
        subject = "Security Alert: Password Changed - SmartStock 360"
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
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.smtp_from_email
        message["To"] = to_email
        message.attach(MIMEText(html_content, "html"))

        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port, timeout=10) as server:
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
            
        logger.info(f"Password change email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send password email: {e}")

def send_low_stock_alert(product_name: str, company_name: str, current_quantity: int, recipients: list[str]):
    """
    Sends a low stock alert to a list of recipients (Owner + Staff).
    """
    if not settings.smtp_username or not settings.smtp_password or not recipients:
        return

    try:
        subject = f"ALERT: {product_name} is running low!"
        
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

        # Send to each recipient
        # Note: In a production system, we might use BCC or send individual emails. 
        # Here we loop for simplicity and personalization if needed later. 
        # Or just send one email with multiple To/Bcc. 
        # Loop is safer for avoiding "Reply All" confusion if that matters, but slower. 
        # Let's use loop for now as volume is low.
        
        if settings.smtp_port == 465:
             with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port, timeout=10) as server:
                server.login(settings.smtp_username, settings.smtp_password)
                for email in recipients:
                    if not email: continue
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = settings.smtp_from_email
                    msg["To"] = email
                    msg.attach(MIMEText(html_content, "html"))
                    server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                for email in recipients:
                    if not email: continue
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = settings.smtp_from_email
                    msg["To"] = email
                    msg.attach(MIMEText(html_content, "html"))
                    server.send_message(msg)

        logger.info(f"Low stock alert sent for {product_name} to {len(recipients)} recipients")


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
    """
    Sends the invoice PDF to the customer.
    """
    if not settings.smtp_username or not settings.smtp_password:
        return

    try:
        subject = f"Invoice #{invoice_number} from {business_name}"
        
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

        message = MIMEMultipart()
        message["Subject"] = subject
        # Display name in From header
        message["From"] = f"{business_name} <{settings.smtp_from_email}>"
        message["To"] = to_email
        
        if reply_to_email:
             message["Reply-To"] = reply_to_email

        # Attach body
        message.attach(MIMEText(html_content, "html"))

        # Attach PDF
        from email.mime.application import MIMEApplication
        pdf_attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        pdf_attachment.add_header(
            "Content-Disposition", 
            "attachment", 
            filename=f"Invoice_{invoice_number}.pdf"
        )
        message.attach(pdf_attachment)

        # Send
        if settings.smtp_port == 465:
             with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port, timeout=10) as server:
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)

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
    """
    Sends a COPY of the invoice to the staff/owner.
    """
    if not settings.smtp_username or not settings.smtp_password:
        return

    try:
        subject = f"[Copy] Invoice #{invoice_number} - {customer_name}"
        
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

        message = MIMEMultipart()
        message["Subject"] = subject
        message["From"] = f"{business_name} (Record) <{settings.smtp_from_email}>"
        message["To"] = to_email
        
        # Attach body
        message.attach(MIMEText(html_content, "html"))

        # Attach PDF
        from email.mime.application import MIMEApplication
        pdf_attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        pdf_attachment.add_header(
            "Content-Disposition", 
            "attachment", 
            filename=f"Invoice_{invoice_number}.pdf"
        )
        message.attach(pdf_attachment)

        # Send
        if settings.smtp_port == 465:
             with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port, timeout=10) as server:
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)

        logger.info(f"Invoice RECORD copy sent to {to_email}")

    except Exception as e:
        logger.error(f"Failed to send invoice copy to {to_email}: {e}")
