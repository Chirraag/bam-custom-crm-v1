from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database import supabase
from services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter()

class EmailSend(BaseModel):
    to_email: str
    subject: str
    body: str
    client_id: str

class GmailAuthSetup(BaseModel):
    credentials: Dict[str, Any]

class GmailAuthComplete(BaseModel):
    auth_code: str

@router.post("/setup-gmail-auth")
async def setup_gmail_auth(auth_data: GmailAuthSetup):
    """Setup Gmail authentication and return auth URL"""
    try:
        auth_url = email_service.setup_gmail_auth(auth_data.credentials)
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error setting up Gmail auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup Gmail authentication: {str(e)}"
        )

@router.post("/complete-gmail-auth")
async def complete_gmail_auth(auth_data: GmailAuthComplete):
    """Complete Gmail authentication with authorization code"""
    try:
        success = email_service.complete_gmail_auth(auth_data.auth_code)
        if success:
            return {"message": "Gmail authentication completed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to complete Gmail authentication"
            )
    except Exception as e:
        logger.error(f"Error completing Gmail auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete Gmail authentication: {str(e)}"
        )

@router.post("/send")
async def send_email(email_data: EmailSend):
    """Send email to client"""
    try:
        # Validate client exists
        client_check = supabase.table('clients').select('id, primary_email').eq('id', email_data.client_id).execute()
        if not client_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {email_data.client_id} not found"
            )
        
        client = client_check.data[0]
        
        # Verify email matches client's primary email
        if client['primary_email'] != email_data.to_email:
            logger.warning(f"Email mismatch: client email {client['primary_email']} vs requested {email_data.to_email}")
        
        # Send email
        success = email_service.send_email(
            email_data.to_email,
            email_data.subject,
            email_data.body,
            email_data.client_id
        )
        
        if success:
            return {"message": "Email sent successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

@router.get("/client/{client_id}")
async def get_client_emails(client_id: str, limit: int = 50, offset: int = 0):
    """Get email history for a specific client"""
    try:
        # Verify client exists
        client_check = supabase.table('clients').select('id').eq('id', client_id).execute()
        if not client_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found"
            )
        
        # Get emails for client
        emails_result = supabase.table('emails').select('*').eq('client_id', client_id).order('sent_at', desc=True).range(offset, offset + limit - 1).execute()
        
        return {"emails": emails_result.data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching client emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch client emails: {str(e)}"
        )

@router.get("/client/{client_id}/stats")
async def get_client_email_stats(client_id: str):
    """Get email statistics for a client"""
    try:
        # Verify client exists
        client_check = supabase.table('clients').select('id').eq('id', client_id).execute()
        if not client_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found"
            )
        
        # Get total email counts
        total_emails = supabase.table('emails').select('direction').eq('client_id', client_id).execute()
        
        # Get unread email count
        unread_emails = supabase.table('emails').select('id').eq('client_id', client_id).eq('direction', 'inbound').eq('read_status', False).execute()
        
        # Calculate statistics
        total_data = total_emails.data
        inbound_count = len([e for e in total_data if e['direction'] == 'inbound'])
        outbound_count = len([e for e in total_data if e['direction'] == 'outbound'])
        unread_count = len(unread_emails.data)
        
        return {
            "total_emails": len(total_data),
            "inbound_emails": inbound_count,
            "outbound_emails": outbound_count,
            "unread_emails": unread_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching email stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch email statistics: {str(e)}"
        )

@router.patch("/mark-read/{email_id}")
async def mark_email_read(email_id: str):
    """Mark an email as read"""
    try:
        # Check if email exists
        email_check = supabase.table('emails').select('id').eq('id', email_id).execute()
        if not email_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email with ID {email_id} not found"
            )
        
        # Update read status
        result = supabase.table('emails').update({
            'read_status': True,
            'updated_at': datetime.now().isoformat()
        }).eq('id', email_id).execute()
        
        return {"message": "Email marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking email as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark email as read: {str(e)}"
        )

@router.post("/sync")
async def trigger_email_sync():
    """Manually trigger email sync"""
    try:
        email_service.sync_emails()
        return {"message": "Email sync completed successfully"}
    except Exception as e:
        logger.error(f"Error during manual sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email sync failed: {str(e)}"
        )

@router.get("/sync-status")
async def get_sync_status():
    """Get last email sync status"""
    try:
        result = supabase.table('email_sync_status').select('*').order('created_at', desc=True).limit(1).execute()
        
        if result.data:
            return {"last_sync": result.data[0]}
        else:
            return {"last_sync": None}
            
    except Exception as e:
        logger.error(f"Error fetching sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sync status: {str(e)}"
        )