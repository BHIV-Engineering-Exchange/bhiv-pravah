# 🚀 Complete Dashboard Launcher

Launch all three dashboards (CRM, Product Image, and Supplier Management) with a single command!

## 🎯 Quick Start

### Option 1: Python Script (Recommended)
```bash
cd "/Users/rishabh/Desktop/Voice bot/ai-agent_project"
python3 start_all_dashboards.py
```

### Option 2: Shell Script (Simple)
```bash
cd "/Users/rishabh/Desktop/Voice bot/ai-agent_project"
./launch_all.sh
```

## 📊 What Gets Started

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **CRM API** | 8001 | http://localhost:8001 | CRM backend API |
| **Main API** | 8000 | http://localhost:8000 | Logistics API with images |
| **CRM Dashboard** | 8501 | http://localhost:8501 | Customer management |
| **Main Dashboard** | 8502 | http://localhost:8502 | Logistics & inventory |
| **Supplier Dashboard** | 8503 | http://localhost:8503 | Enhanced supplier tools |
| **Product Catalog** | 8504 | http://localhost:8504 | Product image management |
| **Supplier Showcase** | 8505 | http://localhost:8505 | Professional supplier portal |

## 🎯 Quick Access

- **👤 For CRM & Customers:** → http://localhost:8501
- **📦 For Products & Inventory:** → http://localhost:8504
- **🏪 For Suppliers:** → http://localhost:8503
- **🤖 For AI Queries:** → http://localhost:8501 (Natural Language section)

## 🛑 Stop All Services

Press `Ctrl+C` in the terminal where you started the launcher.

## 🔧 Troubleshooting

If services fail to start:
1. Check virtual environment: `source venv_new/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Check ports aren't in use: `lsof -i :8501`

## ✨ Features Available

- ✅ Complete CRM System (Accounts, Contacts, Leads, Opportunities)
- ✅ Product Image Management & Upload
- ✅ Professional Supplier Showcase
- ✅ AI-Powered Natural Language Queries
- ✅ Autonomous Logistics Agents
- ✅ Inventory & Order Management
- ✅ Email Notifications & Alerts
- ✅ Performance Analytics & Reports