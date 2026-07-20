import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User, UserRole, School, Subject, Class
from app.auth import get_password_hash

def seed_ems_demo():
    print("--- Seeding EMS Demo Data ---")
    db = SessionLocal()
    try:
        # 1. Create Demo School
        school_name = "Gurukul Demo Academy"
        demo_school = db.query(School).filter(School.name == school_name).first()
        if not demo_school:
            demo_school = School(
                name=school_name,
                address="123 Demo Street, Blackhole Infiverse",
                phone="555-DEMO",
                email="demo@gurukul.com"
            )
            db.add(demo_school)
            db.commit()
            db.refresh(demo_school)
            print(f"Created Demo School: {demo_school.name} (ID: {demo_school.id})")
        else:
            print(f"Demo School already exists: {demo_school.name} (ID: {demo_school.id})")

        # 2. Create Demo Users
        password_hash = get_password_hash("demo123")
        
        users_to_create = [
            {"email": "admin@demo.com", "role": UserRole.ADMIN, "name": "Demo Admin"},
            {"email": "teacher@demo.com", "role": UserRole.TEACHER, "name": "Demo Teacher", "subject": "Science"},
            {"email": "parent@demo.com", "role": UserRole.PARENT, "name": "Demo Parent"},
            {"email": "student@demo.com", "role": UserRole.STUDENT, "name": "Demo Student", "grade": "10"}
        ]
        
        for u in users_to_create:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                new_user = User(
                    email=u["email"],
                    password=password_hash,
                    name=u["name"],
                    role=u["role"],
                    school_id=demo_school.id,
                    is_active=True,
                    subject=u.get("subject"),
                    grade=u.get("grade")
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                print(f"Created EMS User: {u['email']} (Role: {u['role']})")
            else:
                existing.password = password_hash
                existing.school_id = demo_school.id
                existing.role = u["role"]
                db.commit()
                print(f"Updated EMS User: {u['email']}")

        # 3. Create Subject & Class for the Teacher
        teacher = db.query(User).filter(User.email == "teacher@demo.com").first()
        if teacher:
            # Subject
            subject_name = "Science"
            demo_subject = db.query(Subject).filter(Subject.name == subject_name, Subject.school_id == demo_school.id).first()
            if not demo_subject:
                demo_subject = Subject(name=subject_name, code="SCI101", school_id=demo_school.id)
                db.add(demo_subject)
                db.commit()
                db.refresh(demo_subject)
                print(f"Created Subject: {demo_subject.name}")

            # Class
            class_name = "Grade 10-A (Demo)"
            demo_class = db.query(Class).filter(Class.name == class_name, Class.school_id == demo_school.id).first()
            if not demo_class:
                demo_class = Class(
                    name=class_name,
                    grade="10",
                    subject_id=demo_subject.id,
                    teacher_id=teacher.id,
                    school_id=demo_school.id,
                    academic_year="2024-2025"
                )
                db.add(demo_class)
                db.commit()
                print(f"Created Class: {demo_class.name} assigned to {teacher.name}")

        print("--- EMS Demo Seeding Complete ---")
        
    except Exception as e:
        db.rollback()
        print(f"EMS SEED ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_ems_demo()
