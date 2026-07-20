import json
from pathlib import Path
from typing import Any, Dict, List, Union, Optional

# Define allowed base directories
ALLOWED_DIRS = {
    Path(__file__).parent.parent.parent / "data",
    Path(__file__).parent.parent.parent / "logs",
    Path(__file__).parent.parent.parent / "feedback"
}

def validate_file_path(file_path: Union[str, Path]) -> Path:
    """Validate file path to prevent directory traversal attacks"""
    path = Path(file_path).resolve()
    
    # Check if path is within allowed directories
    for allowed_dir in ALLOWED_DIRS:
        try:
            path.relative_to(allowed_dir.resolve())
            return path
        except ValueError:
            continue
    
    raise ValueError(f"Access denied: Path {path} is not in allowed directories")

def load_json(file_path: Union[str, Path], default: Optional[Any] = None) -> Union[Dict[str, Any], List[Any]]:
    """Load JSON file with path validation and error handling"""
    from app.utils.error_recovery import ErrorRecovery
    
    def _load_operation():
        validated_path = validate_file_path(file_path)
        
        if not validated_path.exists():
            return default or []
        
        with open(validated_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    try:
        return ErrorRecovery.safe_file_operation(
            _load_operation, 
            str(file_path), 
            fallback_data=default or []
        )
    except ValueError as e:
        print(f"Path validation error: {e}")
        return default or []
    except Exception as e:
        ErrorRecovery.log_error(e, f"Loading JSON from {file_path}")
        return default or []

def save_json(file_path: Union[str, Path], data: Union[Dict[str, Any], List[Any]]) -> bool:
    """Save JSON file with path validation and error handling"""
    from app.utils.error_recovery import ErrorRecovery
    
    def _save_operation():
        validated_path = validate_file_path(file_path)
        
        # Create directory if it doesn't exist
        validated_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(validated_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    
    try:
        result = ErrorRecovery.safe_file_operation(
            _save_operation, 
            str(file_path), 
            fallback_data=data
        )
        return result is not None
    except ValueError as e:
        print(f"Path validation error: {e}")
        return False
    except Exception as e:
        ErrorRecovery.log_error(e, f"Saving JSON to {file_path}", {"data_type": type(data).__name__})
        return False