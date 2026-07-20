#!/usr/bin/env python3
"""
Deployment script for AI Agent Logistics System
Handles cloud deployment to various platforms
"""

import os
import subprocess
import json
import sys
from pathlib import Path

class DeploymentManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.platforms = {
            'railway': self.deploy_to_railway,
            'render': self.deploy_to_render,
            'heroku': self.deploy_to_heroku,
            'docker': self.deploy_with_docker
        }
    
    def deploy_to_railway(self):
        """Deploy to Railway.app"""
        print("🚂 Deploying to Railway...")
        
        # Create railway.json if it doesn't exist
        railway_config = {
            "build": {
                "builder": "NIXPACKS"
            },
            "deploy": {
                "startCommand": "python start_server.py",
                "healthcheckPath": "/health"
            }
        }
        
        with open(self.project_root / "railway.json", "w") as f:
            json.dump(railway_config, f, indent=2)
        
        # Create Procfile for Railway
        with open(self.project_root / "Procfile", "w") as f:
            f.write("web: python start_server.py\n")
            f.write("worker: python agent.py\n")
        
        print("✅ Railway configuration created")
        print("📝 Next steps:")
        print("1. Install Railway CLI: npm install -g @railway/cli")
        print("2. Login: railway login")
        print("3. Deploy: railway up")
        
    def deploy_to_render(self):
        """Deploy to Render.com"""
        print("🎨 Deploying to Render...")
        
        # Create render.yaml
        render_config = {
            "services": [
                {
                    "type": "web",
                    "name": "ai-agent-api",
                    "env": "python",
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": "python start_server.py",
                    "healthCheckPath": "/health"
                },
                {
                    "type": "worker",
                    "name": "ai-agent-worker",
                    "env": "python",
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": "python agent.py"
                }
            ]
        }
        
        with open(self.project_root / "render.yaml", "w") as f:
            import yaml
            yaml.dump(render_config, f, default_flow_style=False)
        
        print("✅ Render configuration created")
        print("📝 Next steps:")
        print("1. Connect your GitHub repo to Render")
        print("2. Create new Web Service from render.yaml")
        
    def deploy_to_heroku(self):
        """Deploy to Heroku"""
        print("🟣 Deploying to Heroku...")
        
        # Create Procfile
        with open(self.project_root / "Procfile", "w") as f:
            f.write("web: python start_server.py\n")
            f.write("worker: python agent.py\n")
        
        # Create runtime.txt
        with open(self.project_root / "runtime.txt", "w") as f:
            f.write("python-3.11.0\n")
        
        print("✅ Heroku configuration created")
        print("📝 Next steps:")
        print("1. Install Heroku CLI")
        print("2. heroku create your-app-name")
        print("3. git push heroku main")
        
    def deploy_with_docker(self):
        """Deploy using Docker"""
        print("🐳 Building Docker containers...")
        
        try:
            # Build main application
            subprocess.run([
                "docker", "build", "-t", "ai-agent:latest", "."
            ], cwd=self.project_root, check=True)
            
            # Build dashboard
            subprocess.run([
                "docker", "build", "-f", "Dockerfile.dashboard", 
                "-t", "ai-agent-dashboard:latest", "."
            ], cwd=self.project_root, check=True)
            
            print("✅ Docker images built successfully")
            print("📝 To run:")
            print("docker-compose up -d")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker build failed: {e}")
    
    def create_production_env(self):
        """Create production environment file"""
        env_content = """# Production Environment Variables
# Copy this to .env.production and fill in your values

# OpenAI API Key (required for smart chatbot)
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///logistics_agent.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Email Configuration (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Monitoring
SENTRY_DSN=your_sentry_dsn_here

# Feature Flags
ENABLE_SMART_CHATBOT=true
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_HUMAN_REVIEW=true
"""
        
        with open(self.project_root / ".env.production.example", "w") as f:
            f.write(env_content)
        
        print("✅ Production environment template created")
    
    def run_health_check(self):
        """Run comprehensive health check"""
        print("🏥 Running health check...")
        
        checks = [
            ("Database", self.check_database),
            ("API Endpoints", self.check_api),
            ("Agent Logic", self.check_agent),
            ("Dependencies", self.check_dependencies)
        ]
        
        results = {}
        for name, check_func in checks:
            try:
                results[name] = check_func()
                print(f"✅ {name}: OK")
            except Exception as e:
                results[name] = str(e)
                print(f"❌ {name}: {e}")
        
        return results
    
    def check_database(self):
        """Check database connectivity"""
        from database.service import DatabaseService
        with DatabaseService() as db:
            # Try to query something
            orders = db.get_orders()
            return f"Connected, {len(orders)} orders found"
    
    def check_api(self):
        """Check API endpoints"""
        import requests
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            return f"API responding: {response.status_code}"
        except:
            return "API not running on localhost:8000"
    
    def check_agent(self):
        """Check agent functionality"""
        from agent import sense, plan, act
        returns_data = sense()
        if returns_data is not None:
            return f"Agent functional, {len(returns_data)} returns processed"
        return "Agent check failed"
    
    def check_dependencies(self):
        """Check all dependencies are installed"""
        import pkg_resources
        with open(self.project_root / "requirements.txt") as f:
            requirements = f.read().splitlines()
        
        missing = []
        for req in requirements:
            if req.strip() and not req.startswith('#'):
                try:
                    pkg_resources.require(req)
                except:
                    missing.append(req)
        
        if missing:
            raise Exception(f"Missing dependencies: {missing}")
        return f"All {len(requirements)} dependencies satisfied"

def main():
    """Main deployment function"""
    if len(sys.argv) < 2:
        print("Usage: python deploy.py <platform>")
        print("Platforms: railway, render, heroku, docker, health-check")
        return
    
    platform = sys.argv[1].lower()
    deployer = DeploymentManager()
    
    if platform == "health-check":
        deployer.run_health_check()
    elif platform in deployer.platforms:
        deployer.create_production_env()
        deployer.platforms[platform]()
    else:
        print(f"Unknown platform: {platform}")
        print("Available platforms:", list(deployer.platforms.keys()))

if __name__ == "__main__":
    main()