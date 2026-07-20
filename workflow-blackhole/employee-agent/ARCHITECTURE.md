# System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Employee Workstation                        │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │           Electron Desktop Agent                          │ │
│  │                                                           │ │
│  │  ┌─────────────┐    ┌──────────────┐   ┌──────────────┐ │ │
│  │  │   System    │    │   Renderer   │   │     Main     │ │ │
│  │  │  Tray Icon  │◄──►│   Process    │◄─►│   Process    │ │ │
│  │  │             │    │   (Browser)  │   │   (Node.js)  │ │ │
│  │  └─────────────┘    └──────────────┘   └──────┬───────┘ │ │
│  │                                                 │         │ │
│  │                     ┌───────────────────────────┘         │ │
│  │                     │                                     │ │
│  │  ┌──────────────────▼────────────────────────────────┐   │ │
│  │  │         Activity Tracking Manager                 │   │ │
│  │  │                                                    │   │ │
│  │  │  ┌──────────┐ ┌────────────┐ ┌─────────────────┐ │   │ │
│  │  │  │  iohook  │ │ active-win │ │ node-idle-time  │ │   │ │
│  │  │  │  (Mouse/ │ │  (Active   │ │  (Idle Time     │ │   │ │
│  │  │  │   Key)   │ │   Window)  │ │   Detection)    │ │   │ │
│  │  │  └──────────┘ └────────────┘ └─────────────────┘ │   │ │
│  │  │                                                    │   │ │
│  │  └────────────────────┬───────────────────────────────┘   │ │
│  │                       │ Every 30 seconds                  │ │
│  │                       │                                   │ │
│  │  ┌────────────────────▼───────────────────────────────┐   │ │
│  │  │              API Service Layer                     │   │ │
│  │  │              (axios HTTP client)                   │   │ │
│  │  └────────────────────┬───────────────────────────────┘   │ │
│  │                       │                                   │ │
│  └───────────────────────┼───────────────────────────────────┘ │
│                          │ HTTPS/JSON                          │
└──────────────────────────┼─────────────────────────────────────┘
                           │
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Backend API (Render/Cloud)                     │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Express Routes                         │ │
│  │                                                           │ │
│  │  POST /api/agent/login ──────► JWT Authentication        │ │
│  │  POST /api/attendance/start ─► Create Attendance Record  │ │
│  │  POST /api/attendance/end ───► End Attendance Record     │ │
│  │  POST /api/activity/ingest ──► Store Activity Data       │ │
│  │                                                           │ │
│  └───────────────────────┬───────────────────────────────────┘ │
│                          │                                     │
│                          ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                  MongoDB Database                         │ │
│  │                                                           │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │ │
│  │  │    Users    │  │  Attendance  │  │    Activity    │  │ │
│  │  │             │  │   Records    │  │     Data       │  │ │
│  │  │ - email     │  │              │  │                │  │ │
│  │  │ - password  │  │ - userId     │  │ - attendanceId │  │ │
│  │  │ - role      │  │ - startTime  │  │ - mouseEvents  │  │ │
│  │  │             │  │ - endTime    │  │ - keyEvents    │  │ │
│  │  │             │  │ - status     │  │ - idleSeconds  │  │ │
│  │  │             │  │              │  │ - activeApp    │  │ │
│  │  └─────────────┘  └──────────────┘  └────────────────┘  │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Frontend Dashboard (Vercel)                        │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Next.js Application                    │ │
│  │                                                           │ │
│  │  • View employee activity reports                        │ │
│  │  • Monitor active tracking sessions                      │ │
│  │  • Generate productivity analytics                       │ │
│  │  • Manage employee accounts                              │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Employee Login Flow

```
┌────────────┐      ┌──────────┐      ┌─────────────┐      ┌──────────┐
│  Employee  │      │  Electron│      │   Backend   │      │ MongoDB  │
│            │      │   Agent  │      │     API     │      │          │
└─────┬──────┘      └────┬─────┘      └──────┬──────┘      └────┬─────┘
      │                  │                   │                   │
      │  Enter email/pwd │                   │                   │
      ├─────────────────►│                   │                   │
      │                  │                   │                   │
      │                  │ POST /api/agent/login                 │
      │                  │  (email, password)│                   │
      │                  ├──────────────────►│                   │
      │                  │                   │                   │
      │                  │                   │  Find user        │
      │                  │                   ├──────────────────►│
      │                  │                   │                   │
      │                  │                   │  User data        │
      │                  │                   ◄──────────────────┤
      │                  │                   │                   │
      │                  │  JWT token + user │                   │
      │                  ◄──────────────────┤                   │
      │                  │                   │                   │
      │  Show dashboard  │                   │                   │
      ◄─────────────────┤                   │                   │
      │                  │                   │                   │
```

### 2. Start Day Flow

```
┌────────────┐      ┌──────────┐      ┌─────────────┐      ┌──────────┐
│  Employee  │      │  Electron│      │   Backend   │      │ MongoDB  │
│            │      │   Agent  │      │     API     │      │          │
└─────┬──────┘      └────┬─────┘      └──────┬──────┘      └────┬─────┘
      │                  │                   │                   │
      │  Click "Start"   │                   │                   │
      ├─────────────────►│                   │                   │
      │                  │                   │                   │
      │                  │ POST /api/attendance/start            │
      │                  │  (Bearer token)   │                   │
      │                  ├──────────────────►│                   │
      │                  │                   │                   │
      │                  │                   │  Create record    │
      │                  │                   ├──────────────────►│
      │                  │                   │                   │
      │                  │                   │  Attendance ID    │
      │                  │                   ◄──────────────────┤
      │                  │                   │                   │
      │                  │  Attendance ID    │                   │
      │                  ◄──────────────────┤                   │
      │                  │                   │                   │
      │                  │  ┌──────────────────────────────┐    │
      │                  │  │ Start Activity Tracking:     │    │
      │                  │  │ - Enable iohook              │    │
      │                  │  │ - Monitor active window      │    │
      │                  │  │ - Monitor idle time          │    │
      │                  │  │ - Start 30s transmission     │    │
      │                  │  └──────────────────────────────┘    │
      │                  │                   │                   │
      │  Tracking Active │                   │                   │
      ◄─────────────────┤                   │                   │
      │                  │                   │                   │
```

### 3. Activity Tracking Flow (Every 30 seconds)

```
┌────────────┐      ┌──────────┐      ┌─────────────┐      ┌──────────┐
│  Employee  │      │  Electron│      │   Backend   │      │ MongoDB  │
│  (working) │      │   Agent  │      │     API     │      │          │
└─────┬──────┘      └────┬─────┘      └──────┬──────┘      └────┬─────┘
      │                  │                   │                   │
      │  [Mouse clicks]  │                   │                   │
      │  [Key presses]   │                   │                   │
      ├─────────────────►│ Count events      │                   │
      │                  │                   │                   │
      │  [App switching] │                   │                   │
      ├─────────────────►│ Track active app  │                   │
      │                  │                   │                   │
      │                  │ Monitor idle time │                   │
      │                  │                   │                   │
      │        [Every 30 seconds]            │                   │
      │                  │                   │                   │
      │                  │ POST /api/activity/ingest             │
      │                  │ {                 │                   │
      │                  │   attendanceId,   │                   │
      │                  │   mouseEvents: 127,                   │
      │                  │   keyEvents: 53,  │                   │
      │                  │   idleSeconds: 5, │                   │
      │                  │   activeApp: "VSCode"                 │
      │                  │ }                 │                   │
      │                  ├──────────────────►│                   │
      │                  │                   │                   │
      │                  │                   │  Validate + Save  │
      │                  │                   ├──────────────────►│
      │                  │                   │                   │
      │                  │                   │  Success          │
      │                  │                   ◄──────────────────┤
      │                  │                   │                   │
      │                  │  Success          │                   │
      │                  ◄──────────────────┤                   │
      │                  │                   │                   │
      │                  │ Reset counters    │                   │
      │                  │                   │                   │
      │  [Stats updated] │                   │                   │
      ◄─────────────────┤                   │                   │
      │                  │                   │                   │
```

### 4. End Day Flow

```
┌────────────┐      ┌──────────┐      ┌─────────────┐      ┌──────────┐
│  Employee  │      │  Electron│      │   Backend   │      │ MongoDB  │
│            │      │   Agent  │      │     API     │      │          │
└─────┬──────┘      └────┬─────┘      └──────┬──────┘      └────┬─────┘
      │                  │                   │                   │
      │  Click "End Day" │                   │                   │
      ├─────────────────►│                   │                   │
      │                  │                   │                   │
      │                  │ POST /api/attendance/end              │
      │                  │  (Bearer token)   │                   │
      │                  ├──────────────────►│                   │
      │                  │                   │                   │
      │                  │                   │  Update record    │
      │                  │                   │  - Set endTime    │
      │                  │                   │  - status='ended' │
      │                  │                   ├──────────────────►│
      │                  │                   │                   │
      │                  │                   │  Success          │
      │                  │                   ◄──────────────────┤
      │                  │                   │                   │
      │                  │  Success          │                   │
      │                  ◄──────────────────┤                   │
      │                  │                   │                   │
      │                  │  ┌──────────────────────────────┐    │
      │                  │  │ Stop Activity Tracking:      │    │
      │                  │  │ - Send final data            │    │
      │                  │  │ - Stop iohook                │    │
      │                  │  │ - Clear intervals            │    │
      │                  │  │ - Reset state                │    │
      │                  │  └──────────────────────────────┘    │
      │                  │                   │                   │
      │  Tracking Stopped│                   │                   │
      ◄─────────────────┤                   │                   │
      │                  │                   │                   │
```

## Component Details

### Electron Main Process
- **Responsibilities:**
  - Window management
  - Tray icon creation
  - IPC communication
  - State management
  - Lifecycle events

- **Key Libraries:**
  - Electron API
  - electron-store (persistent storage)

### Renderer Process
- **Responsibilities:**
  - UI rendering
  - User interactions
  - Display tracking stats
  - Form handling

- **Key Technologies:**
  - HTML5
  - CSS3
  - Vanilla JavaScript

### Activity Tracker Manager
- **Responsibilities:**
  - Event counting
  - Application monitoring
  - Idle detection
  - Data aggregation
  - Transmission scheduling

- **Key Libraries:**
  - iohook: Global event listening
  - active-win: Window detection
  - node-idle-time: Idle monitoring

### API Service Layer
- **Responsibilities:**
  - HTTP requests
  - Authentication
  - Error handling
  - Response parsing

- **Key Libraries:**
  - axios: HTTP client
  - JWT: Token handling

## Security Architecture

```
┌─────────────────────────────────────────────────┐
│              Security Layers                    │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. Context Isolation (Preload Bridge)          │
│     ├─ Renderer cannot access Node.js           │
│     └─ Only exposed APIs available              │
│                                                 │
│  2. JWT Authentication                          │
│     ├─ Token-based auth                         │
│     ├─ Secure token storage (electron-store)    │
│     └─ Automatic token injection                │
│                                                 │
│  3. HTTPS Communication                         │
│     ├─ All API calls over HTTPS                 │
│     └─ Certificate validation                   │
│                                                 │
│  4. Data Privacy                                │
│     ├─ No local activity storage                │
│     ├─ Event counts only (no content)           │
│     └─ Consent-based tracking                   │
│                                                 │
│  5. User Control                                │
│     ├─ Visible tray icon                        │
│     ├─ Clear tracking status                    │
│     └─ Stop anytime capability                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Deployment Architecture

```
Development:
  npm start → Electron app → http://localhost:5000 (local backend)

Production:
  npm run build → .exe/.dmg → https://backend.company.com

Distribution:
  Installer files → Employee workstations → Backend (cloud)
```
