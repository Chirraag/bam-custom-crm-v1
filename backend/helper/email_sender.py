# email_sender.py
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid
from typing import Optional, Tuple
from config import SMTP_SERVER, SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, SENDER_NAME

logger = logging.getLogger(__name__)

class EmailSender:
    """Send emails using Gmail SMTP with HTML support and threading"""
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str, 
                   reply_to_message_id: Optional[str] = None,
                   original_subject: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Send email via Gmail SMTP with HTML formatting and threading support
        
        Returns:
            Tuple[bool, Optional[str]]: (success, message_id)
        """
        try:
            logger.info(f"📧 Sending email to: {to_email}")
            
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = formataddr((SENDER_NAME, EMAIL_USERNAME))
            message["To"] = to_email
            
            # Generate unique Message-ID
            message_id = make_msgid(domain="vexalink.com")
            message["Message-ID"] = message_id
            
            # Handle threading for follow-up emails
            if reply_to_message_id:
                message["In-Reply-To"] = reply_to_message_id
                message["References"] = reply_to_message_id
                # For follow-ups, use "Re:" prefix if not already present
                if not subject.startswith("Re:"):
                    subject = f"Re: {original_subject or subject}"
            
            message["Subject"] = subject
            
            # Convert simple HTML to more proper HTML
            html_body = EmailSender.convert_to_html(body)
            
            # Create both plain text and HTML versions
            plain_text = EmailSender.convert_to_plain_text(body)
            
            # Attach both versions
            text_part = MIMEText(plain_text, "plain", "utf-8")
            html_part = MIMEText(html_body, "html", "utf-8")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                server.send_message(message)
            
            logger.info(f"✅ Email sent successfully to {to_email} (Message-ID: {message_id})")
            return True, message_id
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False, None
    
    @staticmethod
    def convert_to_html(body: str) -> str:
        """Convert markdown-style formatting to completely natural HTML"""
        # Convert line breaks to HTML
        html_body = body.replace('\n', '<br>')
        
        # Convert **bold** to <b>bold</b> (simpler than <strong>)
        import re
        html_body = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html_body)
        
        # Absolutely minimal HTML - no styling whatsoever
        html_template = f"""<!DOCTYPE html>
<html>
<body>
{html_body}
</body>
</html>"""
        
        return html_template
    
    @staticmethod
    def convert_to_plain_text(body: str) -> str:
        """Convert markdown formatting to plain text for fallback"""
        import re
        
        # Remove **bold** markdown and convert to plain text
        plain_text = re.sub(r'\*\*(.*?)\*\*', r'\1', body)  # Remove bold markers
        plain_text = re.sub(r'<br>', '\n', plain_text)     # Convert breaks to newlines
        plain_text = re.sub(r'<[^>]+>', '', plain_text)    # Remove any HTML tags
        
        return plain_text

# ===================================================================