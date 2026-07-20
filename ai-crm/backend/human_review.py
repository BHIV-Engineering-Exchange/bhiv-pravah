import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional

class HumanReviewSystem:
    def __init__(self):
        self.pending_reviews_file = "data/pending_reviews.json"
        self.review_log_file = "data/review_log.csv"
        self.confidence_threshold = 0.7
        
    def calculate_confidence(self, action_type: str, data: Dict) -> float:
        """Calculate confidence score for agent decisions"""    
        confidence = 0.8  # Start with base confidence
        
        if action_type == "restock":
            # Lower confidence for very high quantities
            quantity = data.get("quantity", 0)
            if quantity > 25:   
                confidence = 0.5  # Low confidence for very high quantities
            elif quantity > 20:
                confidence = 0.6
            elif quantity > 10:
                confidence = 0.7
                
            # Lower confidence if no historical data
            if not self._has_historical_data(data.get("product_id")):
                confidence -= 0.1
                
        elif action_type == "chatbot_response":
            # Lower confidence for complex queries
            query = data.get("query", "").lower()
            urgent_words = ["urgent", "emergency", "complaint", "refund"]
            urgent_count = sum(1 for word in urgent_words if word in query)
            
            if urgent_count >= 2:
                confidence = 0.3  # Very low confidence for multiple urgent keywords
            elif urgent_count == 1:
                confidence = 0.6  # Medium confidence for single urgent keyword
                
        return max(0.1, min(1.0, confidence))
    
    def _has_historical_data(self, product_id: str) -> bool:
        """Check if we have historical data for this product"""
        try:
            returns_df = pd.read_excel("data/returns.xlsx")
            return product_id in returns_df["ProductID"].values
        except:
            return False
    
    def requires_human_review(self, action_type: str, data: Dict) -> bool:
        """Determine if action requires human review"""
        confidence = self.calculate_confidence(action_type, data)
        return confidence < self.confidence_threshold
    
    def submit_for_review(self, action_type: str, data: Dict, agent_decision: str) -> str:
        """Submit decision for human review"""
        review_id = f"{action_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        confidence = self.calculate_confidence(action_type, data)
        
        review_item = {
            "review_id": review_id,
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "confidence": confidence,
            "data": data,
            "agent_decision": agent_decision,
            "status": "pending",
            "human_decision": None,
            "human_notes": None
        }
        
        # Load existing pending reviews
        try:
            with open(self.pending_reviews_file, 'r') as f:
                pending_reviews = json.load(f)
        except FileNotFoundError:
            pending_reviews = []
        
        pending_reviews.append(review_item)
        
        # Save updated pending reviews
        with open(self.pending_reviews_file, 'w') as f:
            json.dump(pending_reviews, f, indent=2)
        
        print(f"⚠️  Action submitted for human review (ID: {review_id}, Confidence: {confidence:.2f})")
        return review_id
    
    def get_pending_reviews(self) -> List[Dict]:
        """Get all pending reviews"""
        try:
            with open(self.pending_reviews_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def approve_decision(self, review_id: str, notes: str = "") -> bool:
        """Approve a pending decision"""
        return self._update_review_status(review_id, "approved", notes)
    
    def reject_decision(self, review_id: str, notes: str = "") -> bool:
        """Reject a pending decision"""
        return self._update_review_status(review_id, "rejected", notes)
    
    def _update_review_status(self, review_id: str, decision: str, notes: str) -> bool:
        """Update review status and log the decision"""
        pending_reviews = self.get_pending_reviews()
        
        for review in pending_reviews:
            if review["review_id"] == review_id:
                review["status"] = decision
                review["human_decision"] = decision
                review["human_notes"] = notes
                review["reviewed_at"] = datetime.now().isoformat()
                
                # Log the review
                self._log_review(review)
                
                # Remove from pending
                pending_reviews.remove(review)
                
                # Save updated pending reviews
                with open(self.pending_reviews_file, 'w') as f:
                    json.dump(pending_reviews, f, indent=2)
                
                print(f"✅ Review {review_id} {decision}")
                return True
        
        print(f"❌ Review {review_id} not found")
        return False
    
    def _log_review(self, review: Dict):
        """Log completed review to CSV"""
        log_entry = {
            "timestamp": review["reviewed_at"],
            "review_id": review["review_id"],
            "action_type": review["action_type"],
            "confidence": review["confidence"],
            "agent_decision": review["agent_decision"],
            "human_decision": review["human_decision"],
            "notes": review["human_notes"]
        }
        
        df = pd.DataFrame([log_entry])
        try:
            # Append to existing log
            df.to_csv(self.review_log_file, mode='a', index=False, header=False)
        except FileNotFoundError:
            # Create new log with header
            df.to_csv(self.review_log_file, mode='w', index=False, header=True)

# Global instance
review_system = HumanReviewSystem()
