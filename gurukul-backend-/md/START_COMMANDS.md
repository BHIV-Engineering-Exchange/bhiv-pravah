# Commands to Start Gurukul and EMS Systems

## Quick Start (All Services)

Open **4 separate terminal windows** and run the commands below in each:

---

## Terminal 1: Gurukul Backend
```powershell
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```
**Runs on:** http://localhost:3000

---

## Terminal 2: EMS Backend
```powershell
cd "EMS System"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
**Runs on:** http://localhost:8000

---

## Terminal 3: Gurukul Frontend
```powershell
cd Frontend
npm run dev
```
**Runs on:** http://localhost:5173

---

## Terminal 4: EMS Frontend
```powershell
cd "EMS System\frontend"
npm run dev
```
**Runs on:** http://localhost:3001

---

## Summary of Ports

| Service | Port | URL |
|---------|------|-----|
| Gurukul Backend | 3000 | http://localhost:3000 |
| EMS Backend | 8000 | http://localhost:8000 |
| Gurukul Frontend | 5173 | http://localhost:5173 |
| EMS Frontend | 3001 | http://localhost:3001 |

---

## Alternative: PowerShell Script (All in One)

Create a file `start-all.ps1` and run it:

```powershell
# Start Gurukul Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload"

# Start EMS Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'EMS System'; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# Start Gurukul Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd Frontend; npm run dev"

# Start EMS Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'EMS System\frontend'; npm run dev"

Write-Host "All services starting in separate windows..."
Write-Host "Gurukul Backend: http://localhost:3000"
Write-Host "EMS Backend: http://localhost:8000"
Write-Host "Gurukul Frontend: http://localhost:5173"
Write-Host "EMS Frontend: http://localhost:3001"
```

---

## Prerequisites

Make sure you have:
- Python 3.8+ installed
- Node.js and npm installed
- All dependencies installed:
  - `cd backend && pip install -r requirements.txt`
  - `cd Frontend && npm install`
  - `cd "EMS System" && pip install -r requirements.txt`
  - `cd "EMS System\frontend" && npm install`

---

## Troubleshooting

- **Port already in use**: Stop the service using that port or change the port in the command
- **Module not found**: Make sure you've installed all dependencies
- **Database errors**: Make sure database files exist and are accessible
