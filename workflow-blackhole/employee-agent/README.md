# Employee Activity Agent

A **privacy-conscious** Electron desktop application for tracking employee activity during work hours. This agent integrates with your existing backend system to provide transparent, ethical activity monitoring.

## 🎯 Purpose

This desktop agent runs on employee workstations to track work activity metrics in a **transparent and ethical** manner. All tracking is:
- **Opt-in**: Requires explicit consent
- **Transparent**: Clear UI showing tracking status
- **Limited**: Only active during work hours (Start Day to End Day)
- **Privacy-focused**: No screenshots, no keystroke content, no stealth mode

> **Note:** This implementation uses **Electron's built-in APIs** for activity tracking. Activity counts are estimated based on system idle state rather than actual event tracking. See [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for details and production recommendations.

## 🔒 What We Track

The agent collects only aggregated, non-invasive metrics:

✅ **What IS tracked:**
- Mouse event counts (NOT positions or movements)
- Keyboard event counts (NOT actual keystrokes)
- Active application names
- Idle/active time duration

❌ **What is NOT tracked:**
- Screenshots or screen content
- Actual keystroke content or typed text
- Mouse positions or coordinates
- Personal files or data
- Activity outside of work hours
- Anything when the app is closed or day is ended

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Electron Desktop Agent          │
│                                         │
│  ┌─────────┐  ┌──────────┐  ┌────────┐ │
│  │  Tray   │  │ Renderer │  │  Main  │ │
│  │   UI    │←→│    UI    │←→│Process │ │
│  └─────────┘  └──────────┘  └────┬───┘ │
│                                   │     │
│  ┌────────────────────────────────┼───┐ │
│  │    Activity Tracker Manager    │   │ │
│  │  ┌──────┐ ┌────────┐ ┌───────┐│   │ │
│  │  │iohook│ │active- │ │ idle  ││   │ │
│  │  │      │ │  win   │ │ time  ││   │ │
│  │  └──────┘ └────────┘ └───────┘│   │ │
│  └────────────────────────────────┘   │ │
│                 │                      │ │
└─────────────────┼──────────────────────┘ │
                  ▼                        │
          ┌──────────────┐                 │
          │ API Service  │                 │
          └──────┬───────┘                 │
                 │                         │
                 ▼                         │
    ┌────────────────────────┐             │
    │  Backend API (Render)  │             │
    │                        │             │
    │  /api/agent/login      │             │
    │  /api/attendance/start │             │
    │  /api/attendance/end   │             │
    │  /api/activity/ingest  │             │
    └────────────────────────┘
```

## 📋 Prerequisites

### System Requirements

- **Windows 10/11** or **macOS 10.13+**
- **Node.js 16+** and **npm**
- Active internet connection for backend communication

### Permissions Required

#### Windows:
- Accessibility permissions (for iohook)
- Network access

#### macOS:
- **Accessibility permissions** (System Preferences → Security & Privacy → Privacy → Accessibility)
- **Input Monitoring** (for iohook to work)
- Network access

## 🚀 Setup Instructions

### 1. Clone and Navigate

```bash
cd employee-agent
```

### 2. Install Dependencies

```bash
npm install
```

**Note**: The `iohook` package requires native compilation. On Windows, you may need:
- Windows Build Tools: `npm install --global windows-build-tools`
- Visual Studio Build Tools

On macOS, you need Xcode Command Line Tools:
```bash
xcode-select --install
```

### 3. Configure Backend URL

Create a `.env` file in the `employee-agent` folder:

```bash
cp .env.example .env
```

Edit `.env` and set your backend URL:

```env
AGENT_API_BASE_URL=https://your-render-backend.onrender.com
```

### 4. Run the Application

**Development mode:**
```bash
npm start
```

or

```bash
npm run dev
```

## 📦 Building Executables

### Build for Windows

```bash
npm run build:win
```

Output: `dist/Employee Activity Agent Setup.exe`

### Build for macOS

```bash
npm run build:mac
```

Output: `dist/Employee Activity Agent.dmg`

### Build for Both

```bash
npm run build
```

## 🎮 Usage

### First Run - Consent

1. **Launch the application**
2. Read the **Privacy & Consent** screen carefully
3. Check the consent checkbox
4. Click **Accept & Continue**

Your consent is stored locally and required only once.

### Daily Usage

1. **Login** with your employee credentials
2. **Start Day** when you begin work
3. The tray icon shows tracking status
4. Monitor your activity stats in the dashboard
5. **End Day** when you finish work
6. **Logout** when done

### Tray Icon

The application runs in the system tray:
- **Click** the tray icon to show/hide the dashboard
- **Right-click** for quick menu:
  - View login status
  - View tracking status
  - Open dashboard
  - Quit application

### Tracking Behavior

- Tracking **starts** only after clicking "Start Day"
- Tracking **stops** immediately when:
  - You click "End Day"
  - You logout
  - You quit the application
- Data is sent to the backend **every 30 seconds**
- If the backend rejects activity (e.g., day not started on server), tracking stops automatically

## 🔧 Troubleshooting

### iohook Installation Issues

**Windows:**
```bash
npm install --global windows-build-tools
npm rebuild iohook
```

**macOS:**
- Grant Accessibility permissions in System Preferences
- Grant Input Monitoring permissions
```bash
npm rebuild iohook
```

**Linux:**
```bash
sudo apt-get install libx11-dev libxtst-dev libxkbfile-dev
npm rebuild iohook
```

### Connection Issues

- Verify `.env` file has correct `AGENT_API_BASE_URL`
- Check internet connection
- Ensure backend is running and accessible
- Check firewall/antivirus settings

### Tracking Not Working

- Check that you clicked "Start Day"
- Verify backend returned a valid attendance ID
- Check console logs for errors
- On macOS, verify Accessibility permissions are granted

## 🔐 Security & Privacy

### Data Storage

- **Consent**: Stored locally using `electron-store`
- **Auth Token**: Stored locally, encrypted by Electron
- **Activity Data**: Never stored locally, sent directly to backend

### Network Communication

- All API calls use HTTPS (if backend uses HTTPS)
- JWT authentication tokens
- 30-second data transmission interval

### Privacy Guarantees

1. **No stealth mode**: Tray icon always visible
2. **No screenshots**: Application never captures screen
3. **No keystroke logging**: Only event counts
4. **User control**: Can stop tracking anytime
5. **Transparent**: Clear UI showing what's tracked

## 🛠️ Development

### Project Structure

```
employee-agent/
├── assets/               # Application icons
├── src/
│   ├── main.js          # Electron main process
│   ├── preload.js       # Preload script (security bridge)
│   ├── managers/
│   │   └── activityTracker.js   # Activity tracking logic
│   ├── services/
│   │   └── apiService.js        # Backend API integration
│   └── renderer/
│       ├── index.html   # UI markup
│       └── app.js       # UI logic
├── .env                 # Configuration (not in git)
├── .env.example         # Configuration template
├── package.json         # Dependencies and build config
└── README.md           # This file
```

### Tech Stack

### Tech Stack

- **Electron 28+**: Desktop app framework
- **Electron powerMonitor**: System idle detection (built-in)
- **axios**: HTTP client
- **electron-store**: Persistent local storage

**Note:** Native dependencies like `iohook` and `active-win` are not included in this version to avoid compilation issues. Activity tracking uses Electron's built-in APIs instead. See [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for details.

### API Integration

The agent expects these backend endpoints:

#### POST /api/agent/login
```json
// Request
{
  "email": "user@company.com",
  "password": "<your_password>"
}

// Response
{
  "success": true,
  "token": "jwt-token-here",
  "user": { "email": "user@company.com", "id": "..." }
}
```

#### POST /api/attendance/start
```json
// Response
{
  "success": true,
  "attendanceId": "attendance-record-id"
}
```

#### POST /api/attendance/end
```json
// Response
{
  "success": true
}
```

#### POST /api/activity/ingest
```json
// Request
{
  "attendanceId": "attendance-record-id",
  "timestamp": "2026-01-31T10:30:00.000Z",
  "mouseEvents": 150,
  "keyboardEvents": 45,
  "idleSeconds": 20,
  "activeApp": "Visual Studio Code",
  "intervalDuration": 30
}

// Response
{
  "success": true
}
```

## 📝 License

MIT

## ⚠️ Important Notes

1. **Not for deployment on Vercel/Render**: This is a desktop application, not a web service
2. **Employee consent required**: Cannot be run without user consent
3. **Requires backend**: Must have backend API running and configured
4. **Platform-specific builds**: Build on the target platform or use a CI service
5. **Accessibility permissions**: Required on macOS and some Linux distributions

## 🆘 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review console logs (View → Toggle Developer Tools)
3. Verify backend API is accessible
4. Check that all dependencies installed successfully

## 🔄 Updates

To update the agent:
```bash
git pull
npm install
npm run build
```

## 📊 Testing

Before deploying to employees:

1. Test login with valid credentials
2. Test Start Day → verify tracking starts
3. Monitor activity stats in UI
4. Check backend receives data every 30s
5. Test End Day → verify tracking stops
6. Test consent flow on fresh install
7. Test tray menu functionality
8. Test quit and reopen behavior
