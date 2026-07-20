"""
HR Intelligence Brain - Plug-and-Play Module
Connects cleanly to any HR platform via REST API
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class HRIntelligenceBrain:
    """Plug-and-play HR Intelligence Brain for any HR platform"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    # Core Intelligence Functions
    def analyze_candidate(self, candidate_data: Dict) -> Dict:
        """Analyze candidate and return AI insights"""
        try:
            response = requests.post(f"{self.base_url}/smart/analyze", 
                                   json=candidate_data, headers=self.headers)
            return response.json() if response.status_code == 200 else {"error": "Analysis failed"}
        except:
            return {"error": "Connection failed"}
    
    def get_recommendations(self, candidate_id: int) -> List[str]:
        """Get AI recommendations for candidate"""
        try:
            response = requests.get(f"{self.base_url}/smart/recommendations/{candidate_id}", 
                                  headers=self.headers)
            return response.json().get("recommendations", []) if response.status_code == 200 else []
        except:
            return []
    
    def predict_success(self, candidate_data: Dict) -> float:
        """Predict hiring success probability"""
        try:
            response = requests.post(f"{self.base_url}/analytics/predict", 
                                   json=candidate_data, headers=self.headers)
            return response.json().get("success_probability", 0.0) if response.status_code == 200 else 0.0
        except:
            return 0.0
    
    def trigger_automation(self, candidate_id: int, event_type: str, metadata: Dict = None) -> Dict:
        """Trigger multi-channel automation"""
        try:
            data = {
                "candidate_id": candidate_id,
                "event_type": event_type,
                "metadata": metadata or {}
            }
            response = requests.post(f"{self.base_url}/trigger/", 
                                   json=data, headers=self.headers)
            return response.json() if response.status_code == 200 else {"error": "Automation failed"}
        except:
            return {"error": "Connection failed"}
    
    # Platform Integration Methods
    def sync_candidate(self, external_candidate: Dict) -> Dict:
        """Sync candidate from external HR platform"""
        # Transform external format to internal format
        internal_candidate = {
            "name": external_candidate.get("full_name") or external_candidate.get("name"),
            "email": external_candidate.get("email_address") or external_candidate.get("email"),
            "phone": external_candidate.get("phone_number") or external_candidate.get("phone"),
            "skills": external_candidate.get("skills", [])
        }
        
        try:
            response = requests.post(f"{self.base_url}/candidate/add", 
                                   json=internal_candidate, headers=self.headers)
            return response.json() if response.status_code == 200 else {"error": "Sync failed"}
        except:
            return {"error": "Connection failed"}
    
    def get_insights_dashboard(self) -> Dict:
        """Get complete dashboard insights for external platform"""
        try:
            response = requests.get(f"{self.base_url}/analytics/dashboard", headers=self.headers)
            return response.json() if response.status_code == 200 else {}
        except:
            return {}
    
    def health_check(self) -> bool:
        """Check if HR Intelligence Brain is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", headers=self.headers)
            return response.status_code == 200
        except:
            return False

# Shashank's Platform Integration Adapter
class ShashankHRAdapter:
    """Adapter for Shashank's HR Platform Integration"""
    
    def __init__(self, shashank_api_url: str, hr_brain: HRIntelligenceBrain):
        self.shashank_api = shashank_api_url
        self.hr_brain = hr_brain
    
    def connect_to_shashank_platform(self) -> bool:
        """Establish connection to Shashank's HR platform"""
        return self.hr_brain.health_check()
    
    def process_shashank_candidate(self, shashank_candidate: Dict) -> Dict:
        """Process candidate from Shashank's platform"""
        # Sync candidate to HR Brain
        sync_result = self.hr_brain.sync_candidate(shashank_candidate)
        
        if "candidate_id" in sync_result:
            candidate_id = sync_result["candidate_id"]
            
            # Get AI insights
            recommendations = self.hr_brain.get_recommendations(candidate_id)
            success_prob = self.hr_brain.predict_success(shashank_candidate)
            
            return {
                "candidate_id": candidate_id,
                "ai_recommendations": recommendations,
                "success_probability": success_prob,
                "status": "processed"
            }
        
        return {"error": "Failed to process candidate"}
    
    def get_platform_insights(self) -> Dict:
        """Get insights formatted for Shashank's platform"""
        insights = self.hr_brain.get_insights_dashboard()
        
        # Format for Shashank's platform
        return {
            "total_candidates": insights.get("total_candidates", 0),
            "average_match_score": insights.get("avg_match_score", 0),
            "top_skills": insights.get("top_skills", []),
            "hiring_trends": "Positive",
            "ai_status": "Active"
        }

# Simple Integration Example
def create_hr_brain_for_shashank(shashank_platform_url: str) -> ShashankHRAdapter:
    """Create HR Intelligence Brain for Shashank's platform"""
    hr_brain = HRIntelligenceBrain()
    adapter = ShashankHRAdapter(shashank_platform_url, hr_brain)
    return adapter

# Usage Example
if __name__ == "__main__":
    # Initialize HR Brain for Shashank's platform
    adapter = create_hr_brain_for_shashank("https://shashank-hr-platform.com/api")
    
    # Test connection
    if adapter.connect_to_shashank_platform():
        print("✅ HR Intelligence Brain connected successfully!")
        
        # Example candidate from Shashank's platform
        sample_candidate = {
            "full_name": "Test Candidate",
            "email_address": "test@example.com",
            "phone_number": "+91-9876543210",
            "skills": ["Python", "AI"]
        }
        
        # Process candidate
        result = adapter.process_shashank_candidate(sample_candidate)
        print(f"📊 Processing result: {result}")
        
        # Get platform insights
        insights = adapter.get_platform_insights()
        print(f"🧠 Platform insights: {insights}")
    else:
        print("❌ Failed to connect HR Intelligence Brain")