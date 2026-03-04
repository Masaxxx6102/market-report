import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from .logger_setup import logger

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailSender:
    """
    Sends the report via Gmail API.
    """
    def __init__(self, credentials_path="credentials.json", token_path="token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    logger.error(f"Gmail credentials not found at {self.credentials_path}. Please provide this file.")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        return creds

    def send_report(self, to_emails: list, subject: str, body: str, attachment_path: str):
        if not self.creds:
            logger.error("Not authenticated. Cannot send email.")
            return False

        service = build('gmail', 'v1', credentials=self.creds)
        
        message = MIMEMultipart()
        message['to'] = ", ".join(to_emails)
        message['subject'] = subject
        
        message.attach(MIMEText(body, 'plain'))
        
        # Attachment
        if attachment_path and os.path.exists(attachment_path):
            part = MIMEBase('application', 'octet-stream')
            with open(attachment_path, 'rb') as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment_path)}"')
            message.attach(part)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        try:
            sent_msg = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            logger.info(f"Email sent successfully. ID: {sent_msg['id']}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
