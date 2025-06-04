from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Google Calendar API settings
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Get the redirect URI dynamically or use the provided one
REDIRECT_URI = "https://zp1v56uxy8rdx5ypatb0ockcb9tr6a-oci3-ngejxxvp--5173--55edb8f4.local-credentialless.webcontainer-api.io/calendar/oauth2callback"

CLIENT_CONFIG = {
    "web": {
        "client_id":
        "478913790629-sf7ik8vpt2aqs56dm2roant8g3btdgeo.apps.googleusercontent.com",
        "client_secret": "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",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [REDIRECT_URI]
    }
}


class EventReminder(BaseModel):
    method: str = "popup"
    minutes: int = 10


class EventAttendee(BaseModel):
    email: str
    displayName: Optional[str] = None
    responseStatus: Optional[str] = "needsAction"


class EventBase(BaseModel):
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    attendees: Optional[List[EventAttendee]] = None
    color_id: Optional[str] = None
    reminders: Optional[List[EventReminder]] = None
    recurrence: Optional[List[str]] = None
    timezone: Optional[str] = "UTC"


class EventCreate(EventBase):
    pass


class EventUpdate(EventBase):
    pass


class CalendarCredentials(BaseModel):
    token: str
    refresh_token: Optional[str] = None
    token_uri: str
    client_id: str
    client_secret: str
    scopes: List[str]


def get_calendar_service(credentials_dict: dict):
    """Create Google Calendar service from credentials"""
    try:
        credentials = Credentials.from_authorized_user_info(
            credentials_dict, SCOPES)
        return build('calendar', 'v3', credentials=credentials)
    except Exception as e:
        logger.error(f"Error creating calendar service: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "status": "Calendar API is working",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/auth-url")
async def get_auth_url():
    """Get Google OAuth authorization URL"""
    try:
        flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES)
        flow.redirect_uri = REDIRECT_URI

        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to get refresh token
        )

        logger.info(f"Generated auth URL with redirect URI: {REDIRECT_URI}")
        logger.info(f"Auth URL: {auth_url}")
        return {"auth_url": auth_url, "state": state}
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Failed to generate auth URL: {str(e)}")


@router.get("/oauth2callback")
async def oauth2callback(code: str, state: Optional[str] = None):
    """Handle OAuth callback and return credentials"""
    try:
        logger.info(f"OAuth callback - Code: {code[:20]}...")
        logger.info(f"OAuth callback - State: {state}")
        logger.info(f"Using redirect URI: {REDIRECT_URI}")

        flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES)
        flow.redirect_uri = REDIRECT_URI

        # Exchange the authorization code for credentials
        flow.fetch_token(code=code)
        credentials = flow.credentials

        logger.info("Successfully obtained credentials")

        # Test the credentials by making a simple API call
        try:
            service = build('calendar', 'v3', credentials=credentials)
            # Test with a simple calendar list call
            calendar_list = service.calendarList().list().execute()
            logger.info(
                f"Credentials test successful - found {len(calendar_list.get('items', []))} calendars"
            )
        except Exception as test_error:
            logger.warning(f"Credential test failed: {str(test_error)}")

        return {
            "token":
            credentials.token,
            "refresh_token":
            credentials.refresh_token,
            "token_uri":
            credentials.token_uri,
            "client_id":
            credentials.client_id,
            "client_secret":
            credentials.client_secret,
            "scopes":
            credentials.scopes,
            "expiry":
            credentials.expiry.isoformat() if credentials.expiry else None
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"OAuth callback error: {error_msg}")

        # Provide specific error messages for common issues
        if "invalid_grant" in error_msg:
            detail = "The authorization code has expired or been used already. Please try authenticating again."
        elif "redirect_uri_mismatch" in error_msg:
            detail = f"Redirect URI mismatch. Expected: {REDIRECT_URI}"
        elif "invalid_client" in error_msg:
            detail = "Invalid client credentials. Please check your Google Console setup."
        else:
            detail = f"Authentication failed: {error_msg}"

        raise HTTPException(status_code=400, detail=detail)


@router.post("/oauth2callback")
async def oauth2callback_post(request: Request):
    """Alternative POST endpoint for OAuth callback"""
    try:
        body = await request.json()
        code = body.get("code")
        state = body.get("state")

        if not code:
            raise HTTPException(status_code=400,
                                detail="Authorization code is required")

        logger.info(f"OAuth POST callback - Code: {code[:20]}...")
        logger.info(f"OAuth POST callback - State: {state}")

        flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES)
        flow.redirect_uri = REDIRECT_URI

        flow.fetch_token(code=code)
        credentials = flow.credentials

        logger.info("Successfully obtained credentials via POST")

        return {
            "token":
            credentials.token,
            "refresh_token":
            credentials.refresh_token,
            "token_uri":
            credentials.token_uri,
            "client_id":
            credentials.client_id,
            "client_secret":
            credentials.client_secret,
            "scopes":
            credentials.scopes,
            "expiry":
            credentials.expiry.isoformat() if credentials.expiry else None
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"OAuth POST callback error: {error_msg}")

        if "invalid_grant" in error_msg:
            detail = "The authorization code has expired or been used already. Please try authenticating again."
        elif "redirect_uri_mismatch" in error_msg:
            detail = f"Redirect URI mismatch. Expected: {REDIRECT_URI}"
        elif "invalid_client" in error_msg:
            detail = "Invalid client credentials. Please check your Google Console setup."
        else:
            detail = f"Authentication failed: {error_msg}"

        raise HTTPException(status_code=400, detail=detail)


@router.get("/refresh-auth")
async def refresh_auth():
    """Get a fresh auth URL when the previous one fails"""
    try:
        # Clear any cached flow state and get a fresh auth URL
        flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES)
        flow.redirect_uri = REDIRECT_URI

        # Add timestamp to prevent caching issues
        import time
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=f"refresh_{int(time.time())}")

        logger.info(f"Generated fresh auth URL: {auth_url}")
        return {
            "auth_url": auth_url,
            "state": state,
            "message": "Fresh authentication URL generated"
        }
    except Exception as e:
        logger.error(f"Error generating fresh auth URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate fresh auth URL: {str(e)}")


@router.post("/events")
async def list_events(credentials: CalendarCredentials,
                      time_min: Optional[str] = None,
                      time_max: Optional[str] = None,
                      max_results: int = 100):
    """List calendar events"""
    try:
        credentials_dict = credentials.dict()
        service = get_calendar_service(credentials_dict)

        # Format time parameters
        if time_min:
            time_min = datetime.fromisoformat(time_min.replace(
                'Z', '+00:00')).isoformat()
        if time_max:
            time_max = datetime.fromisoformat(time_max.replace(
                'Z', '+00:00')).isoformat()

        events_result = service.events().list(calendarId='primary',
                                              timeMin=time_min,
                                              timeMax=time_max,
                                              maxResults=max_results,
                                              singleEvents=True,
                                              orderBy='startTime').execute()

        events = events_result.get('items', [])

        # Process events to ensure consistent format
        processed_events = []
        for event in events:
            processed_event = {
                'id': event.get('id'),
                'summary': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'start': event.get('start', {}),
                'end': event.get('end', {}),
                'attendees': event.get('attendees', []),
                'colorId': event.get('colorId'),
                'reminders': event.get('reminders', {}),
                'recurrence': event.get('recurrence', []),
                'created': event.get('created'),
                'updated': event.get('updated'),
                'creator': event.get('creator', {}),
                'organizer': event.get('organizer', {}),
                'status': event.get('status', 'confirmed')
            }
            processed_events.append(processed_event)

        return {"events": processed_events}
    except HttpError as e:
        logger.error(f"Google API error: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Google Calendar API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error listing events: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch events: {str(e)}")


@router.post("/events/create")
async def create_event(event: EventCreate, credentials: CalendarCredentials):
    """Create a new calendar event"""
    try:
        credentials_dict = credentials.dict()
        service = get_calendar_service(credentials_dict)

        # Prepare event body
        event_body = {
            'summary': event.summary,
            'description': event.description,
            'location': event.location,
            'start': {
                'dateTime': event.start_datetime.isoformat(),
                'timeZone': event.timezone,
            },
            'end': {
                'dateTime': event.end_datetime.isoformat(),
                'timeZone': event.timezone,
            },
        }

        # Add attendees
        if event.attendees:
            event_body['attendees'] = [{
                'email':
                attendee.email,
                'displayName':
                attendee.displayName,
                'responseStatus':
                attendee.responseStatus
            } for attendee in event.attendees]

        # Add color
        if event.color_id:
            event_body['colorId'] = event.color_id

        # Add reminders
        if event.reminders:
            event_body['reminders'] = {
                'useDefault':
                False,
                'overrides': [{
                    'method': reminder.method,
                    'minutes': reminder.minutes
                } for reminder in event.reminders]
            }
        else:
            event_body['reminders'] = {'useDefault': True}

        # Add recurrence
        if event.recurrence:
            event_body['recurrence'] = event.recurrence

        created_event = service.events().insert(calendarId='primary',
                                                body=event_body,
                                                sendUpdates='all').execute()

        return created_event
    except HttpError as e:
        logger.error(f"Google API error creating event: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Google Calendar API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Failed to create event: {str(e)}")


@router.put("/events/{event_id}")
async def update_event(event_id: str, event: EventUpdate,
                       credentials: CalendarCredentials):
    """Update an existing calendar event"""
    try:
        credentials_dict = credentials.dict()
        service = get_calendar_service(credentials_dict)

        # Get existing event first
        existing_event = service.events().get(calendarId='primary',
                                              eventId=event_id).execute()

        # Prepare updated event body
        event_body = {
            'summary': event.summary,
            'description': event.description,
            'location': event.location,
            'start': {
                'dateTime': event.start_datetime.isoformat(),
                'timeZone': event.timezone,
            },
            'end': {
                'dateTime': event.end_datetime.isoformat(),
                'timeZone': event.timezone,
            },
        }

        # Add attendees
        if event.attendees:
            event_body['attendees'] = [{
                'email':
                attendee.email,
                'displayName':
                attendee.displayName,
                'responseStatus':
                attendee.responseStatus
            } for attendee in event.attendees]

        # Add color
        if event.color_id:
            event_body['colorId'] = event.color_id

        # Add reminders
        if event.reminders:
            event_body['reminders'] = {
                'useDefault':
                False,
                'overrides': [{
                    'method': reminder.method,
                    'minutes': reminder.minutes
                } for reminder in event.reminders]
            }
        else:
            event_body['reminders'] = {'useDefault': True}

        # Add recurrence
        if event.recurrence:
            event_body['recurrence'] = event.recurrence

        updated_event = service.events().update(calendarId='primary',
                                                eventId=event_id,
                                                body=event_body,
                                                sendUpdates='all').execute()

        return updated_event
    except HttpError as e:
        logger.error(f"Google API error updating event: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Google Calendar API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Failed to update event: {str(e)}")


@router.delete("/events/{event_id}")
async def delete_event(event_id: str, credentials: CalendarCredentials):
    """Delete a calendar event"""
    try:
        credentials_dict = credentials.dict()
        service = get_calendar_service(credentials_dict)

        service.events().delete(calendarId='primary',
                                eventId=event_id,
                                sendUpdates='all').execute()

        return {"message": "Event deleted successfully"}
    except HttpError as e:
        logger.error(f"Google API error deleting event: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Google Calendar API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Failed to delete event: {str(e)}")


@router.post("/colors")
async def get_calendar_colors(credentials: CalendarCredentials):
    """Get available calendar colors"""
    try:
        credentials_dict = credentials.dict()
        service = get_calendar_service(credentials_dict)

        colors = service.colors().get().execute()
        return colors
    except HttpError as e:
        logger.error(f"Google API error getting colors: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Google Calendar API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting colors: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Failed to get colors: {str(e)}")


@router.get("/event/{event_id}")
async def get_event(event_id: str, credentials_json: str):
    """Get a specific event by ID"""
    try:
        credentials_dict = json.loads(credentials_json)
        service = get_calendar_service(credentials_dict)

        event = service.events().get(calendarId='primary',
                                     eventId=event_id).execute()

        return event
    except HttpError as e:
        logger.error(f"Google API error getting event: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Google Calendar API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting event: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Failed to get event: {str(e)}")
