# AI Integration Admin Panel

A modern React-based admin panel for managing and monitoring AI agents and baskets in the AI Integration Platform.

## Features

- **Agents Management**: View all available agents with their specifications, capabilities, and schemas
- **Baskets Management**: Monitor agent baskets, their configurations, and test cases
- **Real-time Health Monitoring**: Check backend connectivity and service status
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Interactive UI**: Click on agents/baskets to expand detailed information

## Quick Start

### Prerequisites
- Node.js 14+ installed
- AI Integration backend running on http://localhost:8000

### 1. Start the Backend
Navigate to the main AI_integration directory and run:

**Option A: Using the startup scripts**
```bash
# Windows PowerShell
.\start_backend.ps1

# Windows Command Prompt
start_backend.bat
```

**Option B: Manual start**
```bash
cd AI_integration
python main.py
```

The backend should start on http://localhost:8000

### 2. Start the Admin Panel
```bash
cd admin-panel
npm run dev
```

The admin panel will be available at http://localhost:5173

## Usage Guide

### Agents Tab
- **View All Agents**: See a grid of all available agents
- **Agent Details**: Click on any agent card to expand and see:
  - Input/Output schemas
  - Sample input/output data
  - Capabilities and domains
  - Module path information

### Baskets Tab
- **View All Baskets**: See all configured agent baskets
- **Basket Configuration**: Click to expand and see:
  - Execution strategy
  - Included agents
  - Test cases with expected inputs/outputs
  - Source information (file or registry)

### Health Status
- **Connection Indicator**: Top-right shows backend connectivity
- **Service Status**: Bottom panel shows individual service health:
  - MongoDB connection
  - Redis connection
  - Socket.IO connection

## API Endpoints Used

The admin panel connects to these backend endpoints:

- `GET /health` - System health check
- `GET /agents` - Fetch all available agents
- `GET /baskets` - Fetch all available baskets

## Troubleshooting

### Backend Connection Issues
If you see "Backend Connection Error":

1. **Check Backend Status**: Ensure the FastAPI server is running
   ```bash
   curl http://localhost:8000/health
   # or in PowerShell:
   Invoke-RestMethod -Uri http://localhost:8000/health
   ```

2. **Verify CORS Settings**: The backend should allow requests from http://localhost:5173

3. **Check Port Conflicts**: Make sure port 8000 is not used by another service

### Frontend Issues
If the admin panel doesn't load:

1. **Check Node.js**: Ensure Node.js 14+ is installed
2. **Install Dependencies**: Run `npm install` in the admin-panel directory
3. **Port Conflicts**: If port 5173 is busy, Vite will suggest an alternative

### No Data Showing
If agents or baskets don't appear:

1. **Backend Health**: Check if backend services are connected
2. **Agent Registry**: Ensure agents are properly registered in the backend
3. **Basket Configuration**: Verify basket files exist in the baskets/ directory

## Development

### Project Structure
```
admin-panel/
├── src/
│   ├── components/
│   │   ├── AdminDashboard.jsx    # Main dashboard component
│   │   ├── AgentsList.jsx        # Agents listing and details
│   │   ├── BasketsList.jsx       # Baskets listing and details
│   │   └── *.css                 # Component styles
│   ├── services/
│   │   └── api.js                # API service for backend communication
│   ├── App.jsx                   # Main app component
│   └── main.jsx                  # Entry point
├── package.json
└── vite.config.js
```

### Adding New Features
1. **New API Endpoints**: Add methods to `src/services/api.js`
2. **New Components**: Create in `src/components/`
3. **Styling**: Use CSS modules or add to existing CSS files

### Building for Production
```bash
npm run build
```

The built files will be in the `dist/` directory.

## Support

For issues or questions:
1. Check the main AI Integration README
2. Verify backend logs for errors
3. Check browser console for frontend errors

## Version
- Admin Panel: 1.0.0
- Compatible with AI Integration Platform backend
