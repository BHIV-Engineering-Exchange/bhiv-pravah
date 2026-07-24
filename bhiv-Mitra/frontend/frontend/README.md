# AI Assistant Frontend

A modern React frontend for the MITRA AI Assistant system with BHIV ecosystem dashboard.

## Active Deployment Topology

This frontend is part of the integrated deployment:

- `backend/` on Render (or Docker/Kubernetes)
- `frontend/frontend/` on Vercel

Authentication is handled by the FastAPI backend.

## Features

### Core Chat
- Single assistant interface with iOS-inspired design
- Message input with keyboard shortcuts (Enter to send, Shift+Enter for new line)
- Response panel with intent, safety, enforcement, and task display
- TTS integration with browser fallback
- Multi-language support via Google Translate

### Authentication
- Email/password signup and login
- JWT token management
- Session restore on page reload

### Dashboard (NEW)
- **BHIVDashboard**: Ecosystem overview with KPIs, product grid, enforcement metrics
- **ReplayVisualization**: Trace pipeline visualization by trace ID
- **SystemHealthPanel**: Real-time health monitoring with auto-refresh

### Chat History
- Conversation persistence in localStorage
- Create, select, delete conversations
- Responsive sidebar with mobile overlay

## Technology Stack

- **React 19** with TypeScript
- **Tailwind CSS** with custom iOS design system
- **Fetch API** for backend communication

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API running (default: http://localhost:8000)

### Installation

```bash
npm install
```

### Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_KEY=your-api-key-here
```

### Start Development Server

```bash
npm start
```

Opens at http://localhost:3000

### Build for Production

```bash
npm run build
```

## Component Structure

```
src/
├── components/
│   ├── auth/
│   │   ├── Login.tsx
│   │   └── Signup.tsx
│   ├── dashboard/
│   │   ├── BHIVDashboard.tsx
│   │   ├── ReplayVisualization.tsx
│   │   └── SystemHealthPanel.tsx
│   ├── ChatSidebar.tsx
│   ├── ChatMessage.tsx
│   ├── MessageInput.tsx
│   ├── Toast.tsx
│   ├── ConnectionStatus.tsx
│   ├── LanguageDropdown.tsx
│   ├── StatusIndicator.tsx
│   ├── LoadingSpinner.tsx
│   ├── TaskCard.tsx
│   ├── ActionCard.tsx
│   ├── EnforcementBadge.tsx
│   ├── SafetyLabel.tsx
│   └── NextStepHint.tsx
├── services/
│   ├── api.ts
│   └── authApi.ts
├── contexts/
│   ├── AuthContext.tsx
│   └── LanguageContext.tsx
├── utils/
│   ├── translations.ts
│   └── uxTranslations.ts
├── types.ts
├── App.tsx
└── index.tsx
```

## API Integration

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/assistant` | POST | Main chat |
| `/api/auth/signup` | POST | Registration |
| `/api/auth/login` | POST | Login |
| `/api/auth/me` | GET | Session restore |
| `/api/auth/logout` | POST | Logout |
| `/api/tts` | POST | Text-to-speech |
| `/health` | GET | Health check |
| `/api/system/info` | GET | System info |
| `/api/system/stats` | GET | System stats |

### Authentication

All requests include `X-API-Key` header. After login, bearer token is also sent.

## Deployment

### Vercel

1. Push to GitHub
2. Import in Vercel
3. Set root directory to `frontend/frontend`
4. Set environment variables
5. Deploy

### Other Platforms

The `build` folder contains static files for any hosting:
- Netlify
- GitHub Pages
- AWS S3 + CloudFront
- Azure Static Web Apps

## UX Design Principles

1. **Information Hierarchy**: Clear visual hierarchy
2. **Action Transparency**: Every action visible and traceable
3. **Feedback**: Immediate visual feedback
4. **Error Prevention**: Input validation and clear messages
5. **Accessibility**: Semantic HTML, keyboard navigation
6. **Responsive Design**: Desktop, tablet, mobile
7. **Performance**: Optimized rendering

## License

Part of the BHIV Ecosystem.
