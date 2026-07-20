#!/usr/bin/env python3
"""
Office 365 Integration for CRM Email Automation
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import time
import logging
from functools import wraps
import sqlite3
from pathlib import Path

class Office365Integration:
    """Office 365 integration for automated email communications with robust error handling"""
    
    def __init__(self):
        self.client_id = os.getenv('OFFICE365_CLIENT_ID')
        self.client_secret = os.getenv('OFFICE365_CLIENT_SECRET')
        self.tenant_id = os.getenv('OFFICE365_TENANT_ID')
        self.redirect_uri = os.getenv('OFFICE365_REDIRECT_URI', 'http://localhost:8000/auth/callback')
        
        # SMTP settings for Office 365
        self.smtp_server = 'smtp.office365.com'
        self.smtp_port = 587
        self.smtp_username = os.getenv('OFFICE365_EMAIL')
        self.smtp_password = os.getenv('OFFICE365_PASSWORD')
        
        # Graph API endpoints
        self.graph_base_url = 'https://graph.microsoft.com/v1.0'
        self.auth_base_url = 'https://login.microsoftonline.com'
        
        # Token management
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.token_file = Path('data/office365_tokens.json')
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load saved tokens
        self._load_tokens()
        
        # Create data directory if it doesn't exist
        self.token_file.parent.mkdir(exist_ok=True)
    
    def get_auth_url(self) -> str:
        """Get OAuth2 authorization URL"""
        scopes = [
            'https://graph.microsoft.com/Mail.Send',
            'https://graph.microsoft.com/Mail.Read',
            'https://graph.microsoft.com/Calendars.ReadWrite',
            'https://graph.microsoft.com/Contacts.ReadWrite'
        ]
        
        auth_url = (
            f"{self.auth_base_url}/{self.tenant_id}/oauth2/v2.0/authorize?"
            f"client_id={self.client_id}&"
            f"response_type=code&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={' '.join(scopes)}&"
            f"response_mode=query"
        )
        
        return auth_url
    
    def get_access_token(self, auth_code: str) -> Dict:
        """Exchange authorization code for access token"""
        token_url = f"{self.auth_base_url}/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            return token_data
        else:
            raise Exception(f"Failed to get access token: {response.text}")
    
    def _load_tokens(self):
        """Load tokens from persistent storage"""
        try:
            if self.token_file.exists():
                with open(self.token_file, 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get('access_token')
                    self.refresh_token = tokens.get('refresh_token')
                    expires_at_str = tokens.get('expires_at')
                    if expires_at_str:
                        self.token_expires_at = datetime.fromisoformat(expires_at_str)
        except Exception as e:
            self.logger.warning(f"Failed to load tokens: {e}")
    
    def _save_tokens(self, token_data: Dict):
        """Save tokens to persistent storage"""
        try:
            expires_in = token_data.get('expires_in', 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            tokens = {
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token') or self.refresh_token,
                'expires_at': expires_at.isoformat()
            }
            
            with open(self.token_file, 'w') as f:
                json.dump(tokens, f)
                
            self.token_expires_at = expires_at
            self.logger.info("Tokens saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save tokens: {e}")
    
    def _is_token_expired(self) -> bool:
        """Check if the current access token is expired"""
        if not self.access_token or not self.token_expires_at:
            return True
        
        # Add 5 minute buffer
        return datetime.now() + timedelta(minutes=5) >= self.token_expires_at
    
    def refresh_access_token(self) -> Dict:
        """Refresh the access token with robust error handling"""
        if not self.refresh_token:
            raise Exception("No refresh token available. Please re-authenticate.")
        
        token_url = f"{self.auth_base_url}/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(token_url, data=data, timeout=30)
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data.get('access_token')
                    
                    # Update refresh token if provided
                    if 'refresh_token' in token_data:
                        self.refresh_token = token_data['refresh_token']
                    
                    # Save tokens
                    self._save_tokens(token_data)
                    
                    self.logger.info("Access token refreshed successfully")
                    return token_data
                    
                elif response.status_code == 400:
                    error_data = response.json()
                    error_code = error_data.get('error')
                    
                    if error_code == 'invalid_grant':
                        # Refresh token expired or invalid
                        self.logger.error("Refresh token expired. Re-authentication required.")
                        self.access_token = None
                        self.refresh_token = None
                        self.token_expires_at = None
                        raise Exception("Refresh token expired. Please re-authenticate.")
                    else:
                        raise Exception(f"Token refresh failed: {error_data.get('error_description', response.text)}")
                        
                else:
                    self.logger.warning(f"Token refresh attempt {attempt + 1} failed: {response.status_code} - {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        raise Exception(f"Failed to refresh access token after {self.max_retries} attempts: {response.text}")
                        
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise Exception(f"Network error after {self.max_retries} attempts: {e}")
        
        # This should never be reached due to the raise statements above
        raise Exception("Unexpected error in token refresh")
    
    def _ensure_valid_token(self):
        """Ensure we have a valid access token, refreshing if necessary"""
        if self._is_token_expired():
            if self.refresh_token:
                self.refresh_access_token()
            else:
                raise Exception("No valid access token and no refresh token available. Please re-authenticate.")
    
    def send_email_graph_api(self, to_email: str, subject: str, body: str, 
                            cc_emails: Optional[List[str]] = None, attachments: Optional[List[str]] = None) -> Dict:
        """Send email using Microsoft Graph API with robust error handling"""
        self._ensure_valid_token()
        
        if not self.access_token:
            raise Exception("No valid access token available. Please authenticate first.")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Build recipients
        to_recipients = [{'emailAddress': {'address': to_email}}]
        cc_recipients = []
        if cc_emails:
            cc_recipients = [{'emailAddress': {'address': email}} for email in cc_emails]
        
        # Build message
        message = {
            'message': {
                'subject': subject,
                'body': {
                    'contentType': 'HTML',
                    'content': body
                },
                'toRecipients': to_recipients,
                'ccRecipients': cc_recipients
            }
        }
        
        # Add attachments if provided
        if attachments:
            message['message']['attachments'] = []
            for attachment_path in attachments:
                if os.path.exists(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        content = f.read()
                        import base64
                        encoded_content = base64.b64encode(content).decode()
                        
                        attachment = {
                            '@odata.type': '#microsoft.graph.fileAttachment',
                            'name': os.path.basename(attachment_path),
                            'contentBytes': encoded_content
                        }
                        message['message']['attachments'].append(attachment)
        
        # Send email with retry logic
        send_url = f"{self.graph_base_url}/me/sendMail"
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(send_url, headers=headers, json=message, timeout=30)
                
                if response.status_code == 202:
                    self.logger.info(f"Email sent successfully to {to_email}")
                    return {'status': 'sent', 'message': 'Email sent successfully'}
                    
                elif response.status_code == 401:
                    # Token might be expired, try to refresh once
                    if attempt == 0:
                        self.logger.info("Token expired, attempting refresh")
                        self.refresh_access_token()
                        headers['Authorization'] = f'Bearer {self.access_token}'
                        continue
                    else:
                        raise Exception("Authentication failed after token refresh")
                        
                elif response.status_code == 429:
                    # Rate limited, wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                    
                else:
                    error_msg = f"Failed to send email: {response.status_code} - {response.text}"
                    self.logger.warning(f"Send attempt {attempt + 1} failed: {error_msg}")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    else:
                        raise Exception(error_msg)
                        
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Network error on send attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise Exception(f"Network error after {self.max_retries} attempts: {e}")
        
        raise Exception("Unexpected error in email sending")
    
    def send_email_smtp(self, to_email: str, subject: str, body: str, 
                       cc_emails: Optional[List[str]] = None, attachments: Optional[List[str]] = None) -> Dict:
        """Send email using SMTP (fallback method)"""
        if not self.smtp_username or not self.smtp_password:
            raise Exception("SMTP credentials not configured")
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # Add body
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(attachment_path)}'
                            )
                            msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)
            
            server.send_message(msg, to_addrs=recipients)
            server.quit()
            
            return {'status': 'sent', 'message': 'Email sent successfully via SMTP'}
            
        except Exception as e:
            raise Exception(f"Failed to send email via SMTP: {str(e)}")
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   cc_emails: Optional[List[str]] = None, attachments: Optional[List[str]] = None) -> Dict:
        """Send email (tries Graph API first, falls back to SMTP) with comprehensive error handling"""
        last_error = None
        
        # Try Graph API first if we have credentials
        if self.client_id and self.client_secret:
            try:
                return self.send_email_graph_api(to_email, subject, body, cc_emails, attachments)
            except Exception as e:
                self.logger.warning(f"Graph API email failed: {e}")
                last_error = e
        
        # Fallback to SMTP if Graph API fails or is not configured
        if self.smtp_username and self.smtp_password:
            try:
                return self.send_email_smtp(to_email, subject, body, cc_emails, attachments)
            except Exception as e:
                self.logger.error(f"SMTP email also failed: {e}")
                if last_error:
                    raise Exception(f"Both Graph API and SMTP failed. Graph API: {last_error}, SMTP: {e}")
                else:
                    raise e
        
        # No valid configuration available
        if last_error:
            raise last_error
        else:
            raise Exception("No email configuration available (neither Graph API nor SMTP credentials configured)")
    
    def create_calendar_event(self, subject: str, start_time: datetime, end_time: datetime,
                             attendees: Optional[List[str]] = None, location: Optional[str] = None, 
                             body: Optional[str] = None) -> Dict:
        """Create calendar event"""
        if not self.access_token:
            raise Exception("No access token available. Please authenticate first.")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Build attendees
        attendee_list = []
        if attendees:
            attendee_list = [
                {
                    'emailAddress': {'address': email, 'name': email.split('@')[0]},
                    'type': 'required'
                }
                for email in attendees
            ]
        
        # Build event
        event = {
            'subject': subject,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC'
            },
            'attendees': attendee_list
        }
        
        if location:
            event['location'] = {'displayName': location}
        
        if body:
            event['body'] = {'contentType': 'HTML', 'content': body}
        
        # Create event
        events_url = f"{self.graph_base_url}/me/events"
        response = requests.post(events_url, headers=headers, json=event)
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create calendar event: {response.text}")
    
    def get_emails(self, folder: str = 'inbox', limit: int = 10) -> List[Dict]:
        """Get emails from specified folder"""
        if not self.access_token:
            raise Exception("No access token available. Please authenticate first.")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Get emails
        emails_url = f"{self.graph_base_url}/me/mailFolders/{folder}/messages?$top={limit}"
        response = requests.get(emails_url, headers=headers)
        
        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            raise Exception(f"Failed to get emails: {response.text}")

class CRMEmailTemplates:
    """Email templates for CRM communications"""
    
    @staticmethod
    def opportunity_approval_email(opportunity_data: Dict) -> Dict:
        """Generate opportunity approval email"""
        subject = f"Opportunity Approved: {opportunity_data['name']}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #28a745;">✅ Opportunity Approved</h2>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>{opportunity_data['name']}</h3>
                    <p><strong>Account:</strong> {opportunity_data.get('account_name', 'N/A')}</p>
                    <p><strong>Amount:</strong> ${opportunity_data.get('amount', 0):,.2f}</p>
                    <p><strong>Stage:</strong> {opportunity_data.get('stage', 'N/A').title()}</p>
                    <p><strong>Probability:</strong> {opportunity_data.get('probability', 0)}%</p>
                    <p><strong>Expected Close Date:</strong> {opportunity_data.get('close_date', 'N/A')}</p>
                </div>
                
                <p>This opportunity has been approved and is now active in the system.</p>
                
                <div style="margin: 30px 0;">
                    <a href="http://localhost:8501" 
                       style="background-color: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px;">
                        View in CRM Dashboard
                    </a>
                </div>
                
                <hr style="margin: 30px 0;">
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated message from the AI Agent CRM System.
                </p>
            </div>
        </body>
        </html>
        """
        
        return {'subject': subject, 'body': body}
    
    @staticmethod
    def order_confirmation_email(order_data: Dict) -> Dict:
        """Generate order confirmation email"""
        subject = f"Order Confirmation: #{order_data.get('order_id', 'N/A')}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #28a745;">📦 Order Confirmed</h2>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Order #{order_data.get('order_id', 'N/A')}</h3>
                    <p><strong>Customer:</strong> {order_data.get('customer_id', 'N/A')}</p>
                    <p><strong>Product:</strong> {order_data.get('product_id', 'N/A')}</p>
                    <p><strong>Quantity:</strong> {order_data.get('quantity', 0)}</p>
                    <p><strong>Status:</strong> {order_data.get('status', 'N/A')}</p>
                    <p><strong>Order Date:</strong> {order_data.get('order_date', 'N/A')}</p>
                </div>
                
                <p>Your order has been confirmed and is being processed.</p>
                
                <div style="margin: 30px 0;">
                    <a href="http://localhost:8000/delivery/order/{order_data.get('order_id', '')}" 
                       style="background-color: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px;">
                        Track Your Order
                    </a>
                </div>
                
                <hr style="margin: 30px 0;">
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated message from the AI Agent Logistics System.
                </p>
            </div>
        </body>
        </html>
        """
        
        return {'subject': subject, 'body': body}
    
    @staticmethod
    def lead_follow_up_email(lead_data: Dict) -> Dict:
        """Generate lead follow-up email"""
        subject = f"Follow-up: {lead_data.get('company', 'Your Inquiry')}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #007bff;">👋 Following Up on Your Inquiry</h2>
                
                <p>Dear {lead_data.get('full_name', 'Valued Customer')},</p>
                
                <p>Thank you for your interest in our logistics solutions. I wanted to follow up 
                on your recent inquiry and see how we can help {lead_data.get('company', 'your organization')} 
                achieve its logistics goals.</p>
                
                <div style="background-color: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Your Requirements:</h3>
                    <p>{lead_data.get('need', 'Logistics automation solution')}</p>
                    <p><strong>Budget Range:</strong> ${lead_data.get('budget', 0):,.0f}</p>
                    <p><strong>Timeline:</strong> {lead_data.get('timeline', 'To be determined')}</p>
                </div>
                
                <p>Based on your requirements, I believe our AI-powered logistics platform 
                would be an excellent fit for your needs. I'd love to schedule a brief call 
                to discuss how we can help streamline your operations.</p>
                
                <div style="margin: 30px 0;">
                    <a href="mailto:sales@ailogistics.com?subject=Schedule Demo - {lead_data.get('company', '')}" 
                       style="background-color: #28a745; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px;">
                        Schedule a Demo
                    </a>
                </div>
                
                <p>Best regards,<br>
                AI Logistics Sales Team</p>
                
                <hr style="margin: 30px 0;">
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated follow-up from the AI Agent CRM System.
                </p>
            </div>
        </body>
        </html>
        """
        
        return {'subject': subject, 'body': body}

# Example usage and testing
def test_office365_integration():
    """Test Office 365 integration"""
    office365 = Office365Integration()
    
    # Test email templates
    templates = CRMEmailTemplates()
    
    # Test opportunity approval email
    opp_data = {
        'name': 'TechCorp Logistics Upgrade',
        'account_name': 'TechCorp Industries',
        'amount': 300000.0,
        'stage': 'proposal',
        'probability': 75.0,
        'close_date': '2024-02-15'
    }
    
    email_content = templates.opportunity_approval_email(opp_data)
    print("Opportunity Approval Email:")
    print(f"Subject: {email_content['subject']}")
    print("Body generated successfully")
    
    # Test order confirmation email
    order_data = {
        'order_id': 12345,
        'customer_id': 'CUST001',
        'product_id': 'A101',
        'quantity': 10,
        'status': 'Confirmed',
        'order_date': '2024-01-15'
    }
    
    email_content = templates.order_confirmation_email(order_data)
    print(f"\nOrder Confirmation Email:")
    print(f"Subject: {email_content['subject']}")
    print("Body generated successfully")
    
    # Test lead follow-up email
    lead_data = {
        'full_name': 'John Smith',
        'company': 'TechCorp',
        'need': 'Inventory management system',
        'budget': 100000.0,
        'timeline': 'Q2 2024'
    }
    
    email_content = templates.lead_follow_up_email(lead_data)
    print(f"\nLead Follow-up Email:")
    print(f"Subject: {email_content['subject']}")
    print("Body generated successfully")

if __name__ == "__main__":
    test_office365_integration()