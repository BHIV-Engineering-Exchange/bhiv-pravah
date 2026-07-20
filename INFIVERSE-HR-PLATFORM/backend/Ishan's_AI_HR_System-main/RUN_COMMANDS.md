# 🚀 HR-AI System Run Commands

## **Quick Start (Recommended)**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start complete system
python start_system.py
```

## **Manual Start Commands**

### **Backend Only**
```bash
python run_fastapi.py
# OR
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

### **Dashboard Only**
```bash
streamlit run dashboard/app.py
```

### **Both Services**
```bash
# Terminal 1: Backend
python run_fastapi.py

# Terminal 2: Dashboard
streamlit run dashboard/app.py
```

## **Production Commands**

### **With Gunicorn**
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:5000
```

### **Background Services**
```bash
# Backend in background
nohup python run_fastapi.py &

# Dashboard in background
nohup streamlit run dashboard/app.py &
```

## **Testing Commands**

```bash
# System health test
python simple_test.py

# API tests
python test_api.py

# Robustness tests
python test_robustness.py
```

## **Access URLs**

- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/health
- **System Status**: http://localhost:5000/system/status

## **Environment Setup**

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## **Docker Commands (Optional)**

```bash
# Build image
docker build -t hr-ai-system .

# Run container
docker run -p 5000:5000 -p 8501:8501 hr-ai-system
```