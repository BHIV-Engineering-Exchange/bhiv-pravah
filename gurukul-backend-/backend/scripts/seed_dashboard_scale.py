import sys
import os
import uuid
import random
import time
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal, engine, Base
from app.routers.auth import get_password_hash
from app.models.all_models import User, Tenant, Cohort, TeacherStudentAssignment, TestResult, Reflection
from app.models.dashboard_models import DashboardAlert, DashboardAction, DashboardAuditLog

def generate_uuid():
    return str(uuid.uuid4())

def seed():
    print("=" * 60)
    print("GURUKUL SCALE SIMULATION SEED ENGINE")
    print("Target Database: SQLite (gurukul.db)")
    print("=" * 60)
    
    # Ensure tables are created first
    print("Ensuring database tables are created...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # 1. Clean existing seed data
    print("Cleaning existing seed data...")
    db.query(DashboardAuditLog).delete()
    db.query(DashboardAction).delete()
    db.query(DashboardAlert).delete()
    db.query(TeacherStudentAssignment).delete()
    db.query(TestResult).delete()
    db.query(Reflection).delete()
    db.query(User).filter(User.email.like("%@test.gurukul")).delete()
    db.query(Cohort).filter(Cohort.name.like("Grade %")).delete()
    db.query(Tenant).filter(Tenant.name.like("Institution %")).delete()
    db.commit()
    print("Clean complete.")

    # 2. Pre-compute password hash (critical for speed!)
    start_time = time.time()
    print("Pre-computing password hash for seeded users...")
    hashed_pwd = get_password_hash("GurukulTest@123")
    print(f"Hash computed in {time.time() - start_time:.2f} seconds.")

    # 3. Create 20 Tenants (Institutions)
    print("Generating 20 Tenants...")
    tenants = []
    for i in range(1, 21):
        tenants.append({
            "id": generate_uuid(),
            "name": f"Institution {i}",
            "type": "INSTITUTION",
            "created_at": datetime.now(timezone.utc)
        })
    db.bulk_insert_mappings(Tenant, tenants)
    db.commit()
    print(f"Seeded {len(tenants)} tenants.")

    # 4. Create 100 Cohorts (5 per Tenant)
    print("Generating 100 Cohorts...")
    cohorts = []
    cohort_names = ["Grade 10-A", "Grade 10-B", "Grade 9-A", "Grade 9-B", "Grade 8-A"]
    for tenant in tenants:
        for name in cohort_names:
            cohorts.append({
                "id": generate_uuid(),
                "name": name,
                "tenant_id": tenant["id"],
                "created_at": datetime.now(timezone.utc)
            })
    db.bulk_insert_mappings(Cohort, cohorts)
    db.commit()
    print(f"Seeded {len(cohorts)} cohorts.")

    # 5. Create 200 Teachers (10 per Tenant)
    print("Generating 200 Teachers...")
    teachers = []
    for i, tenant in enumerate(tenants):
        for j in range(1, 11):
            teacher_idx = i * 10 + j
            teachers.append({
                "id": generate_uuid(),
                "email": f"teacher_{teacher_idx}@test.gurukul",
                "hashed_password": hashed_pwd,
                "full_name": f"Teacher {teacher_idx}",
                "role": "TEACHER",
                "tenant_id": tenant["id"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc)
            })
    db.bulk_insert_mappings(User, teachers)
    db.commit()
    print(f"Seeded {len(teachers)} teachers.")

    # 5.5 Create default Admin user
    print("Generating default admin user...")
    admin_user = User(
        id=generate_uuid(),
        email="admin@test.gurukul",
        hashed_password=hashed_pwd,
        full_name="System Admin",
        role="ADMIN",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(admin_user)
    db.commit()
    print("Seeded default admin user: admin@test.gurukul")

    # 6. Create 5000 Students (~50 per Cohort, distributed among the 100 cohorts)
    print("Generating 5000 Students...")
    students = []
    student_counter = 1
    for cohort in cohorts:
        tenant_id = cohort["tenant_id"]
        for _ in range(50):
            students.append({
                "id": generate_uuid(),
                "email": f"student_{student_counter}@test.gurukul",
                "hashed_password": hashed_pwd,
                "full_name": f"Student {student_counter}",
                "role": "STUDENT",
                "tenant_id": tenant_id,
                "cohort_id": cohort["id"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc)
            })
            student_counter += 1
    db.bulk_insert_mappings(User, students)
    db.commit()
    print(f"Seeded {len(students)} students.")

    # 7. Create Teacher-Student Assignments
    print("Assigning teachers to students...")
    assignments = []
    # Map teacher list by tenant_id for fast lookup
    teachers_by_tenant = {}
    for t in teachers:
        teachers_by_tenant.setdefault(t["tenant_id"], []).append(t)

    for student in students:
        tenant_teachers = teachers_by_tenant.get(student["tenant_id"], [])
        if tenant_teachers:
            # Assign 2 random teachers to each student
            selected_teachers = random.sample(tenant_teachers, min(2, len(tenant_teachers)))
            for teacher in selected_teachers:
                assignments.append({
                    "id": generate_uuid(),
                    "teacher_id": teacher["id"],
                    "student_id": student["id"],
                    "cohort_id": student["cohort_id"],
                    "subject": random.choice(["Science", "Arabic", "Mathematics"]),
                    "created_at": datetime.now(timezone.utc)
                })
    db.bulk_insert_mappings(TeacherStudentAssignment, assignments)
    db.commit()
    print(f"Seeded {len(assignments)} teacher-student assignments.")

    # 8. Create Test Results (~3 per student = ~15000 test results)
    print("Generating 15,000 Test Results...")
    test_results = []
    subjects_and_topics = [
        ("Science", "Chemical Reactions"),
        ("Arabic", "Grammar Rules"),
        ("Mathematics", "Algebraic Expressions")
    ]
    for student in students:
        for subj, topic in subjects_and_topics:
            score = random.randint(5, 10)
            test_results.append({
                "id": generate_uuid(),
                "user_id": student["id"],
                "subject": subj,
                "topic": topic,
                "difficulty": "medium",
                "num_questions": 10,
                "questions": {},
                "user_answers": {},
                "score": score,
                "total_questions": 10,
                "percentage": float(score * 10.0),
                "created_at": datetime.now(timezone.utc)
            })
    db.bulk_insert_mappings(TestResult, test_results)
    db.commit()
    print(f"Seeded {len(test_results)} test results.")

    # 9. Create reflections (1 per student = 5000 reflections)
    print("Generating 5000 reflections...")
    reflections = []
    for student in students:
        reflections.append({
            "id": generate_uuid(),
            "user_id": student["id"],
            "content": f"Daily comprehension checkpoint reflection for student {student['full_name']}",
            "mood_score": random.randint(6, 10),
            "created_at": datetime.now(timezone.utc)
        })
    db.bulk_insert_mappings(Reflection, reflections)
    db.commit()
    print(f"Seeded {len(reflections)} student reflections.")

    # 10. Create 1000 Alerts
    print("Generating 1000 Alerts...")
    alerts = []
    alert_types = ["COMPREHENSION", "ATTENDANCE", "PACING"]
    priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    statuses = ["OPEN", "RESOLVED", "CLOSED"]
    
    # Pre-select creators (teachers)
    teacher_ids = [t["id"] for t in teachers]

    for _ in range(1000):
        student = random.choice(students)
        creator_id = random.choice(teacher_ids)
        alerts.append({
            "id": generate_uuid(),
            "type": random.choice(alert_types),
            "priority": random.choice(priorities),
            "owner_id": student["id"],
            "status": random.choice(statuses),
            "created_by": creator_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
    db.bulk_insert_mappings(DashboardAlert, alerts)
    db.commit()
    print(f"Seeded {len(alerts)} alerts.")

    # 11. Create 2000 Actions
    print("Generating 2000 Actions...")
    actions = []
    action_statuses = ["Created", "Assigned", "In Progress", "Completed", "Closed", "Cancelled"]
    for _ in range(2000):
        student = random.choice(students)
        creator_id = random.choice(teacher_ids)
        actions.append({
            "id": generate_uuid(),
            "title": f"Action plan: {random.choice(['Comprehension remedial review', 'Pacing acceleration adjustment', 'Attendance check-in'])}",
            "description": "Lifecycle tracked action for student operational foundation MVP.",
            "owner_id": student["id"],
            "status": random.choice(action_statuses),
            "created_by": creator_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
    db.bulk_insert_mappings(DashboardAction, actions)
    db.commit()
    print(f"Seeded {len(actions)} actions.")

    # 12. Create 3000 Audit Logs
    print("Generating 3000 Audit Logs...")
    audit_logs = []
    all_alert_ids = [a["id"] for a in alerts]
    all_action_ids = [ac["id"] for ac in actions]
    operations = ["CREATE", "ASSIGN", "UPDATE_STATUS"]
    
    for _ in range(3000):
        entity_type = random.choice(["ALERT", "ACTION"])
        entity_id = random.choice(all_alert_ids) if entity_type == "ALERT" else random.choice(all_action_ids)
        operator_id = random.choice(teacher_ids)
        status_val = random.choice(statuses) if entity_type == "ALERT" else random.choice(action_statuses)
        
        audit_logs.append({
            "id": generate_uuid(),
            "created_by": operator_id,
            "timestamp": datetime.now(timezone.utc),
            "entity": entity_type,
            "entity_id": entity_id,
            "operation": random.choice(operations),
            "status": status_val,
            "details": {"seeded": True}
        })
    db.bulk_insert_mappings(DashboardAuditLog, audit_logs)
    db.commit()
    print(f"Seeded {len(audit_logs)} audit logs.")

    db.close()
    print("=" * 60)
    print(f"SUCCESS: Seeding completed in {time.time() - start_time:.2f} seconds!")
    print("=" * 60)

if __name__ == "__main__":
    seed()
