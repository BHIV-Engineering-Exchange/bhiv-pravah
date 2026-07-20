#!/usr/bin/env python3
"""
Quick Email Configuration Test
Test your email settings before sending to suppliers
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def test_email_config():
    """Test email configuration with a simple test email"""
    
    print("🧪 Testing Email Configuration...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get email settings
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    company_name = os.getenv("COMPANY_NAME", "Your Company")
    
    print(f"📧 Email User: {email_user}")
    print(f"🏢 Company: {company_name}")
    print(f"🌐 SMTP Server: {smtp_server}:{smtp_port}")
    
    if not email_user or email_user == "your-gmail@gmail.com":
        print("\n❌ EMAIL_USER not configured!")
        print("📝 Please update .env file with your real Gmail address")
        return False
    
    if not email_password or email_password == "your-16-character-app-password":
        print("\n❌ EMAIL_PASSWORD not configured!")
        print("🔑 Please update .env file with your Gmail App Password")
        print("\n📱 How to get Gmail App Password:")
        print("1. Go to Google Account Settings")
        print("2. Security → 2-Step Verification (enable if not done)")
        print("3. App Passwords → Select 'Mail' → Generate")
        print("4. Copy the 16-character password to .env file")
        return False
    
    # Test email sending
    try:
        print(f"\n📤 Attempting to send test email to {email_user}...")
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = email_user  # Send to yourself for testing
        msg['Subject'] = "🧪 AI Logistics System - Email Test"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>✅ Email Configuration Test Successful!</h2>
            <p>This is a test email from your AI Logistics System.</p>
            
            <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>📊 Configuration Details:</h3>
                <ul>
                    <li><strong>Email User:</strong> {email_user}</li>
                    <li><strong>Company:</strong> {company_name}</li>
                    <li><strong>SMTP Server:</strong> {smtp_server}:{smtp_port}</li>
                    <li><strong>Test Time:</strong> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
            </div>
            
            <p>🎉 <strong>Your supplier notification system is now ready to send real emails!</strong></p>
            
            <p>Next steps:</p>
            <ol>
                <li>Use the dashboard to send restock alerts to suppliers</li>
                <li>Suppliers will receive professional emails automatically</li>
                <li>All email activity will be logged in the system</li>
            </ol>
            
            <p>Best regards,<br>
            <strong>AI Logistics System</strong></p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect and send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_password)
        
        text = msg.as_string()
        server.sendmail(email_user, email_user, text)
        server.quit()
        
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print(f"📬 Check your inbox at {email_user}")
        print("\n🎉 Email configuration is working!")
        print("🚀 Your supplier notification system is ready!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ EMAIL TEST FAILED: {e}")
        print("\n🔧 Common Solutions:")
        
        if "Username and Password not accepted" in str(e):
            print("1. ✅ Make sure you're using Gmail App Password (not regular password)")
            print("2. ✅ Verify 2-Factor Authentication is enabled")
            print("3. ✅ Generate new App Password if needed")
        
        elif "Connection refused" in str(e):
            print("1. ✅ Check your internet connection")
            print("2. ✅ Verify SMTP server and port (Gmail: smtp.gmail.com:587)")
            print("3. ✅ Check firewall settings")
        
        else:
            print("1. ✅ Double-check email address and password")
            print("2. ✅ Ensure Gmail account has 2FA enabled")
            print("3. ✅ Try generating a new App Password")
        
        return False

if __name__ == "__main__":
    test_email_config()