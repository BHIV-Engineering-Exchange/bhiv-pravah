# Running Gurukul on Localhost

This guide explains how to run the Gurukul application on your local machine for development.

## Prerequisites

- **Node.js** (v18 or higher) - for frontend
- **Python** (v3.10 or higher) - for backend
- **Git** - to clone the repository

## Quick Start

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. (Optional) Create `.env` file:
   ```bash
   copy .env.example .env
   ```
   The backend will work with defaults (SQLite database, port 3000).

6. Run the backend:
   ```bash
   python -m app.main
   ```
   Or use the PowerShell script:
   ```powershell
   .\run_dev.ps1
   ```

   The backend should start on `http://localhost:3000`

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd Frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. (Optional) Create `.env` file:
   ```bash
   copy .env.example .env
   ```
   The frontend will auto-detect localhost if no `.env` is provided.

4. Run the development server:
   ```bash
   npm run dev
   ```

   The frontend should start on `http://localhost:5173`

## How It Works

### Automatic Detection

The frontend automatically detects if it's running on localhost:
- **On localhost**: Uses `http://localhost:3000` for API calls
- **On production (Render)**: Uses `https://gurukul-backend-kap2.onrender.com`

### Development Proxy

During development, Vite proxies all `/api/*` requests to `http://localhost:3000`, so you don't need to configure CORS.

### Database

- **Localhost**: Uses SQLite (`gurukul.db` file in the backend directory)
- **Production (Render)**: Uses PostgreSQL (configured via `DATABASE_URL`)

## Troubleshooting

### Backend won't start
- Make sure port 3000 is not in use by another application
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.10+)

### Frontend can't connect to backend
- Make sure the backend is running on `http://localhost:3000`
- Check browser console for CORS errors
- Verify the `VITE_API_URL` in `.env` or check auto-detection in `config.js`

### Database issues
- SQLite database file (`gurukul.db`) will be created automatically
- If you see database errors, delete `gurukul.db` and restart the backend (tables will be recreated)

## Environment Variables

### Frontend (.env)
- `VITE_API_URL` - Backend API URL (optional, auto-detects localhost)

### Backend (.env)
- `DATABASE_URL` - Database connection string (optional, defaults to SQLite)
- `JWT_SECRET_KEY` - Secret key for JWT tokens (change in production!)
- `PORT` - Backend port (default: 3000)
- `HOST` - Backend host (default: 0.0.0.0)

## Running Both Servers

You need to run both the backend and frontend simultaneously:

1. **Terminal 1** - Backend:
   ```bash
   cd backend
   python -m app.main
   ```

2. **Terminal 2** - Frontend:
   ```bash
   cd Frontend
   npm run dev
   ```

Then open `http://localhost:5173` in your browser.

## Production Deployment

For production on Render:
- Frontend: Set `VITE_API_URL` to your Render backend URL
- Backend: Set `DATABASE_URL` to your PostgreSQL connection string
- Backend: Set `JWT_SECRET_KEY` to a secure random string

