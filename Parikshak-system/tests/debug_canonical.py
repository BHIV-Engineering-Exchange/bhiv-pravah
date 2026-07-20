#!/usr/bin/env python3
"""
Debug Test - Trace the canonical intelligence engine execution
"""
import requests
import json

def debug_assignment_engine():
    """Debug the canonical intelligence engine"""
    base_url = "http://localhost:8000"
    
    print("DEBUG: CANONICAL INTELLIGENCE ENGINE")
    print("=" * 50)
    
    # Test with detailed logging
    test_data = {
        "task_title": "Simple Test Task",
        "task_description": "A basic test task to debug the scoring system",
        "submitted_by": "DebugUser",
        "github_repo_link": "",  # No repo to simplify
        "module_id": "task-review-agent",
        "schema_version": "v1.0"
    }
    
    print("Submitting test task...")
    response = requests.post(f"{base_url}/api/v1/lifecycle/submit", data=test_data)
    
    if response.status_code == 200:
        result = response.json()
        submission_id = result["submission_id"]
        
        print(f"Submission ID: {submission_id}")
        print(f"API Score: {result['review_summary']['score']}")
        print(f"API Status: {result['review_summary']['status']}")
        
        # Get detailed review
        review_response = requests.get(f"{base_url}/api/v1/lifecycle/review/{submission_id}")
        
        if review_response.status_code == 200:
            review_data = review_response.json()
            
            print("\nDETAILED REVIEW DATA:")
            print(f"Overall Score: {review_data['score']}")
            print(f"Overall Status: {review_data['status']}")
            print(f"Title Score: {review_data.get('title_score', 'MISSING')}")
            print(f"Description Score: {review_data.get('description_score', 'MISSING')}")
            print(f"Repository Score: {review_data.get('repository_score', 'MISSING')}")
            
            # Check for canonical authority markers
            print(f"\nCANONICAL MARKERS:")
            print(f"Evaluation Summary: {review_data.get('evaluation_summary', 'MISSING')}")
            
            # Check supporting signals
            analysis = review_data.get('analysis', {})
            if analysis:
                print(f"\nANALYSIS DATA:")
                for key, value in analysis.items():
                    if isinstance(value, dict):
                        print(f"  {key}: {len(value)} items")
                    else:
                        print(f"  {key}: {value}")
            
            # Check for failure reasons
            failure_reasons = review_data.get('failure_reasons', [])
            if failure_reasons:
                print(f"\nFAILURE REASONS:")
                for reason in failure_reasons:
                    print(f"  - {reason}")
            
        else:
            print(f"Failed to get review: {review_response.status_code}")
    else:
        print(f"Submission failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    debug_assignment_engine()