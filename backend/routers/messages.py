from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import telnyx
import os
import logging
from database import get_db, supabase

router = APIRouter()
logger = logging.getLogger(__name__)

# Debug: Print environment variables (remove in production)
logger.info(f"TELNYX_API_KEY exists: {bool(os.getenv('TELNYX_API_KEY'))}")
logger.info(
    f"TELNYX_MESSAGING_PROFILE_ID: {os.getenv('TELNYX_MESSAGING_PROFILE_ID')}")
logger.info(f"TELNYX_PHONE_NUMBER: {os.getenv('TELNYX_PHONE_NUMBER')}")

# Initialize Telnyx
try:
    telnyx.api_key = os.getenv("TELNYX_API_KEY")
    TELNYX_MESSAGING_PROFILE_ID = os.getenv("TELNYX_MESSAGING_PROFILE_ID")
    TELNYX_PHONE_NUMBER = os.getenv("TELNYX_PHONE_NUMBER")

    if not telnyx.api_key:
        logger.error("TELNYX_API_KEY not found in environment variables")
    if not TELNYX_MESSAGING_PROFILE_ID:
        logger.error(
            "TELNYX_MESSAGING_PROFILE_ID not found in environment variables")
    if not TELNYX_PHONE_NUMBER:
        logger.error("TELNYX_PHONE_NUMBER not found in environment variables")

    logger.info("Telnyx configuration loaded successfully")
except Exception as e:
    logger.error(f"Error loading Telnyx configuration: {str(e)}")


class SMSCreate(BaseModel):
    client_id: str
    content: str
    phone_number: Optional[str] = None


class SMSMessage(BaseModel):
    id: str
    client_id: str
    phone_number: str
    content: str
    direction: str
    status: str
    telnyx_message_id: Optional[str] = None
    created_at: datetime


@router.get("/client/{client_id}")
async def get_client_messages(client_id: str):
    """Get all SMS messages for a specific client"""
    try:
        logger.info(f"Fetching messages for client: {client_id}")

        # First verify client exists
        client_response = supabase.table("clients").select(
            "id, primary_phone").eq("id", client_id).execute()
        if not client_response.data:
            logger.warning(f"Client with ID {client_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Client with ID {client_id} not found")

        logger.info(f"Client found: {client_response.data[0]}")

        # Get all messages for this client
        messages_response = supabase.table("messages").select("*").eq(
            "client_id", client_id).order("created_at").execute()

        logger.info(
            f"Found {len(messages_response.data)} messages for client {client_id}"
        )

        return {
            "client_id": client_id,
            "client_phone": client_response.data[0].get("primary_phone"),
            "messages": messages_response.data
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(
            f"Failed to fetch messages for client {client_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch messages: {str(e)}")


@router.post("/send")
async def send_sms(sms: SMSCreate):
    """Send SMS to a client"""
    try:
        logger.info(f"Attempting to send SMS to client: {sms.client_id}")
        logger.info(f"Message content: {sms.content[:50]}...")

        # Validate Telnyx configuration
        if not telnyx.api_key:
            logger.error("Telnyx API key not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SMS service not properly configured - missing API key")

        if not TELNYX_MESSAGING_PROFILE_ID:
            logger.error("Telnyx messaging profile ID not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=
                "SMS service not properly configured - missing messaging profile ID"
            )

        if not TELNYX_PHONE_NUMBER:
            logger.error("Telnyx phone number not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=
                "SMS service not properly configured - missing phone number")

        # Get client details
        logger.info(f"Looking up client {sms.client_id}")
        client_response = supabase.table("clients").select("*").eq(
            "id", sms.client_id).execute()
        if not client_response.data:
            logger.warning(f"Client with ID {sms.client_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {sms.client_id} not found")

        client = client_response.data[0]
        logger.info(
            f"Client found: {client.get('first_name')} {client.get('last_name')}"
        )

        # Use provided phone number or client's primary phone
        phone_number = sms.phone_number or client.get("primary_phone")
        if not phone_number:
            logger.warning(
                f"No phone number available for client {sms.client_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No phone number available for this client")

        logger.info(f"Using phone number: {phone_number}")

        # Send SMS via Telnyx
        try:
            logger.info("Attempting to send SMS via Telnyx...")
            logger.info(f"From: {TELNYX_PHONE_NUMBER}")
            logger.info(f"To: {phone_number}")
            logger.info(f"Messaging Profile ID: {TELNYX_MESSAGING_PROFILE_ID}")

            telnyx_response = telnyx.Message.create(
                from_=TELNYX_PHONE_NUMBER,
                to=phone_number,
                text=sms.content,
                messaging_profile_id=TELNYX_MESSAGING_PROFILE_ID)

            logger.info(f"Telnyx response: {telnyx_response}")

            # Store message in database
            message_data = {
                "client_id": sms.client_id,
                "phone_number": phone_number,
                "content": sms.content,
                "direction": "outbound",
                "status": "sent",
                "telnyx_message_id": telnyx_response.id,
                "created_at": datetime.utcnow().isoformat()
            }

            logger.info("Storing message in database...")
            db_response = supabase.table("messages").insert(
                message_data).execute()
            logger.info("Message stored successfully")

            return db_response.data[0]

        except Exception as telnyx_error:
            logger.error(
                f"Telnyx API error with phone number: {str(telnyx_error)}")
            logger.info("Attempting fallback with alpha sender 'TESTCRM'...")

            # Fallback: Try sending with alpha sender
            try:
                telnyx_response_alpha = telnyx.Message.create(
                    from_="TESTCRM",  # Alpha sender
                    to=phone_number,
                    text=sms.content,
                    messaging_profile_id=TELNYX_MESSAGING_PROFILE_ID)

                logger.info(f"Alpha sender success: {telnyx_response_alpha}")

                # Store successful message with alpha sender
                message_data = {
                    "client_id": sms.client_id,
                    "phone_number": phone_number,
                    "content": sms.content,
                    "direction": "outbound",
                    "status": "sent",
                    "telnyx_message_id": telnyx_response_alpha.id,
                    "created_at": datetime.utcnow().isoformat()
                }

                logger.info("Storing alpha sender message in database...")
                db_response = supabase.table("messages").insert(
                    message_data).execute()
                logger.info("Alpha sender message stored successfully")

                return db_response.data[0]

            except Exception as alpha_error:
                logger.error(f"Alpha sender also failed: {str(alpha_error)}")

                # Both phone number and alpha sender failed - store as failed
                message_data = {
                    "client_id": sms.client_id,
                    "phone_number": phone_number,
                    "content": sms.content,
                    "direction": "outbound",
                    "status": "failed",
                    "created_at": datetime.utcnow().isoformat()
                }

                try:
                    supabase.table("messages").insert(message_data).execute()
                    logger.info("Failed message stored in database")
                except Exception as db_error:
                    logger.error(
                        f"Failed to store failed message: {str(db_error)}")

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=
                    f"Failed to send SMS with both phone number and alpha sender. Phone error: {str(telnyx_error)}. Alpha error: {str(alpha_error)}"
                )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in send_sms: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to send SMS: {str(e)}")


@router.post("/webhook")
async def telnyx_webhook(request: Request):
    """Handle incoming SMS webhooks from Telnyx"""
    try:
        payload = await request.json()
        logger.info(f"Received Telnyx webhook: {payload}")

        # Extract message data from webhook
        data = payload.get("data", {})
        event_type = data.get("event_type")

        if event_type == "message.received":
            payload_data = data.get("payload", {})

            from_number = payload_data.get("from", {}).get("phone_number")
            to_number = payload_data.get("to", [{}])[0].get("phone_number")
            message_content = payload_data.get("text")
            telnyx_message_id = payload_data.get(
                "id")  # Message ID, not event ID

            logger.info(
                f"Processing message from {from_number} to {to_number}: {message_content}"
            )

            # Find client by phone number
            client_response = supabase.table("clients").select("*").eq(
                "primary_phone", from_number).execute()

            if client_response.data:
                client_id = client_response.data[0]["id"]

                # Store incoming message
                message_data = {
                    "client_id": client_id,
                    "phone_number": from_number,
                    "content": message_content,
                    "direction": "inbound",
                    "status": "received",
                    "telnyx_message_id": telnyx_message_id,
                    "created_at": datetime.utcnow().isoformat()
                }

                supabase.table("messages").insert(message_data).execute()
                logger.info(f"Stored incoming message from client {client_id}")
            else:
                logger.warning(
                    f"Received SMS from unknown number: {from_number}")

                # Optional: Store message from unknown sender
                message_data = {
                    "client_id": None,  # or create a special "unknown" client
                    "phone_number": from_number,
                    "content": message_content,
                    "direction": "inbound",
                    "status": "received",
                    "telnyx_message_id": telnyx_message_id,
                    "created_at": datetime.utcnow().isoformat()
                }
                # Uncomment if you want to store unknown messages:
                # supabase.table("messages").insert(message_data).execute()

        elif event_type in [
                "message.sent", "message.delivered", "message.failed"
        ]:
            # Handle message status updates - CORRECTED: Access payload data
            payload_data = data.get("payload", {})
            telnyx_message_id = payload_data.get("id")
            new_status = event_type.split(".")[1]  # sent, delivered, or failed

            # Update message status in database
            update_result = supabase.table("messages").update({
                "status":
                new_status
            }).eq("telnyx_message_id", telnyx_message_id).execute()

            logger.info(
                f"Updated message {telnyx_message_id} status to {new_status}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error processing webhook: {str(e)}")


@router.get("/client/{client_id}/phone-numbers")
async def get_client_phone_numbers(client_id: str):
    """Get all available phone numbers for a client"""
    try:
        client_response = supabase.table("clients").select("*").eq(
            "id", client_id).execute()
        if not client_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Client with ID {client_id} not found")

        client = client_response.data[0]

        # Extract all phone number fields
        phone_fields = [
            "primary_phone", "mobile_phone", "alternate_phone", "home_phone",
            "work_phone"
        ]
        phone_numbers = []

        for field in phone_fields:
            if client.get(field):
                phone_numbers.append({
                    "type": field.replace("_", " ").title(),
                    "number": client[field]
                })

        return {"client_id": client_id, "phone_numbers": phone_numbers}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(
            f"Failed to fetch phone numbers for client {client_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch phone numbers: {str(e)}")
