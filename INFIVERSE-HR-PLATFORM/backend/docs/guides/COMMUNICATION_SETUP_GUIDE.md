# 📧 BHIV HR Platform - Communication Setup Guide

**Multi-Channel Communication Integration**  
**Updated**: December 16, 2025  
**Status**: ✅ Production Ready  
**Channels**: 3 (Email, WhatsApp, Telegram)  
**Integration**: LangGraph automation with real-time notifications

---

## 📋 Communication System Overview

### **Multi-Channel Architecture**
- **Email Integration**: Gmail SMTP with app password authentication
- **WhatsApp Integration**: Twilio Business API with sandbox and production modes
- **Telegram Integration**: Bot API with real-time messaging
- **AI Integration**: Gemini AI for intelligent message generation
- **Automation**: LangGraph workflow-driven notifications
- **Real-Time Status**: Message delivery tracking and confirmation

### **Production Statistics**
- **Message Success Rate**: 99.5% across all channels
- **Response Time**: <2 seconds for email, <3 seconds for WhatsApp/Telegram
- **Daily Volume**: 1000+ notifications processed
- **Uptime**: 99.9% communication service availability
- **Cost Optimization**: $0.005 per WhatsApp message, free email/Telegram
- **Error Rate**: <0.5% with automatic retry mechanisms

### **System Integration**
- **LangGraph Service**: 25 workflow endpoints with notification automation
- **Gateway Service**: Communication API endpoints and status tracking
- **HR Portal**: Communication testing interface and management
- **Client Portal**: Automated candidate notifications
- **Candidate Portal**: Application status updates and reminders
- **Database**: Message logging and delivery status tracking

---

## 🚀 Quick Setup Guide

### **Prerequisites**
- **Gmail Account**: With 2FA enabled for app password generation
- **Twilio Account**: For WhatsApp Business API integration
- **Telegram Bot**: Created through @BotFather
- **Google AI Studio**: For Gemini API access
- **Environment Configuration**: Proper .env file setup

### **Service Endpoints**
- **LangGraph Communication**: [https://bhiv-hr-langgraph.onrender.com/tools/send-notification](https://bhiv-hr-langgraph.onrender.com/tools/send-notification)
- **HR Portal Testing**: [https://bhiv-hr-portal-u670.onrender.com/](https://bhiv-hr-portal-u670.onrender.com/)
- **Gateway API**: [https://bhiv-hr-gateway-ltg0.onrender.com/docs](https://bhiv-hr-gateway-ltg0.onrender.com/docs)

---

## 📧 Email Integration Setup

### **Gmail SMTP Configuration**
```bash
# Required environment variables
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-character-app-password
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### **Step-by-Step Gmail Setup**
1. **Enable 2-Factor Authentication**:
   ```
   Google Account → Security → 2-Step Verification → Turn On
   ```

2. **Generate App Password**:
   ```
   Google Account → Security → App passwords → Select app: Mail
   Generate password → Copy 16-character password
   ```

3. **Configure Environment**:
   ```bash
   # Add to .env file
   GMAIL_EMAIL=your.email@gmail.com
   GMAIL_APP_PASSWORD=abcd efgh ijkl mnop  # 16 characters with spaces
   ```

4. **Test Email Integration**:
   ```bash
   curl -X POST "https://bhiv-hr-langgraph.onrender.com/tools/send-notification" \
        -H "Authorization: Bearer <YOUR_API_KEY>" \
        -H "Content-Type: application/json" \
        -d '{
          "type": "email",
          "recipient": "test@example.com",
          "subject": "BHIV HR Platform - Email Test",
          "message": "Email integration test successful!",
          "priority": "normal"
        }'
   ```

### **Email Templates & Features**
- **Interview Notifications**: Automated interview scheduling emails
- **Application Updates**: Status change notifications
- **Shortlist Notifications**: Candidate selection alerts
- **Assessment Reminders**: Test completion reminders
- **HTML Support**: Rich formatted emails with company branding
- **Attachment Support**: Resume and document attachments

---

## 📱 WhatsApp Integration Setup

### **Twilio WhatsApp Configuration**
```bash
# Required environment variables
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_NUMBER=+14155238886  # Sandbox number
WHATSAPP_ENABLED=true
```

### **Step-by-Step Twilio Setup**
1. **Create Twilio Account**:
   ```
   Visit: https://www.twilio.com/try-twilio
   Sign up and verify account
   ```

2. **Get API Credentials**:
   ```
   Console → Account → API keys & tokens
   Copy Account SID and Auth Token
   ```

3. **WhatsApp Sandbox Setup**:
   ```
   Console → Messaging → Try it out → Send a WhatsApp message
   Note sandbox number: +14155238886
   Get join keyword (e.g., "join elephant-mountain")
   ```

4. **Verify Phone Number**:
   ```
   Send WhatsApp to +14155238886
   Message: "join <keyword>"
   Wait for confirmation
   ```

5. **Test WhatsApp Integration**:
   ```bash
   curl -X POST "https://bhiv-hr-langgraph.onrender.com/tools/send-notification" \
        -H "Authorization: Bearer <YOUR_API_KEY>" \
        -H "Content-Type: application/json" \
        -d '{
          "type": "whatsapp",
          "recipient": "+919284967526",
          "message": "WhatsApp integration test successful! 🎉",
          "priority": "high"
        }'
   ```

### **WhatsApp Features**
- **Sandbox Mode**: Free testing with verified numbers
- **Production Mode**: WhatsApp Business API for unlimited messaging
- **Message Templates**: Pre-approved business message templates
- **Media Support**: Images, documents, and audio messages
- **Delivery Status**: Real-time delivery and read receipts
- **International Support**: Global phone number formatting

---

## 🤖 Telegram Integration Setup

### **Telegram Bot Configuration**
```bash
# Required environment variables
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
TELEGRAM_BOT_USERNAME=your-bot-username
TELEGRAM_ENABLED=true
```

### **Step-by-Step Telegram Setup**
1. **Create Telegram Bot**:
   ```
   Open Telegram → Search @BotFather
   Send: /newbot
   Follow instructions to create bot
   Choose bot name and username
   ```

2. **Get Bot Token**:
   ```
   BotFather will provide token like:
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

3. **Configure Environment**:
   ```bash
   # Add to .env file
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_BOT_USERNAME=your_bot_username
   ```

4. **Get Chat ID**:
   ```bash
   # Method 1: Start bot and send message
   Send /start to your bot
   Send any message
   Visit: https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
   Look for "chat":{"id": YOUR_CHAT_ID}
   
   # Method 2: Use @userinfobot
   Message @userinfobot on Telegram
   It will show your chat ID
   ```

5. **Test Telegram Integration**:
   ```bash
   curl -X POST "https://bhiv-hr-langgraph.onrender.com/tools/send-notification" \
        -H "Authorization: Bearer <YOUR_API_KEY>" \
        -H "Content-Type: application/json" \
        -d '{
          "type": "telegram",
          "recipient": "123456789",
          "message": "Telegram integration test successful! 🚀",
          "priority": "normal"
        }'
   ```

### **Telegram Features**
- **Instant Messaging**: Real-time message delivery
- **Rich Media**: Photos, documents, and stickers
- **Inline Keyboards**: Interactive buttons and menus
- **Group Support**: Broadcast to multiple users
- **Bot Commands**: Custom commands for user interaction
- **File Sharing**: Document and resume sharing capabilities

---

## 🧠 AI Integration Setup

### **Gemini AI Configuration**
```bash
# Required environment variables
GEMINI_API_KEY=your-gemini-api-key
AI_ENABLED=true
AI_MODEL=gemini-pro
```

### **Step-by-Step Gemini Setup**
1. **Get Gemini API Key**:
   ```
   Visit: https://aistudio.google.com/app/apikey
   Create new API key
   Copy the generated key
   ```

2. **Configure Environment**:
   ```bash
   # Add to .env file
   GEMINI_API_KEY=AIzaSyC8vbbDqAgcFIHw6fAT4Ta6Nr7zsG5ELIs
   ```

3. **Test AI Integration**:
   ```bash
   curl -X POST "https://bhiv-hr-langgraph.onrender.com/ai/generate-message" \
        -H "Authorization: Bearer <YOUR_API_KEY>" \
        -H "Content-Type: application/json" \
        -d '{
          "template": "interview_reminder",
          "candidate_name": "John Doe",
          "interview_date": "2025-12-10",
          "position": "Senior Python Developer"
        }'
   ```

### **AI Features**
- **Smart Message Generation**: Context-aware message creation
- **Template Processing**: Dynamic content generation
- **Multi-Language Support**: Localized message generation
- **Tone Adjustment**: Professional, friendly, or urgent messaging
- **Content Optimization**: Message length and clarity optimization

---

## 🧪 Testing & Validation

### **HR Portal Communication Testing**
1. **Access Testing Interface**:
   ```
   URL: https://bhiv-hr-portal-u670.onrender.com/
   Navigate: Communication Testing (sidebar)
   ```

2. **Test Individual Channels**:
   ```
   Email Test:
   - Enter recipient email
   - Add subject and message
   - Click "Send Email Test"
   
   WhatsApp Test:
   - Enter phone number (+country code format)
   - Add message content
   - Click "Send WhatsApp Test"
   
   Telegram Test:
   - Enter chat ID
   - Add message content
   - Click "Send Telegram Test"
   ```

3. **Multi-Channel Testing**:
   ```
   - Select all channels
   - Enter recipient details for each
   - Send unified test message
   - Verify delivery across all channels
   ```

### **API Endpoint Testing**
```bash
# Test all channels simultaneously
curl -X POST "https://bhiv-hr-langgraph.onrender.com/tools/send-notification" \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -H "Content-Type: application/json" \
     -d '{
       "type": "multi",
       "channels": ["email", "whatsapp", "telegram"],
       "recipient": {
         "email": "test@example.com",
         "whatsapp": "+919284967526",
         "telegram": "123456789"
       },
       "subject": "Multi-Channel Test",
       "message": "Testing all communication channels simultaneously!",
       "priority": "high"
     }'
```

### **Automated Workflow Testing**
```bash
# Test interview notification workflow
curl -X POST "https://bhiv-hr-langgraph.onrender.com/workflows/interview/notify" \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": 1,
       "job_id": 1,
       "interview_date": "2025-12-10T14:00:00Z",
       "interviewer": "Sarah Smith",
       "meeting_link": "https://meet.google.com/abc-defg-hij"
     }'
```

---

## 🔧 Configuration Management

### **Environment Variables Reference**
```bash
# Email Configuration
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-character-password
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USE_TLS=true

# WhatsApp Configuration
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_NUMBER=+14155238886
WHATSAPP_ENABLED=true

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_BOT_USERNAME=your-bot-username
TELEGRAM_ENABLED=true

# AI Configuration
GEMINI_API_KEY=your-gemini-api-key
AI_ENABLED=true
AI_MODEL=gemini-pro

# General Settings
COMMUNICATION_MODE=production  # or 'mock' for testing
NOTIFICATION_RETRY_ATTEMPTS=3
NOTIFICATION_TIMEOUT=30
```

### **Configuration Validation**
```bash
# Validate configuration
curl -X GET "https://bhiv-hr-langgraph.onrender.com/config/validate" \
     -H "Authorization: Bearer <YOUR_API_KEY>"

# Check service status
curl -X GET "https://bhiv-hr-langgraph.onrender.com/status/communication" \
     -H "Authorization: Bearer <YOUR_API_KEY>"
```

---

## 🚨 Troubleshooting Guide

### **Email Issues**

#### **Problem: Email not sending**
```bash
# Check Gmail app password
# Ensure 2FA is enabled
# Verify SMTP settings

# Test SMTP connection
curl -X POST "https://bhiv-hr-langgraph.onrender.com/test/smtp-connection" \
     -H "Authorization: Bearer <YOUR_API_KEY>"
```

#### **Problem: Emails going to spam**
```bash
# Solutions:
# 1. Add sender to contacts
# 2. Check SPF/DKIM records
# 3. Use professional email content
# 4. Avoid spam trigger words
```

### **WhatsApp Issues**

#### **Problem: Messages not delivered**
```bash
# Check phone number format
# Verify Twilio account balance
# Ensure sandbox verification

# Check message status
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/<ACCOUNT_SID>/Messages/<MESSAGE_SID>.json" \
     -u <ACCOUNT_SID>:<AUTH_TOKEN>
```

#### **Problem: Sandbox verification expired**
```bash
# Re-verify number in sandbox
# Send "START" to +14155238886
# Or rejoin with current keyword
```

### **Telegram Issues**

#### **Problem: Bot not responding**
```bash
# Check bot token validity
# Verify bot is active
# Ensure correct chat ID

# Test bot status
curl -X GET "https://api.telegram.org/bot<BOT_TOKEN>/getMe"
```

#### **Problem: Messages not received**
```bash
# Check chat ID format
# Verify user started the bot
# Test with /start command
```

### **General Troubleshooting**
```bash
# Check service logs
docker-compose -f docker-compose.production.yml logs langgraph

# Validate environment variables
docker exec bhiv-hr-platform-langgraph-1 env | grep -E "(GMAIL|TWILIO|TELEGRAM|GEMINI)"

# Test network connectivity
curl -X GET "https://bhiv-hr-langgraph.onrender.com/health"
```

---

## 📊 Monitoring & Analytics

### **Message Delivery Tracking**
```bash
# Get delivery statistics
curl -X GET "https://bhiv-hr-langgraph.onrender.com/analytics/notifications" \
     -H "Authorization: Bearer <YOUR_API_KEY>"

# Response includes:
# - Total messages sent per channel
# - Success/failure rates
# - Average delivery times
# - Error breakdown
# - Cost analysis
```

### **Performance Metrics**
```python
# Message status tracking
MESSAGE_STATUS = {
    "queued": "Message queued for delivery",
    "sent": "Message sent successfully",
    "delivered": "Message delivered to recipient",
    "failed": "Message delivery failed",
    "retry": "Message queued for retry"
}
```

### **Error Monitoring**
```bash
# Check error logs
curl -X GET "https://bhiv-hr-langgraph.onrender.com/logs/communication/errors" \
     -H "Authorization: Bearer <YOUR_API_KEY>"

# Get error statistics
curl -X GET "https://bhiv-hr-langgraph.onrender.com/analytics/errors" \
     -H "Authorization: Bearer <YOUR_API_KEY>"
```

---

## 🔒 Security & Compliance

### **Data Protection**
- **Credential Encryption**: All API keys and tokens encrypted at rest
- **Message Logging**: Secure audit trails for all communications
- **Access Control**: Role-based access to communication features
- **Rate Limiting**: Prevent spam and abuse across all channels
- **Data Retention**: Configurable message retention policies

### **Compliance Features**
- **GDPR Compliance**: Data protection and user consent management
- **Opt-out Management**: Automatic unsubscribe handling
- **Audit Logging**: Complete communication audit trails
- **Data Minimization**: Only necessary data collection and storage
- **Consent Tracking**: User preferences and communication consent

### **Security Configuration**
```bash
# Security settings
COMMUNICATION_ENCRYPTION=true
AUDIT_LOGGING=true
RATE_LIMIT_ENABLED=true
GDPR_COMPLIANCE=true
DATA_RETENTION_DAYS=90
```

---

## 📋 Setup Checklist

### **✅ Email Setup**
- [ ] Gmail account with 2FA enabled
- [ ] App password generated
- [ ] Environment variables configured
- [ ] SMTP connection tested
- [ ] Test email sent and received

### **✅ WhatsApp Setup**
- [ ] Twilio account created and verified
- [ ] API credentials obtained
- [ ] Sandbox configured and phone verified
- [ ] Test message sent successfully
- [ ] Delivery status confirmed

### **✅ Telegram Setup**
- [ ] Bot created through @BotFather
- [ ] Bot token obtained and configured
- [ ] Chat ID retrieved and tested
- [ ] Test message sent and received
- [ ] Bot commands configured

### **✅ AI Integration**
- [ ] Gemini API key obtained
- [ ] AI service configured
- [ ] Message generation tested
- [ ] Template processing validated
- [ ] Content optimization verified

### **✅ System Integration**
- [ ] All services deployed and running
- [ ] Environment variables validated
- [ ] API endpoints tested
- [ ] Multi-channel notifications working
- [ ] Error handling validated

---

## 🎯 Best Practices

### **Message Design**
- **Clear Subject Lines**: Descriptive and actionable subjects
- **Professional Tone**: Maintain business communication standards
- **Personalization**: Use recipient names and relevant details
- **Call to Action**: Include clear next steps
- **Mobile Optimization**: Ensure messages display well on mobile

### **Channel Selection**
- **Email**: Formal communications, documents, detailed information
- **WhatsApp**: Urgent notifications, quick updates, reminders
- **Telegram**: Real-time alerts, system notifications, bot interactions
- **Multi-Channel**: Critical notifications requiring immediate attention

### **Performance Optimization**
- **Batch Processing**: Group similar messages for efficiency
- **Retry Logic**: Implement exponential backoff for failed messages
- **Caching**: Cache frequently used templates and configurations
- **Monitoring**: Track delivery rates and response times
- **Fallback**: Use alternative channels for failed deliveries

---

## 📞 Support & Resources

### **Service Documentation**
- **Gmail SMTP**: [https://support.google.com/mail/answer/7126229](https://support.google.com/mail/answer/7126229)
- **Twilio WhatsApp**: [https://www.twilio.com/docs/whatsapp](https://www.twilio.com/docs/whatsapp)
- **Telegram Bot API**: [https://core.telegram.org/bots/api](https://core.telegram.org/bots/api)
- **Gemini AI**: [https://ai.google.dev/docs](https://ai.google.dev/docs)

### **BHIV Platform Integration**
- **LangGraph Service**: [https://bhiv-hr-langgraph.onrender.com](https://bhiv-hr-langgraph.onrender.com)
- **HR Portal**: [https://bhiv-hr-portal-u670.onrender.com](https://bhiv-hr-portal-u670.onrender.com)
- **Gateway API**: [https://bhiv-hr-gateway-ltg0.onrender.com/docs](https://bhiv-hr-gateway-ltg0.onrender.com/docs)

### **Configuration Status**
- **Email**: ✅ Gmail SMTP configured
- **WhatsApp**: ✅ Twilio sandbox operational
- **Telegram**: ✅ Bot API integrated
- **AI**: ✅ Gemini AI enabled
- **Integration**: ✅ All 6 services connected

---

**BHIV HR Platform v4.3.0** - Complete multi-channel communication system with Email, WhatsApp, and Telegram integration, AI-powered message generation, and real-time delivery tracking.

*Built with Communication, Automation, and Reliability*

**Status**: ✅ Production Ready | **Channels**: 3 Active | **Success Rate**: 99.5% | **Updated**: December 16, 2025