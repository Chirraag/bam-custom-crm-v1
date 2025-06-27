import os
import time
import ssl
import imaplib
import email
import logging

from email.header import decode_header
from email.utils import parsedate_to_datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from database import supabase  # make sure this is your initialized client

from mailparser_reply import EmailReplyParser

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# --- Pydantic model ---
class EmailBase(BaseModel):
    model_config = ConfigDict(extra="allow")
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    thread_id: Optional[str] = None
    client_id: Optional[str] = None
    direction: Optional[str] = None
    from_address: Optional[str] = None
    to_address: List[str]
    subject: Optional[str] = None
    raw_body: Optional[str] = None
    parsed_body: Optional[str] = None
    received_at: Optional[str] = None
    sent_at: Optional[str] = None

# --- Helpers ---
def clean(text: str) -> str:
    return text.replace("\r", "").replace("\n", " ").strip()

def get_env_var(name: str) -> str:
    val = os.getenv(name)
    if not val:
        logger.error(f"Environment variable {name} is not set.")
        raise RuntimeError(f"Missing env var {name}")
    return val

# --- Main polling function ---
def check_inbox():
    # load & validate config
    EMAIL_USERNAME = get_env_var("EMAIL_USERNAME")
    EMAIL_PASSWORD = get_env_var("EMAIL_PASSWORD")
    IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
    IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))

    while True:
        try:
            imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            imap.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            imap.select("INBOX")

            status, messages = imap.search(None, "UNSEEN")
            if status != "OK":
                logger.warning("IMAP search failed: %s", status)
                imap.logout()
                time.sleep(60)
                continue

            for eid in messages[0].split():
                try:
                    res, msg_data = imap.fetch(eid, "(RFC822)")
                    if res != "OK":
                        logger.warning("Fetch failed for ID %s: %s", eid, res)
                        continue

                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    sender = email.utils.parseaddr(msg["From"])[1]
                    subject, encoding = decode_header(msg.get("Subject", ""))[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="ignore")
                    subject = clean(subject)

                    message_id = msg.get("Message-ID")
                    in_reply_to = msg.get("In-Reply-To")

                    # get plaintext body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")
                    mail_message = EmailReplyParser(languages=["en"]).parse_reply(text=body)
                    body = clean(mail_message)

                    # resolve thread_id
                    thread_id = message_id
                    if in_reply_to:
                        lookup = (
                            supabase.table("mails")
                            .select("thread_id")
                            .eq("message_id", in_reply_to)
                            .execute()
                        )
                        if lookup.data:
                            thread_id = lookup.data[0]["thread_id"]

                    # parse date header
                    date_str = msg.get("Date", "")
                    received_dt = parsedate_to_datetime(date_str) if date_str else None
                    logger.info(received_dt)

                    # lookup client
                    resp = (
                        supabase.table("clients")
                        .select("id,primary_email,alternate_email")
                        .or_(f"primary_email.eq.{sender},alternate_email.eq.{sender}")
                        .execute()
                    )
                    client_id = resp.data[0]["id"] if resp.data else None

                    record = EmailBase(
                        message_id=message_id,
                        in_reply_to=in_reply_to,
                        thread_id=thread_id,
                        client_id=client_id,
                        direction="incoming",
                        from_address=sender,
                        to_address=[EMAIL_USERNAME],
                        subject=subject,
                        raw_body=body,
                        parsed_body=mail_message,
                        received_at=received_dt.isoformat() if received_dt else None,
                    )
                    email_data = record.model_dump()
                    # Insert into Supabase
                    insert_resp = supabase.table("mails").insert(email_data).execute()
                    logger.info("Inserted email %s into DB", body)

                except Exception as exc:
                    logger.exception("Error processing email ID %s: %s", eid, exc)

            imap.logout()
        except ConnectionRefusedError as cre:
            logger.error("Connection refused: %s", cre)
        except imaplib.IMAP4.error as ime:
            logger.error("IMAP protocol error: %s", ime)
        except ssl.SSLEOFError as sslerr:
            logger.error("SSL EOF error: %s", sslerr)
        except Exception as e:
            logger.exception("Unexpected polling error: %s", e)

