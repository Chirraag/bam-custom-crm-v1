from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import os

router = APIRouter()

# Google Calendar API settings
SCOPES = ['https://www.googleapis.com/auth/calendar']
CLIENT_CONFIG = {
    "web": {
        "client_id": "478913790629-sf7ik8vpt2aqs56dm2roant8g3btdgeo.apps.googleusercontent.com",
        "client_secret": "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",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:5173/calendar/oauth2callback"]
    }
}

class EventBase(BaseModel):
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    attendees: Optional[List[str]] = None
    color_id: Optional[str] = None
    reminders: Optional[dict] = None

class EventCreate(EventBase):
    pass

class EventUpdate(EventBase):
    pass

class Event(EventBase):
    id: str
    created: datetime
    updated: datetime
    creator: dict
    organizer: dict
    status: str

def get_calendar_service(credentials_dict: dict):
    credentials = Credentials.from_authorized_user_info(credentials_dict, SCOPES)
    return build('calendar', 'v3', credentials=credentials)

@router.get("/auth-url")
async def get_auth_url():
    flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES)
    flow.redirect_uri = "http://localhost:5173/calendar/oauth2callback"
    auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    return {"auth_url": auth_url}

@router.post("/oauth2callback")
async def oauth2callback(code: str):
    flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES)
    flow.redirect_uri = "http://localhost:5173/calendar/oauth2callback"
    
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        return {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/events")
async def list_events(credentials_json: str, time_min: Optional[str] = None, time_max: Optional[str] = None):
    try:
        credentials_dict = json.loads(credentials_json)
        service = get_calendar_service(credentials_dict)
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events")
async def create_event(event: EventCreate, credentials_json: str):
    try:
        credentials_dict = json.loads(credentials_json)
        service = get_calendar_service(credentials_dict)
        
        event_body = {
            'summary': event.summary,
            'description': event.description,
            'location': event.location,
            'start': {
                'dateTime': event.start_datetime.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': event.end_datetime.isoformat(),
                'timeZone': 'UTC',
            },
        }
        
        if event.attendees:
            event_body['attendees'] = [{'email': email} for email in event.attendees]
        if event.color_id:
            event_body['colorId'] = event.color_id
        if event.reminders:
            event_body['reminders'] = event.reminders
            
        created_event = service.events().insert(
            calendarId='primary',
            body=event_body,
            sendUpdates='all'
        ).execute()
        
        return created_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/events/{event_id}")
async def update_event(event_id: str, event: EventUpdate, credentials_json: str):
    try:
        credentials_dict = json.loads(credentials_json)
        service = get_calendar_service(credentials_dict)
        
        event_body = {
            'summary': event.summary,
            'description': event.description,
            'location': event.location,
            'start': {
                'dateTime': event.start_datetime.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': event.end_datetime.isoformat(),
                'timeZone': 'UTC',
            },
        }
        
        if event.attendees:
            event_body['attendees'] = [{'email': email} for email in event.attendees]
        if event.color_id:
            event_body['colorId'] = event.color_id
        if event.reminders:
            event_body['reminders'] = event.reminders
            
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event_body,
            sendUpdates='all'
        ).execute()
        
        return updated_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/events/{event_id}")
async def delete_event(event_id: str, credentials_json: str):
    try:
        credentials_dict = json.loads(credentials_json)
        service = get_calendar_service(credentials_dict)
        
        service.events().delete(
            calendarId='primary',
            eventId=event_id,
            sendUpdates='all'
        ).execute()
        
        return {"message": "Event deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/colors")
async def get_calendar_colors(credentials_json: str):
    try:
        credentials_dict = json.loads(credentials_json)
        service = get_calendar_service(credentials_dict)
        
        colors = service.colors().get().execute()
        return colors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))