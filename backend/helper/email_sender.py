import logging
import smtplib
import requests
import mimetypes
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Optional, Tuple
from config import SMTP_SERVER, SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, SENDER_NAME

logger = logging.getLogger(__name__)

class EmailSender:
    """Send emails using Gmail SMTP with HTML support and threading"""

    @staticmethod
    def send_email(to_email: str, subject: str, body: str,
                   reply_to_message_id: Optional[str] = None,
                   original_subject: Optional[str] = None,
                   attachments: Optional[list] = None) -> Tuple[bool, Optional[str]]:
        """
        Send email via Gmail SMTP with HTML formatting and threading support.

        Returns:
            Tuple[bool, Optional[str]]: (success, message_id)
        """
        try:
            logger.info(f"📧 Sending email to: {to_email}")

            # Create email message (modern API)
            message = EmailMessage()
            message["From"] = formataddr((SENDER_NAME, EMAIL_USERNAME))
            message["To"] = to_email

            # Generate unique Message-ID
            message_id = make_msgid(domain="vexalink.com")
            message["Message-ID"] = message_id

            # Threading headers
            if reply_to_message_id:
                message["In-Reply-To"] = reply_to_message_id
                message["References"] = reply_to_message_id
                if not subject.lower().startswith("re:"):
                    subject = f"Re: {original_subject or subject}"

            message["Subject"] = subject

            # Generate plain and HTML bodies
            html_body = EmailSender.convert_to_html(body)
            plain_text = EmailSender.convert_to_plain_text(body)

            message.set_content(plain_text)
            message.add_alternative(html_body, subtype="html")

            # Attach files (from public URLs like Supabase)
            if attachments:
                for attachment in attachments:
                    response = requests.get(attachment["url"])
                    response.raise_for_status()

                    file_bytes = response.content
                    filename = attachment["name"]
                    mime_type, _ = mimetypes.guess_type(filename)
                    maintype, subtype = (mime_type or "application/octet-stream").split("/")

                    message.add_attachment(
                        file_bytes,
                        maintype=maintype,
                        subtype=subtype,
                        filename=filename
                    )

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
        """Convert markdown-style formatting to minimal HTML"""
        import re
        html_body = body.replace('\n', '<br>')
        html_body = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html_body)
        return f"""<!DOCTYPE html>
<html>
  <body>{html_body}</body>
</html>"""

    @staticmethod
    def convert_to_plain_text(body: str) -> str:
        """Convert markdown formatting to plain text"""
        import re
        plain_text = re.sub(r'\*\*(.*?)\*\*', r'\1', body)
        plain_text = re.sub(r'<br>', '\n', plain_text)
        plain_text = re.sub(r'<[^>]+>', '', plain_text)
        return plain_text
