"""
Database migration script to create School Admin Dashboard tables.
Run this after adding the new models.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base
from app.models import (
    Subject, Class, ClassStudent, StudentParent,
    Lesson, Lecture, TimetableSlot, Holiday, Event, Announcement
)

def migrate():
    """Create all new tables for School Admin Dashboard."""
    print("Creating School Admin Dashboard tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("[OK] All tables created successfully!")
        print("\nCreated tables:")
        print("  - subjects")
        print("  - classes")
        print("  - class_students")
        print("  - student_parents")
        print("  - lessons")
        print("  - lectures")
        print("  - timetable_slots")
        print("  - holidays")
        print("  - events")
        print("  - announcements")
        
    except Exception as e:
        print(f"[ERROR] Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    migrate()
