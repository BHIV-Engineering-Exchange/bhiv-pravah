import os
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tools.database_sync_manager import DatabaseSyncManager

class ResumeWatcher(FileSystemEventHandler):
    def __init__(self):
        self.sync_manager = DatabaseSyncManager()
        self.supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        
    def on_created(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.supported_extensions:
                print(f"New resume detected: {file_path.name}")
                time.sleep(2)  # Wait for file to be fully written
                self.sync_manager.sync_new_resumes()
    
    def on_deleted(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.supported_extensions:
                print(f"Resume deleted: {file_path.name}")
                self.sync_manager.clean_database()
                self.sync_manager.clean_csv()

def start_auto_sync():
    """Start automatic resume folder monitoring"""
    resume_folder = "resume"
    
    if not os.path.exists(resume_folder):
        print(f"Resume folder not found: {resume_folder}")
        return
    
    print("Starting Auto-Sync Watcher...")
    print(f"Monitoring: {os.path.abspath(resume_folder)}")
    print("Auto-sync will trigger when resumes are added/removed")
    print("Press Ctrl+C to stop")
    
    event_handler = ResumeWatcher()
    observer = Observer()
    observer.schedule(event_handler, resume_folder, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nAuto-sync watcher stopped")
    
    observer.join()

if __name__ == "__main__":
    start_auto_sync()
