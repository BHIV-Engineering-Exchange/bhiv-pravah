# Quick Start Guide

## For Employees

### Installation

1. Download the installer for your platform:
   - **Windows**: `Employee Activity Agent Setup.exe`
   - **macOS**: `Employee Activity Agent.dmg`

2. **Windows**: Run the installer and follow the prompts
   **macOS**: Open the DMG and drag the app to Applications folder

3. Launch the application from:
   - **Windows**: Start Menu → Employee Activity Agent
   - **macOS**: Applications → Employee Activity Agent

### First Time Setup

1. **Grant Permissions** (macOS only):
   - System Preferences → Security & Privacy → Privacy
   - Enable **Accessibility** for Employee Activity Agent
   - Enable **Input Monitoring** for Employee Activity Agent

2. **Read & Accept Consent**:
   - Read the privacy notice carefully
   - Check the consent checkbox
   - Click "Accept & Continue"

3. **Login**:
   - Enter your company email
   - Enter your password
   - Click "Login"

### Daily Workflow

#### Starting Your Day
1. Open the app (or click the tray icon)
2. Click **"Start Day"**
3. Minimize to tray - tracking runs in background

#### During Work
- The tray icon shows tracking status
- Click tray icon to view live activity stats
- App sends data to server every 30 seconds

#### Ending Your Day
1. Open the app dashboard
2. Click **"End Day"**
3. Tracking stops immediately

### Tray Icon Guide

- **Green dot** 🟢 = Day started, tracking active
- **Gray dot** ⚪ = Day not started
- Click to open dashboard
- Right-click for quick menu

### Privacy Reminders

✅ You can see what's being tracked in real-time  
✅ You can stop tracking anytime by ending your day  
✅ No tracking when app is closed  
✅ No screenshots or keystroke content  

## For IT Administrators

### Deployment

#### 1. Backend Configuration

Ensure these API endpoints are live:
```
POST /api/agent/login
POST /api/attendance/start
POST /api/attendance/end
POST /api/activity/ingest
```

#### 2. Build Configuration

Set backend URL in `.env`:
```env
AGENT_API_BASE_URL=https://your-company-backend.com
```

Build for distribution:
```bash
npm run build:win   # Windows
npm run build:mac   # macOS
```

#### 3. Distribution

**Option A: Manual Distribution**
- Share installer files via network drive
- Email download links to employees

**Option B: MDM/GPO Deployment**
- Use SCCM, Intune, or Jamf
- Silent install parameters available

#### 4. Employee Onboarding

Provide employees with:
- Installer file
- Login credentials
- Quick start instructions
- Privacy policy document

### Group Policy (Windows)

Pre-configure for domain-joined machines:

```reg
[HKEY_LOCAL_MACHINE\SOFTWARE\Policies\EmployeeActivityAgent]
"BackendURL"="https://your-backend.com"
"AutoStartWithWindows"=dword:00000001
```

### macOS Deployment Profile

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>
        <dict>
            <key>PayloadType</key>
            <string>com.apple.TCC.configuration-profile-policy</string>
            <key>Services</key>
            <dict>
                <key>Accessibility</key>
                <array>
                    <dict>
                        <key>Allowed</key>
                        <true/>
                        <key>CodeRequirement</key>
                        <string>identifier "com.employeeagent.app"</string>
                    </dict>
                </array>
            </dict>
        </dict>
    </array>
</dict>
</plist>
```

### Monitoring Deployment

Check backend logs for:
- Successful logins
- Active tracking sessions
- Data ingestion frequency
- Error rates

### Common Issues

| Issue | Solution |
|-------|----------|
| "Cannot track activity" | Grant Accessibility permissions |
| "Connection failed" | Check firewall, verify backend URL |
| "Login failed" | Verify user credentials in backend |
| "iohook error" | Reinstall with admin rights |

### Security Considerations

- All data transmitted over HTTPS
- JWT tokens for authentication
- No data stored locally (except consent)
- Tokens expire based on backend policy
- Agent respects backend's day start/end state

## For Developers

### Local Development

```bash
# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Edit .env with local backend
# AGENT_API_BASE_URL=http://localhost:5000

# Run in dev mode
npm run dev
```

### Testing

1. **Test consent flow**: Delete electron-store data
2. **Test tracking**: Monitor console for event counts
3. **Test API calls**: Check network tab in DevTools
4. **Test error handling**: Disconnect backend

### Debugging

Enable developer tools:
```javascript
// In main.js, add:
mainWindow.webContents.openDevTools();
```

View logs:
- **Windows**: `%APPDATA%\employee-activity-agent\logs`
- **macOS**: `~/Library/Logs/employee-activity-agent`

### Building Custom Versions

Modify `package.json` build section:
```json
{
  "build": {
    "appId": "com.yourcompany.agent",
    "productName": "Your Company Agent"
  }
}
```

## Support

**For Employees**: Contact your IT department  
**For Admins**: Check backend API logs and agent console  
**For Developers**: See README.md and inline code comments
