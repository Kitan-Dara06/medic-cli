"""
Logging and metrics system for medic CLI
Tracks test results, fix rates, and usage patterns
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path


class MedicLogger:
    """Logs medic CLI operations and metrics"""
    
    def __init__(self, log_dir=None):
        """
        Initialize the logger
        
        Args:
            log_dir: Directory to store logs (default: ~/.medic/logs)
        """
        if log_dir is None:
            log_dir = Path.home() / ".medic" / "logs"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"medic_{datetime.now().strftime('%Y%m%d')}.json"
        
    def log_event(self, event_type, data):
        """
        Log an event
        
        Args:
            event_type: Type of event (crash_detected, fix_applied, etc.)
            data: Event data dictionary
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        # Append to daily log file
        events = []
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                try:
                    events = json.load(f)
                except json.JSONDecodeError:
                    events = []
        
        events.append(event)
        
        with open(self.log_file, 'w') as f:
            json.dump(events, f, indent=2)
    
    def log_crash(self, file_path, line_num, error_type, error_message):
        """Log a crash detection"""
        self.log_event("crash_detected", {
            "file": file_path,
            "line": line_num,
            "error_type": error_type,
            "error_message": error_message
        })
    
    def log_fix_generated(self, file_path, old_code, new_code):
        """Log when a fix is generated"""
        self.log_event("fix_generated", {
            "file": file_path,
            "old_code": old_code,
            "new_code": new_code
        })
    
    def log_fix_applied(self, file_path, success):
        """Log when a fix is applied"""
        self.log_event("fix_applied", {
            "file": file_path,
            "success": success
        })
    
    def log_fix_rejected(self, file_path):
        """Log when a fix is rejected by user"""
        self.log_event("fix_rejected", {
            "file": file_path
        })
    
    def get_stats(self, days=7):
        """
        Get statistics for the last N days
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_crashes": 0,
            "fixes_generated": 0,
            "fixes_applied": 0,
            "fixes_rejected": 0,
            "error_types": {},
            "success_rate": 0.0
        }
        
        # Read logs from the last N days
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            log_file = self.log_dir / f"medic_{date.strftime('%Y%m%d')}.json"
            
            if not log_file.exists():
                continue
            
            with open(log_file, 'r') as f:
                try:
                    events = json.load(f)
                except json.JSONDecodeError:
                    continue
            
            for event in events:
                event_type = event.get("event_type")
                data = event.get("data", {})
                
                if event_type == "crash_detected":
                    stats["total_crashes"] += 1
                    error_type = data.get("error_type", "Unknown")
                    stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1
                
                elif event_type == "fix_generated":
                    stats["fixes_generated"] += 1
                
                elif event_type == "fix_applied":
                    if data.get("success"):
                        stats["fixes_applied"] += 1
                
                elif event_type == "fix_rejected":
                    stats["fixes_rejected"] += 1
        
        # Calculate success rate
        total_responses = stats["fixes_applied"] + stats["fixes_rejected"]
        if total_responses > 0:
            stats["success_rate"] = stats["fixes_applied"] / total_responses * 100
        
        return stats


# Global logger instance (optional, can be disabled)
_global_logger = None

def get_logger(enabled=True):
    """Get or create the global logger instance"""
    global _global_logger
    if enabled and _global_logger is None:
        _global_logger = MedicLogger()
    return _global_logger
