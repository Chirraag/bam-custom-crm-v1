from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database import get_db, supabase

router = APIRouter()

class MessageBase(BaseModel):
    sender_id: int
    recipient_id: int
    content: str
    is_read: bool = False

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_read: Optional[bool] = None

class Message(MessageBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

@router.get("/", response_model=List[Message])
async def get_messages():
    try:
        response = supabase.table("messages").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )

@router.get("/conversation/{user_id}/{other_id}", response_model=List[Message])
async def get_conversation(user_id: int, other_id: int):
    try:
        # Get messages where user is sender and other is recipient OR vice versa
        response = supabase.table("messages").select("*").or_(
            f"sender_id.eq.{user_id},recipient_id.eq.{other_id}",
            f"sender_id.eq.{other_id},recipient_id.eq.{user_id}"
        ).order("created_at").execute()
        
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversation: {str(e)}"
        )

@router.post("/", response_model=Message, status_code=status.HTTP_201_CREATED)
async def create_message(message: MessageCreate):
    try:
        # Check if sender exists
        sender_check = supabase.table("users").select("id").eq("id", message.sender_id).execute()
        if not sender_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sender with ID {message.sender_id} not found"
            )
        
        # Check if recipient exists
        recipient_check = supabase.table("users").select("id").eq("id", message.recipient_id).execute()
        if not recipient_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient with ID {message.recipient_id} not found"
            )
        
        response = supabase.table("messages").insert(message.dict()).execute()
        return response.data[0]
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create message: {str(e)}"
        )

@router.put("/{message_id}", response_model=Message)
async def update_message(message_id: int, message: MessageUpdate):
    try:
        # First check if message exists
        check_response = supabase.table("messages").select("*").eq("id", message_id).execute()
        if not check_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found"
            )
        
        # Filter out None values
        update_data = {k: v for k, v in message.dict().items() if v is not None}
        
        # Update message
        response = supabase.table("messages").update(update_data).eq("id", message_id).execute()
        return response.data[0]
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update message: {str(e)}"
        )

@router.put("/mark-read/{user_id}/{other_id}", status_code=status.HTTP_200_OK)
async def mark_conversation_as_read(user_id: int, other_id: int):
    try:
        # Mark all messages from other_id to user_id as read
        supabase.table("messages").update({"is_read": True}).eq("recipient_id", user_id).eq("sender_id", other_id).execute()
        
        return {"message": "Messages marked as read"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark messages as read: {str(e)}"
        )

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: int):
    try:
        # First check if message exists
        check_response = supabase.table("messages").select("*").eq("id", message_id).execute()
        if not check_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found"
            )
        
        # Delete message
        supabase.table("messages").delete().eq("id", message_id).execute()
        return None
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {str(e)}"
        )