import os
import shutil
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import threading
import schedule
import time

logger = logging.getLogger(__name__)

class BackupManager:
    """Automated backup system for data files and database"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_retention_days = 30
        self.auto_backup_enabled = False
        self._backup_thread = None
        
    def create_full_backup(self) -> str:
        """Create a complete system backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"full_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Backup data directory
            data_dir = Path("data")
            if data_dir.exists():
                shutil.copytree(data_dir, backup_path / "data", dirs_exist_ok=True)
            
            # Backup feedback directory
            feedback_dir = Path("feedback")
            if feedback_dir.exists():
                shutil.copytree(feedback_dir, backup_path / "feedback", dirs_exist_ok=True)
            
            # Backup logs directory
            logs_dir = Path("logs")
            if logs_dir.exists():
                shutil.copytree(logs_dir, backup_path / "logs", dirs_exist_ok=True)
            
            # Create backup manifest
            manifest = {
                "backup_type": "full",
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "files_backed_up": self._get_file_list(backup_path),
                "backup_size_bytes": self._get_directory_size(backup_path)
            }
            
            with open(backup_path / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Full backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            # Clean up partial backup
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise
    
    def create_incremental_backup(self, last_backup_time: datetime = None) -> str:
        """Create incremental backup of changed files"""
        if not last_backup_time:
            last_backup_time = datetime.now() - timedelta(hours=24)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"incremental_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        changed_files = []
        
        try:
            # Check for changed files
            for directory in ["data", "feedback", "logs"]:
                dir_path = Path(directory)
                if not dir_path.exists():
                    continue
                
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime > last_backup_time:
                            # Copy changed file
                            relative_path = file_path.relative_to(".")
                            dest_path = backup_path / relative_path
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(file_path, dest_path)
                            changed_files.append(str(relative_path))
            
            # Create backup manifest
            manifest = {
                "backup_type": "incremental",
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "since": last_backup_time.isoformat(),
                "changed_files": changed_files,
                "backup_size_bytes": self._get_directory_size(backup_path)
            }
            
            with open(backup_path / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Incremental backup created: {backup_path} ({len(changed_files)} files)")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Incremental backup failed: {e}")
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise
    
    def restore_backup(self, backup_path: str, target_dir: str = ".") -> bool:
        """Restore from backup"""
        backup_path = Path(backup_path)
        target_dir = Path(target_dir)
        
        if not backup_path.exists():
            logger.error(f"Backup path does not exist: {backup_path}")
            return False
        
        try:
            # Read manifest
            manifest_path = backup_path / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
                logger.info(f"Restoring {manifest['backup_type']} backup from {manifest['created_at']}")
            
            # Restore directories
            for item in backup_path.iterdir():
                if item.is_dir() and item.name in ["data", "feedback", "logs"]:
                    dest_path = target_dir / item.name
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(item, dest_path)
                    logger.info(f"Restored directory: {item.name}")
            
            logger.info(f"Backup restored successfully from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Remove old backup files"""
        cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
        
        removed_count = 0
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                try:
                    # Extract timestamp from directory name
                    timestamp_str = backup_dir.name.split('_')[-2] + '_' + backup_dir.name.split('_')[-1]
                    backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if backup_date < cutoff_date:
                        shutil.rmtree(backup_dir)
                        removed_count += 1
                        logger.info(f"Removed old backup: {backup_dir.name}")
                        
                except (ValueError, IndexError):
                    # Skip directories that don't match expected format
                    continue
        
        logger.info(f"Cleanup completed: {removed_count} old backups removed")
        return removed_count
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get list of available backups"""
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                manifest_path = backup_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path) as f:
                            manifest = json.load(f)
                        
                        backups.append({
                            "name": backup_dir.name,
                            "path": str(backup_dir),
                            "type": manifest.get("backup_type", "unknown"),
                            "created_at": manifest.get("created_at"),
                            "size_bytes": manifest.get("backup_size_bytes", 0),
                            "file_count": len(manifest.get("files_backed_up", []))
                        })
                    except Exception as e:
                        logger.warning(f"Could not read manifest for {backup_dir.name}: {e}")
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups
    
    def start_auto_backup(self, interval_hours: int = 24):
        """Start automated backup process"""
        if self.auto_backup_enabled:
            logger.warning("Auto backup is already running")
            return
        
        self.auto_backup_enabled = True
        
        # Schedule backups
        schedule.every(interval_hours).hours.do(self._scheduled_backup)
        schedule.every().day.at("02:00").do(self.cleanup_old_backups)
        
        # Start background thread
        self._backup_thread = threading.Thread(target=self._backup_scheduler, daemon=True)
        self._backup_thread.start()
        
        logger.info(f"Auto backup started (interval: {interval_hours} hours)")
    
    def stop_auto_backup(self):
        """Stop automated backup process"""
        self.auto_backup_enabled = False
        schedule.clear()
        logger.info("Auto backup stopped")
    
    def _scheduled_backup(self):
        """Perform scheduled backup"""
        try:
            # Get last backup time
            backups = self.get_backup_list()
            if backups:
                last_backup = datetime.fromisoformat(backups[0]["created_at"])
                # Create incremental backup if last backup was recent
                if datetime.now() - last_backup < timedelta(days=7):
                    self.create_incremental_backup(last_backup)
                else:
                    self.create_full_backup()
            else:
                self.create_full_backup()
                
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
    
    def _backup_scheduler(self):
        """Background thread for running scheduled backups"""
        while self.auto_backup_enabled:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _get_file_list(self, directory: Path) -> List[str]:
        """Get list of files in directory"""
        files = []
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                files.append(str(file_path.relative_to(directory)))
        return files
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory"""
        total_size = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    def export_data_csv(self, output_dir: str = "exports") -> Dict[str, str]:
        """Export all data to CSV files"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exported_files = {}
        
        try:
            # Export candidates
            from app.utils.database import db_manager
            
            candidates = db_manager.get_all_candidates(active_only=False)
            if candidates:
                candidates_file = output_dir / f"candidates_export_{timestamp}.csv"
                with open(candidates_file, 'w', newline='', encoding='utf-8') as f:
                    if candidates:
                        writer = csv.DictWriter(f, fieldnames=candidates[0].keys())
                        writer.writeheader()
                        writer.writerows(candidates)
                exported_files['candidates'] = str(candidates_file)
            
            # Export feedback
            feedback_data = []
            for candidate in candidates:
                feedback_list = db_manager.get_feedback_by_candidate(candidate['id'])
                feedback_data.extend(feedback_list)
            
            if feedback_data:
                feedback_file = output_dir / f"feedback_export_{timestamp}.csv"
                with open(feedback_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=feedback_data[0].keys())
                    writer.writeheader()
                    writer.writerows(feedback_data)
                exported_files['feedback'] = str(feedback_file)
            
            logger.info(f"Data exported to CSV files: {exported_files}")
            return exported_files
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            raise

# Global backup manager instance
backup_manager = BackupManager()