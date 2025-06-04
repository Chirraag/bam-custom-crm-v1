import os
import base64
import email
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from database import supabase

logger = logging.getLogger(__name__)

@dataclass
class EmailData:
    gmail_message_id: str
    gmail_thread_id: str
    subject: str
    from_email: str
    to_email: str
    body_text: str
    body_html: str
    sent_at: datetime
    raw_data: Dict

class EmailService:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/gmail.modify']
        self.credentials_file = 'gmail_credentials.json'
        self.token_file = 'gmail_token.json'
        
    def get_gmail_service(self):
        """Get authenticated Gmail service"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        
        # If credentials are invalid, refresh or get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Gmail credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    raise Exception("Gmail credentials expired. Please re-authenticate.")
            else:
                raise Exception("No valid Gmail credentials found. Please authenticate first.")
            
            # Save refreshed credentials
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)
    
    def setup_gmail_auth(self, credentials_json: dict) -> str:
        """Setup Gmail authentication and return auth URL"""
        try:
            # Save credentials to file
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials_json, f)
            
            flow = Flow.from_client_secrets_file(
                self.credentials_file, 
                scopes=self.scopes,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # For installed apps
            )
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                prompt='consent'
            )
            
            return auth_url
        except Exception as e:
            logger.error(f"Error setting up Gmail auth: {e}")
            raise
    
    def complete_gmail_auth(self, auth_code: str) -> bool:
        """Complete Gmail authentication with authorization code"""
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_file, 
                scopes=self.scopes,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            # Save credentials
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            
            logger.info("Gmail authentication completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error completing Gmail auth: {e}")
            return False
    
    def get_client_by_email(self, email_address: str) -> Optional[Dict]:
        """Find client by email address"""
        try:
            result = supabase.table('clients').select('*').eq('primary_email', email_address).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error finding client by email {email_address}: {e}")
            return None
    
    def parse_gmail_message(self, message: Dict) -> EmailData:
        """Parse Gmail API message into EmailData object"""
        payload = message['payload']
        headers = payload.get('headers', [])
        
        # Extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
        to_email = next((h['value'] for h in headers if h['name'] == 'To'), '')
        
        # Parse date
        sent_at = datetime.fromtimestamp(int(message['internalDate']) / 1000)
        
        # Extract body
        body_text, body_html = self._extract_email_body(payload)
        
        return EmailData(
            gmail_message_id=message['id'],
            gmail_thread_id=message['threadId'],
            subject=subject,
            from_email=from_email,
            to_email=to_email,
            body_text=body_text,
            body_html=body_html,
            sent_at=sent_at,
            raw_data=message
        )
    
    def _extract_email_body(self, payload) -> Tuple[str, str]:
        """Extract text and HTML body from email payload"""
        body_text = ""
        body_html = ""
        
        def decode_base64(data):
            try:
                return base64.urlsafe_b64decode(data).decode('utf-8')
            except:
                return ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body_text = decode_base64(part['body']['data'])
                elif part['mimeType'] == 'text/html' and 'data' in part['body']:
                    body_html = decode_base64(part['body']['data'])
        else:
            if payload['mimeType'] == 'text/plain' and 'data' in payload['body']:
                body_text = decode_base64(payload['body']['data'])
            elif payload['mimeType'] == 'text/html' and 'data' in payload['body']:
                body_html = decode_base64(payload['body']['data'])
        
        return body_text, body_html
    
    def _extract_email_address(self, email_string: str) -> str:
        """Extract email address from 'Name <email@domain.com>' format"""
        if '<' in email_string and '>' in email_string:
            return email_string.split('<')[1].split('>')[0].strip()
        return email_string.strip()
    
    def store_email_in_db(self, email_data: EmailData, client_id: str, direction: str):
        """Store email in Supabase database"""
        try:
            # Check if email already exists
            existing = supabase.table('emails').select('id').eq('gmail_message_id', email_data.gmail_message_id).execute()
            
            if existing.data:
                logger.info(f"Email {email_data.gmail_message_id} already exists, skipping")
                return
            
            email_record = {
                'client_id': client_id,
                'gmail_message_id': email_data.gmail_message_id,
                'gmail_thread_id': email_data.gmail_thread_id,
                'direction': direction,
                'subject': email_data.subject,
                'body_text': email_data.body_text,
                'body_html': email_data.body_html,
                'from_email': email_data.from_email,
                'to_email': email_data.to_email,
                'sent_at': email_data.sent_at.isoformat(),
                'read_status': False
            }
            
            result = supabase.table('emails').insert(email_record).execute()
            logger.info(f"Stored email {email_data.gmail_message_id} for client {client_id}")
            
        except Exception as e:
            logger.error(f"Error storing email {email_data.gmail_message_id}: {e}")
    
    def sync_emails(self):
        """Main sync function - fetch and process new emails"""
        try:
            logger.info("Starting email sync...")
            service = self.get_gmail_service()
            
            # Get last sync timestamp
            last_sync = self.get_last_sync_time()
            
            # Fetch new messages from Gmail
            query = f"after:{last_sync.strftime('%Y/%m/%d')}" if last_sync else ""
            
            results = service.users().messages().list(
                userId='me', 
                q=query,
                maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} new messages")
            
            processed_count = 0
            # Process each message
            for message_ref in messages:
                try:
                    # Get full message details
                    message = service.users().messages().get(
                        userId='me', 
                        id=message_ref['id']
                    ).execute()
                    
                    email_data = self.parse_gmail_message(message)
                    
                    # Determine direction and find client
                    client = None
                    direction = 'outbound'
                    
                    # Check if email is from a client (inbound)
                    from_email = self._extract_email_address(email_data.from_email)
                    client = self.get_client_by_email(from_email)
                    
                    if client:
                        direction = 'inbound'
                    else:
                        # Check if email is to a client (outbound)
                        to_email = self._extract_email_address(email_data.to_email)
                        client = self.get_client_by_email(to_email)
                        direction = 'outbound'
                    
                    # Only store if related to a client
                    if client:
                        self.store_email_in_db(email_data, client['id'], direction)
                        processed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing message {message_ref['id']}: {e}")
                    continue
            
            # Update last sync time
            self.update_last_sync_time()
            logger.info(f"Email sync completed successfully. Processed {processed_count} emails.")
            
        except Exception as e:
            logger.error(f"Error during email sync: {e}")
            raise
    
    def get_last_sync_time(self) -> Optional[datetime]:
        """Get last sync timestamp from database"""
        try:
            result = supabase.table('email_sync_status').select('last_sync_at').order('created_at', desc=True).limit(1).execute()
            if result.data:
                return datetime.fromisoformat(result.data[0]['last_sync_at'].replace('Z', '+00:00'))
            return None
        except Exception as e:
            logger.error(f"Error getting last sync time: {e}")
            return None
    
    def update_last_sync_time(self):
        """Update last sync timestamp in database"""
        try:
            supabase.table('email_sync_status').insert({
                'last_sync_at': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error updating last sync time: {e}")
    
    def send_email(self, to_email: str, subject: str, body: str, client_id: str) -> bool:
        """Send email via Gmail API and store in database"""
        try:
            service = self.get_gmail_service()
            
            from email.mime.text import MIMEText
            
            # Create message
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = subject
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send email
            send_result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully. Message ID: {send_result['id']}")
            
            # Store in database
            email_data = EmailData(
                gmail_message_id=send_result['id'],
                gmail_thread_id=send_result['threadId'],
                subject=subject,
                from_email="me",  # Will be replaced with actual sender
                to_email=to_email,
                body_text=body,
                body_html="",
                sent_at=datetime.now(),
                raw_data=send_result
            )
            
            self.store_email_in_db(email_data, client_id, 'outbound')
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

# Create global instance
email_service = EmailService()