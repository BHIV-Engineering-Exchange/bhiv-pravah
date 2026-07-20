# AI Integration Platform - Complete Startup Guide

## 🚀 Quick Start (Step by Step)

### Step 1: Start the Backend Server
Navigate to the main AI_integration directory and run:

```bash
# Option 1: Use the startup script (Recommended)
start_backend.bat

# Option 2: Manual start
python main.py
```

**Expected Output:**
```
INFO: Started server process [PID]
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Verify Backend is Running:**
```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

### Step 2: Start the Admin Panel Frontend
Open a new terminal, navigate to the admin-panel directory and run:

```bash
# Option 1: Use the startup script (Recommended)
cd admin-panel
start_frontend.bat

# Option 2: Manual start
cd admin-panel
C:\Users\nipun\OneDrive\Attachments\Desktop\gitvlone\AI_integration\admin-panel\node_modules\.bin\vite.cmd
```

**Expected Output:**
```
VITE v6.3.5  ready in 193 ms
➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Step 3: Access the Admin Panel
Open your browser and go to: **http://localhost:5173**

## 🎯 What You'll See

### Admin Panel Features:
- **Agents Tab**: View all available AI agents with their specifications
- **Baskets Tab**: Monitor agent baskets and their configurations  
- **Health Status**: Real-time backend connectivity monitoring
- **Interactive UI**: Click on cards to expand detailed information

### Expected Data:
- **Agents**: cashflow_analyzer, vedic_quiz_agent, workflow_agent, etc.
- **Baskets**: finance_daily_check, gurukul_practice, content_analysis, etc.
- **Health**: MongoDB, Redis, and Socket.IO connection status

## 🔧 Troubleshooting

### Backend Issues:
1. **Port 8000 in use**: Change FASTAPI_PORT in .env file
2. **Python not found**: Ensure Python 3.9+ is installed and in PATH
3. **Dependencies missing**: Run `pip install -r requirements.txt`

### Frontend Issues:
1. **Port 5173 in use**: Vite will automatically suggest an alternative port
2. **Blank page**: Check browser console for JavaScript errors
3. **404 errors**: Ensure you're using the correct startup command

### Connection Issues:
1. **Backend Connection Error**: Verify backend is running on port 8000
2. **CORS errors**: Backend is configured to allow localhost:5173
3. **No data showing**: Check if agents and baskets are properly configured

## 📁 Project Structure

```
AI_integration/
├── main.py                 # FastAPI backend server
├── start_backend.bat       # Backend startup script
├── agents/                 # AI agents directory
├── baskets/               # Agent baskets configuration
├── admin-panel/           # React frontend
│   ├── start_frontend.bat # Frontend startup script
│   ├── src/
│   │   ├── components/    # React components
│   │   └── services/      # API services
│   └── package.json
└── README.md
```

## 🌐 URLs

- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:5173
- **API Health**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

## 🔄 Development Workflow

1. **Start Backend**: Always start the backend first
2. **Start Frontend**: Then start the admin panel
3. **Development**: Both support hot reload for development
4. **Testing**: Use the admin panel to test agents and baskets

## 📝 Notes

- The admin panel will show a connection error if the backend is not running
- Both servers support hot reload - changes will be reflected automatically
- Use Ctrl+C to stop either server
- The frontend automatically retries backend connections

## 🎉 Success Indicators

✅ Backend shows "Application startup complete"  
✅ Frontend shows "VITE ready"  
✅ Admin panel loads at http://localhost:5173  
✅ Health status shows green "All systems operational"  
✅ Agents and baskets are visible in their respective tabs  

If you see all these indicators, your AI Integration Platform is running successfully!
