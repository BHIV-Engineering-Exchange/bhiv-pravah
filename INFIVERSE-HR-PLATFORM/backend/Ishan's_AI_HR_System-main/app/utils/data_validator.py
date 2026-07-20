import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

class DataValidator:
    """Validates and ensures all required data files exist"""
    
    REQUIRED_FILES = {
        "feedback/cvs.csv": "Candidate CVs data",
        "feedback/jds.csv": "Job descriptions data", 
        "feedback/feedbacks.csv": "HR feedback data",
        "feedback/feedback_log.csv": "Feedback logging",
        "feedback/system_log.json": "System event logging",
        "data/candidates.json": "Candidate storage"
    }
    
    @classmethod
    def validate_data_files(cls) -> Dict[str, Any]:
        """Validate all required data files exist and are accessible"""
        results = {
            "status": "success",
            "missing_files": [],
            "created_files": [],
            "errors": []
        }
        
        for file_path, description in cls.REQUIRED_FILES.items():
            try:
                if not os.path.exists(file_path):
                    cls._create_missing_file(file_path, description)
                    results["created_files"].append(file_path)
                
                # Test file accessibility
                cls._test_file_access(file_path)
                
            except Exception as e:
                results["errors"].append(f"{file_path}: {str(e)}")
                results["status"] = "error"
        
        return results
    
    @classmethod
    def _create_missing_file(cls, file_path: str, description: str):
        """Create missing data file with default structure"""
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        if file_path.endswith('.csv'):
            cls._create_csv_file(file_path)
        elif file_path.endswith('.json'):
            cls._create_json_file(file_path)
    
    @classmethod
    def _create_csv_file(cls, file_path: str):
        """Create CSV file with appropriate headers"""
        headers = {
            "feedback/cvs.csv": ["id", "name", "email", "phone", "skills", "experience", "education", "location", "status"],
            "feedback/jds.csv": ["id", "title", "department", "location", "requirements", "description", "status", "created_date"],
            "feedback/feedbacks.csv": ["id", "candidate_id", "job_id", "feedback_score", "comment", "actual_outcome", "created_date", "hr_name"],
            "feedback/feedback_log.csv": ["timestamp", "candidate_id", "score", "comment", "outcome", "event"]
        }
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if file_path in headers:
                writer.writerow(headers[file_path])
    
    @classmethod
    def _create_json_file(cls, file_path: str):
        """Create JSON file with default structure"""
        default_data = {
            "feedback/system_log.json": [],
            "data/candidates.json": []
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_data.get(file_path, {}), f, indent=2)
    
    @classmethod
    def _test_file_access(cls, file_path: str):
        """Test if file can be read and written"""
        # Test read access
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1)  # Read first character
        
        # Test write access
        with open(file_path, 'a', encoding='utf-8') as f:
            pass  # Just open for append to test write access
    
    @classmethod
    def get_system_status(cls) -> Dict[str, Any]:
        """Get comprehensive system status"""
        validation_result = cls.validate_data_files()
        
        status = {
            "data_files": validation_result,
            "directories": {
                "feedback": os.path.exists("feedback"),
                "data": os.path.exists("data"),
                "app": os.path.exists("app")
            },
            "permissions": cls._check_permissions()
        }
        
        return status
    
    @classmethod
    def _check_permissions(cls) -> Dict[str, bool]:
        """Check file system permissions"""
        permissions = {}
        
        for file_path in cls.REQUIRED_FILES.keys():
            try:
                # Check if we can write to the directory
                directory = os.path.dirname(file_path)
                test_file = os.path.join(directory, '.permission_test')
                
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                
                permissions[directory] = True
            except:
                permissions[directory] = False
        
        return permissions

def ensure_data_integrity():
    """Convenience function to ensure all data files are ready"""
    validator = DataValidator()
    result = validator.validate_data_files()
    
    if result["status"] == "error":
        raise RuntimeError(f"Data validation failed: {result['errors']}")
    
    return result