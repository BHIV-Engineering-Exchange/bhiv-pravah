# Gurukul Backend API (Refactored v2)
## How to Run
```powershell
# Windows
./run_dev.ps1
# OR
python -m app.main
```

## Architecture
- `app/main.py`: Entry point
- `app/routers/`: API endpoints
- `app/models/`: Database models
- `run_dev.ps1`: Startup script

# Old README Content


A FastAPI backend application running on a single port.

## Features

- FastAPI framework with automatic API documentation
- CORS middleware enabled
- RESTful API endpoints for CRUD operations
- Health check endpoint
- Interactive API documentation (Swagger UI)

## Installation

1. Create and activate virtual environment:

   **Windows (PowerShell):**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   **Windows (Command Prompt):**
   ```bash
   python -m venv venv
   venv\Scripts\activate.bat
   ```

   **Linux/Mac:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env` (if it doesn't exist, one will be created automatically)
   - Edit `.env` file to configure your settings:
     ```
     HOST=0.0.0.0
     PORT=8000
     DEBUG=True
     RELOAD=True
     API_TITLE=Gurukul Backend API
     CORS_ORIGINS=*
     ```

## Environment Variables

The application uses environment variables from the `.env` file for configuration:

- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)
- `DEBUG` - Debug mode (default: True)
- `RELOAD` - Auto-reload on code changes (default: True)
- `API_TITLE` - API title
- `API_DESCRIPTION` - API description
- `API_VERSION` - API version
- `CORS_ORIGINS` - Allowed CORS origins (use `*` for all or comma-separated list)

## Running the Application

### Option 1: Using Python directly
```bash
python main.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application will run on **http://localhost:8000**

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `GET /items` - Get all items
- `GET /items/{item_id}` - Get item by ID
- `POST /items` - Create a new item
- `PUT /items/{item_id}` - Update an item
- `DELETE /items/{item_id}` - Delete an item

## Example Request

Create an item:
```bash
curl -X POST "http://localhost:8000/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sample Item",
    "description": "This is a sample item",
    "price": 99.99
  }'
```

## Port Configuration

The application runs on **port 8000** by default. To change the port, edit the `PORT` variable in your `.env` file. The application will automatically load these settings when it starts.

**Note:** Never commit your `.env` file to version control. The `.env.example` file is provided as a template.
