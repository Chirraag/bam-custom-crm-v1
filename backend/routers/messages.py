from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
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
    phone_number: Optional[str] = None  # Override client's phone
    from_phone_number: Optional[str] = None  # Operator's phone number


class SMSMessage(BaseModel):
    id: str
    client_id: str
    to_number: str
    from_number: str
    content: str
    direction: str
    status: str
    telnyx_message_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extract user ID from the Authorization header and get user details"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Extract user ID from Bearer token (format: "Bearer user_id")
    try:
        parts = authorization.split()
        if len(parts) == 2 and parts[0] == "Bearer":
            user_id = parts[1]

            # Get user details including phone number
            user_response = supabase.table("crm_users").select(
                "id, email, name, phone_number"
            ).eq("id", user_id).execute()

            if user_response.data:
                return user_response.data[0]
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user"
                )
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


@router.get("/test")
async def test_messages_endpoint():
    """Test endpoint to verify messages router is working"""
    try:
        return {
            "status":
            "Messages API is working",
            "timestamp":
            datetime.now().isoformat(),
            "telnyx_configured":
            bool(telnyx.api_key and TELNYX_MESSAGING_PROFILE_ID
                 and TELNYX_PHONE_NUMBER)
        }
    except Exception as e:
        logger.error(f"Test endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/client/{client_id}")
async def get_client_messages(
    client_id: str, 
    authorization: Optional[str] = Header(None)
):
    """Get SMS messages for a specific client - filtered by operator's phone number"""
    try:
        logger.info(f"Fetching messages for client: {client_id}")

        # Get current user
        user = get_current_user(authorization)
        user_id = user['id']
        user_phone = user.get('phone_number')

        if not user_phone:
            logger.warning(f"User {user_id} has no phone number assigned")
            return {
                "client_id": client_id,
                "client_phone": None,
                "messages": []
            }

        logger.info(f"User ID: {user_id}, Phone: {user_phone}")

        # First verify client exists
        client_response = supabase.table("clients").select(
            "id, primary_phone").eq("id", client_id).execute()
        if not client_response.data:
            logger.warning(f"Client with ID {client_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Client with ID {client_id} not found")

        logger.info(f"Client found: {client_response.data[0]}")

        # Get messages for this client where:
        # 1. Outbound: from_number matches operator's phone
        # 2. Inbound: to_number matches operator's phone
        messages_response = supabase.table("messages").select("*").eq(
            "client_id", client_id
        ).or_(
            f"from_number.eq.{user_phone},to_number.eq.{user_phone}"
        ).order("created_at").execute()

        logger.info(
            f"Found {len(messages_response.data)} messages for client {client_id} and operator phone {user_phone}"
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
async def send_sms(
    sms: SMSCreate,
    authorization: Optional[str] = Header(None)
):
    """Send SMS to a client"""
    try:
        logger.info(f"Attempting to send SMS to client: {sms.client_id}")
        logger.info(f"Message content: {sms.content[:50]}...")

        # Get current user
        user = get_current_user(authorization)
        user_id = user['id']
        user_phone = user.get('phone_number')

        if not user_phone and not sms.from_phone_number:
            logger.error(f"User {user_id} has no phone number assigned")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your account does not have a phone number assigned. Please contact the administrator."
            )

        logger.info(f"User ID: {user_id}, Phone: {user_phone}")

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
        to_phone_number = sms.phone_number or client.get("primary_phone")
        if not to_phone_number:
            logger.warning(
                f"No phone number available for client {sms.client_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No phone number available for this client")

        # Determine the "from" phone number - prioritize operator's phone
        from_number = user_phone if user_phone else (sms.from_phone_number if sms.from_phone_number else TELNYX_PHONE_NUMBER)

        logger.info(f"To number: {to_phone_number}")
        logger.info(f"From number: {from_number}")

        # Send SMS via Telnyx
        try:
            logger.info("Attempting to send SMS via Telnyx...")
            logger.info(f"From: {from_number}")
            logger.info(f"To: {to_phone_number}")
            logger.info(f"Message content (raw): {repr(sms.content)}"
                        )  # Show raw content with escape chars
            logger.info(f"Messaging Profile ID: {TELNYX_MESSAGING_PROFILE_ID}")

            # Preserve formatting: ensure newlines and emojis are maintained
            formatted_content = sms.content.strip(
            )  # Remove leading/trailing whitespace but preserve internal formatting

            telnyx_response = telnyx.Message.create(
                from_=from_number,
                to=to_phone_number,
                text=formatted_content,  # Use formatted content
                messaging_profile_id=TELNYX_MESSAGING_PROFILE_ID)

            logger.info(f"Telnyx response: {telnyx_response}")

            # Store message in database with proper to/from numbers
            message_data = {
                "client_id": sms.client_id,
                "to_number": to_phone_number,
                "from_number": from_number,
                "content": formatted_content,  # Store formatted content
                "direction": "outbound",
                "status": "sent",
                "telnyx_message_id": telnyx_response.id,
                "user_id": user_id,  # Store the operator who sent this message
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

            # If using operator's phone failed, try with default TELNYX_PHONE_NUMBER
            if from_number != TELNYX_PHONE_NUMBER:
                logger.info(f"Attempting fallback with default phone number {TELNYX_PHONE_NUMBER}...")
                try:
                    formatted_content = sms.content.strip()

                    telnyx_response_fallback = telnyx.Message.create(
                        from_=TELNYX_PHONE_NUMBER,
                        to=to_phone_number,
                        text=formatted_content,
                        messaging_profile_id=TELNYX_MESSAGING_PROFILE_ID)

                    logger.info(f"Fallback success: {telnyx_response_fallback}")

                    # Store successful message
                    message_data = {
                        "client_id": sms.client_id,
                        "to_number": to_phone_number,
                        "from_number": TELNYX_PHONE_NUMBER,
                        "content": formatted_content,
                        "direction": "outbound",
                        "status": "sent",
                        "telnyx_message_id": telnyx_response_fallback.id,
                        "user_id": user_id,
                        "created_at": datetime.utcnow().isoformat()
                    }

                    logger.info("Storing fallback message in database...")
                    db_response = supabase.table("messages").insert(
                        message_data).execute()
                    logger.info("Fallback message stored successfully")

                    return db_response.data[0]

                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")

            # Try alpha sender as last resort
            logger.info("Attempting fallback with alpha sender 'TESTCRM'...")

            # Fallback: Try sending with alpha sender
            try:
                formatted_content = sms.content.strip(
                )  # Preserve formatting for fallback too

                telnyx_response_alpha = telnyx.Message.create(
                    from_="TESTCRM",  # Alpha sender
                    to=to_phone_number,
                    text=formatted_content,  # Use formatted content
                    messaging_profile_id=TELNYX_MESSAGING_PROFILE_ID)

                logger.info(f"Alpha sender success: {telnyx_response_alpha}")

                # Store successful message with alpha sender
                message_data = {
                    "client_id": sms.client_id,
                    "to_number": to_phone_number,
                    "from_number": "TESTCRM",
                    "content": formatted_content,  # Store formatted content
                    "direction": "outbound",
                    "status": "sent",
                    "telnyx_message_id": telnyx_response_alpha.id,
                    "user_id": user_id,
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
                    "to_number": to_phone_number,
                    "from_number": from_number,
                    "content":
                    sms.content,  # Store original content even if failed
                    "direction": "outbound",
                    "status": "failed",
                    "user_id": user_id,
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

                # Store incoming message with proper to/from numbers
                message_data = {
                    "client_id": client_id,
                    "to_number": to_number,  # The operator's phone number
                    "from_number": from_number,  # The client's phone number
                    "content": message_content,  # Preserve original formatting
                    "direction": "inbound",
                    "status": "received",
                    "telnyx_message_id": telnyx_message_id,
                    "user_id": None,  # No user_id for inbound messages
                    "created_at": datetime.utcnow().isoformat()
                }

                supabase.table("messages").insert(message_data).execute()
                logger.info(f"Stored incoming message from client {client_id} to {to_number}")
            else:
                logger.warning(
                    f"Received SMS from unknown number: {from_number}")

                # Optional: Store message from unknown sender
                message_data = {
                    "client_id": None,  # or create a special "unknown" client
                    "to_number": to_number,
                    "from_number": from_number,
                    "content": message_content,
                    "direction": "inbound",
                    "status": "received",
                    "telnyx_message_id": telnyx_message_id,
                    "user_id": None,
                    "created_at": datetime.utcnow().isoformat()
                }
                # Uncomment if you want to store unknown messages:
                # supabase.table("messages").insert(message_data).execute()

        elif event_type in [
                "message.sent", "message.delivered", "message.failed"
        ]:
            # Handle message status updates
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