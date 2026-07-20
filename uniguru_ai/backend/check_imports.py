import sys
import os

print("Current Working Directory:", os.getcwd())
print("Files in CWD:", os.listdir())
try:
    import services
    print("Successfully imported services")
    import services.validation_service
    print("Successfully imported services.validation_service")
except ImportError as e:
    print("Failed to import:", e)
