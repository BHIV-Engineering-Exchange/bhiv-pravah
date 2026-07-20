    # AI Agent Logistics System - Quick Start

## How to Run the Project

Simply double-click the `run_project.bat` file in the project directory, or run it from command prompt:

```cmd
run_project.bat
```

This will automatically start all services with the correct configuration.

## Services Started

- **API Server**: http://localhost:8000
- **CRM Dashboard**: http://localhost:8502
- **Main Dashboard**: http://localhost:8503
- **Product Catalog**: http://localhost:8505
- **API Documentation**: http://localhost:8000/docs

## Configuration

The batch file includes:
- Proper Unicode encoding support (`PYTHONIOENCODING=utf-8`)
- Headless Streamlit mode for server deployment
- Automatic cleanup of existing processes
- Proper startup sequencing

## Stopping Services

To stop all services, close the command prompt windows or use Task Manager to end the processes.

## Dependencies

All required Python packages are already installed. If you encounter any issues, run:

```cmd
pip install -r requirements.txt
```

## Notes

- Services run in background windows
- The batch file handles process cleanup automatically
- All dashboards are configured for headless operation