# AI Agent Logistics Dashboard Frontend

A modern, mobile-responsive React dashboard replacing the Streamlit interface for production use.

## Features

- **Mobile-Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Real-time Dashboard**: Live KPIs, charts, and alerts
- **Employee Self-Service Portal**: Personal metrics, review requests, and attendance tracking
- **Facial Recognition Attendance**: Privacy-compliant biometric attendance system
- **Material-UI Components**: Professional, accessible interface

## Quick Start

### Development
```bash
npm install
npm start
```

### Production Build
```bash
npm run build:prod
npm run serve
```

### Docker Deployment
```bash
docker build -t logistics-dashboard .
docker run -p 3000:80 logistics-dashboard
```

## Environment Variables

Create `.env.local` for development:
```
REACT_APP_API_URL=http://localhost:8000
```

## API Integration

The frontend connects to the FastAPI backend at `/api/` endpoints:

- `/api/dashboard/*` - Dashboard data and KPIs
- `/api/employee/*` - Employee self-service features
- `/api/attendance/*` - Attendance management

## Components

- **Dashboard**: Main analytics view with KPIs and charts
- **EmployeePortal**: Personal metrics and review requests
- **AttendanceSystem**: Facial recognition check-in/out
- **Navigation**: Responsive navigation with mobile drawer

## Production Deployment

1. Build the application: `npm run build:prod`
2. Serve with nginx or any static file server
3. Configure API proxy for backend communication
4. Enable HTTPS in production environment

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Security Features

- JWT authentication
- HTTPS enforcement
- Content Security Policy
- XSS protection headers
- Privacy-compliant facial recognition
