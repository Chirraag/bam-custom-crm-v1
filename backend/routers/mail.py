from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from database import get_db, supabase
import logging
from helper.email_sender import EmailSender
from helper.email_reciever import check_inbox 
import os

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

router = APIRouter()

class EmailBase(BaseModel):
    # Allow extra fields to be included in the model
    model_config = ConfigDict(extra="allow")

    message_id : Optional[str] = None
    in_reply_to : Optional[str] = None
    thread_id : Optional[str] = None
    client_id : str
    direction : Optional[str] = None
    from_address : Optional[str] = None
    to_address : List[str]
    subject : str
    raw_body : Optional[str] = None
    parsed_body : str
    received_at : Optional[str] = None
    sent_at : Optional[str] = None


class EmailCreate(EmailBase):
    pass


@router.get("/{client_id}", response_model=List[dict])
async def get_mails(client_id: str):
    try:
        response = supabase.table("mails").select("*").eq("client_id", client_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"Failed to fetch notes: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch notes: {str(e)}")


@router.post("", status_code=status.HTTP_201_CREATED)
async def send_mail(email:EmailBase):
    try:
        EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
        # Validate required fields
        if not email.to_address[0] or not email.parsed_body or not email.subject:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Client ID, Created By, and Content are required")

        logger.info(f"Sending mail to: {email.to_address}")


        # Convert note to dict (this now includes extra fields thanks to extra="allow")
        email_data = email.model_dump()
        logger.info(f"Mail data before processing: {email_data}")
        # Add timestamps
        email_data["sent_at"] = datetime.now().isoformat()
        email_data["sent_at"] = email_data["sent_at"].replace("T", " ").replace("Z", "").split(".")[0]+"+5:30"
        logger.info(email_data["sent_at"])
        email_data["from_address"] = EMAIL_USERNAME

        # Remove None values to avoid overwriting database defaults
        email_data = {k: v for k, v in email_data.items() if v is not None}
        [success,message_id] = EmailSender.send_email(email.to_address[0],email.subject,email.parsed_body,email.in_reply_to,email.subject)
        email_data["message_id"] = message_id
        email_data["direction"] = "outgoing"
        if not email_data['thread_id']:
            email_data['thread_id'] = message_id
        logger.info(f"Successfully sent mail with ID: {email_data}")
        response = supabase.table("mails").insert(email_data).execute()
        new_mail = response.data[0]
        return new_mail
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to send mail: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to send mail: {str(e)}")


