import pytest
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to ensure proper module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import Base, get_db
from app.routers.auth import get_current_user
from app.models.all_models import User, Tenant, Cohort, TeacherStudentAssignment, TestResult, Reflection
from app.models.dashboard_models import DashboardAlert, DashboardAction, DashboardAuditLog
from app.routers.dashboard import router as dashboard_router
from app.main import app as main_app

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh temporary SQLite database for each test to ensure isolation."""
    temp_dir = Path(__file__).resolve().parent / ".tmp"
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / "test_dashboard_temp.db"
    db_path.unlink(missing_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path}", 
        connect_args={"check_same_thread": False}
    )
    
    # Create all registered tables in the DB
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    # Seed basic records needed for testing
    # Tenants
    t1 = Tenant(id="tenant-1", name="Institution A", type="INSTITUTION")
    t2 = Tenant(id="tenant-2", name="Institution B", type="INSTITUTION")
    session.add_all([t1, t2])
    session.commit()

    # Cohorts
    c1 = Cohort(id="cohort-1", name="Grade 10-A", tenant_id="tenant-1")
    c2 = Cohort(id="cohort-2", name="Grade 10-B", tenant_id="tenant-1")
    c3 = Cohort(id="cohort-3", name="Grade 9-A", tenant_id="tenant-2")
    session.add_all([c1, c2, c3])
    session.commit()

    # Users (Student, Teacher, Institution Admin, Regional Admin)
    u_student1 = User(id="student-1", email="student1@test.gurukul", role="STUDENT", tenant_id="tenant-1", cohort_id="cohort-1")
    u_student2 = User(id="student-2", email="student2@test.gurukul", role="STUDENT", tenant_id="tenant-1", cohort_id="cohort-2")
    u_student3 = User(id="student-3", email="student3@test.gurukul", role="STUDENT", tenant_id="tenant-2", cohort_id="cohort-3")
    
    u_teacher1 = User(id="teacher-1", email="teacher1@test.gurukul", role="TEACHER", tenant_id="tenant-1")
    u_teacher2 = User(id="teacher-2", email="teacher2@test.gurukul", role="TEACHER", tenant_id="tenant-2")
    
    u_inst_admin = User(id="inst-admin", email="inst_admin@test.gurukul", role="INSTITUTION_ADMIN", tenant_id="tenant-1")
    u_reg_admin = User(id="reg-admin", email="reg_admin@test.gurukul", role="REGIONAL_ADMIN")
    u_admin = User(id="admin", email="admin@test.gurukul", role="ADMIN")
    
    session.add_all([u_student1, u_student2, u_student3, u_teacher1, u_teacher2, u_inst_admin, u_reg_admin, u_admin])
    session.commit()

    # Assignments (Teacher 1 is assigned to Student 1 & 2)
    asg1 = TeacherStudentAssignment(id="asg-1", teacher_id="teacher-1", student_id="student-1", cohort_id="cohort-1", subject="Science")
    asg2 = TeacherStudentAssignment(id="asg-2", teacher_id="teacher-1", student_id="student-2", cohort_id="cohort-2", subject="Mathematics")
    session.add_all([asg1, asg2])
    session.commit()
    
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        db_path.unlink(missing_ok=True)

# Helper to override authentication in testing client
def get_auth_client(db_session, current_user_id: str):
    app = FastAPI()
    
    # Override database session dependency
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Override current user dependency
    test_user = db_session.query(User).filter(User.id == current_user_id).first()
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    app.include_router(dashboard_router, prefix="/api/v1")
    return TestClient(app)

class TestDashboardFoundation:
    """Test Suite for Dashboard, Alerts, Actions, and Audit Trail APIs"""

    def test_health_check(self):
        """Test public system health endpoint"""
        client = TestClient(main_app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "system_state" in data

    def test_rbac_boundaries_student_dashboard(self, db_session):
        """Students can view their own dashboard but cannot view teacher/admin dashboards"""
        client_student = get_auth_client(db_session, "student-1")
        
        # Access own student dashboard -> 200 OK
        resp = client_student.get("/api/v1/dashboard/student")
        assert resp.status_code == 200
        assert resp.json()["role"] == "student"
        
        # Access other student's dashboard -> 403 Forbidden
        resp = client_student.get("/api/v1/dashboard/student", params={"student_id": "student-2"})
        assert resp.status_code == 403

        # Access teacher dashboard -> 403 Forbidden
        resp = client_student.get("/api/v1/dashboard/teacher")
        assert resp.status_code == 403

    def test_rbac_boundaries_teacher_dashboard(self, db_session):
        """Teachers can view teacher dashboard, and only their students' dashboards"""
        client_teacher = get_auth_client(db_session, "teacher-1")
        
        # Access own teacher dashboard -> 200 OK
        resp = client_teacher.get("/api/v1/dashboard/teacher")
        assert resp.status_code == 200
        assert resp.json()["role"] == "teacher"
        assert resp.json()["kpis"]["total_assigned_students"] == 2
        
        # Access assigned student's dashboard -> 200 OK
        resp = client_teacher.get("/api/v1/dashboard/student", params={"student_id": "student-1"})
        assert resp.status_code == 200

        # Access unassigned student's dashboard -> 403 Forbidden (student-3 is in tenant-2)
        resp = client_teacher.get("/api/v1/dashboard/student", params={"student_id": "student-3"})
        assert resp.status_code == 403

    def test_alert_engine_lifecycle_and_audit(self, db_session):
        """Create, assign, status change and resolve alert flows, checking audit logging"""
        # 1. Create Alert (as teacher-1)
        client = get_auth_client(db_session, "teacher-1")
        payload = {
            "type": "COMPREHENSION",
            "priority": "HIGH",
            "owner_id": "student-1"
        }
        resp = client.post("/api/v1/alerts", json=payload)
        assert resp.status_code == 201
        alert_id = resp.json()["id"]
        assert resp.json()["status"] == "OPEN"

        # Check Audit Log created
        audit_logs = db_session.query(DashboardAuditLog).filter(DashboardAuditLog.entity_id == alert_id).all()
        assert len(audit_logs) == 1
        assert audit_logs[0].operation == "CREATE"
        assert audit_logs[0].status == "OPEN"

        # 2. Assign Alert to student-2 (unassigning student-1, teacher-1 can do this since student-2 is assigned)
        assign_payload = {"owner_id": "student-2"}
        resp = client.put(f"/api/v1/alerts/{alert_id}/assign", json=assign_payload)
        assert resp.status_code == 200
        assert resp.json()["owner_id"] == "student-2"

        # Check Assign Audit Log
        audit_logs = db_session.query(DashboardAuditLog).filter(DashboardAuditLog.entity_id == alert_id).all()
        assert len(audit_logs) == 2
        operations = {log.operation for log in audit_logs}
        assert "CREATE" in operations
        assert "ASSIGN" in operations

        # 3. Student-2 Resolves alert -> 200 OK
        client_student = get_auth_client(db_session, "student-2")
        status_payload = {"status": "RESOLVED"}
        resp = client_student.put(f"/api/v1/alerts/{alert_id}/status", json=status_payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "RESOLVED"

        # Check Resolve Audit Log
        audit_logs = db_session.query(DashboardAuditLog).filter(DashboardAuditLog.entity_id == alert_id).all()
        assert len(audit_logs) == 3
        operations = {log.operation for log in audit_logs}
        assert "CREATE" in operations
        assert "ASSIGN" in operations
        assert "UPDATE_STATUS" in operations

        # 4. Student tries to Close alert -> 403 Forbidden
        status_payload = {"status": "CLOSED"}
        resp = client_student.put(f"/api/v1/alerts/{alert_id}/status", json=status_payload)
        assert resp.status_code == 403

        # 5. Teacher closes alert -> 200 OK
        resp = client.put(f"/api/v1/alerts/{alert_id}/status", json=status_payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "CLOSED"

    def test_action_engine_lifecycle(self, db_session):
        """Verify lifecycle states of actions: Created -> Assigned -> In Progress -> Completed"""
        client = get_auth_client(db_session, "teacher-1")
        
        # 1. Create Action
        payload = {
            "title": "Remedial review on Fractions",
            "description": "Student needs help with standard subject topic."
        }
        resp = client.post("/api/v1/actions", json=payload)
        assert resp.status_code == 201
        action_id = resp.json()["id"]
        assert resp.json()["status"] == "Created"

        # 2. Assign Action
        assign_payload = {"owner_id": "student-1"}
        resp = client.put(f"/api/v1/actions/{action_id}/assign", json=assign_payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "Assigned"
        assert resp.json()["owner_id"] == "student-1"

        # 3. Transition to In Progress (as Student-1)
        client_student = get_auth_client(db_session, "student-1")
        status_payload = {"status": "In Progress"}
        resp = client_student.put(f"/api/v1/actions/{action_id}/status", json=status_payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "In Progress"

        # 4. Try to set invalid status value -> 400 Bad Request
        status_payload = {"status": "InvalidStatus"}
        resp = client_student.put(f"/api/v1/actions/{action_id}/status", json=status_payload)
        assert resp.status_code == 400

    def test_audit_logs_queryable_access(self, db_session):
        """Verify that only authorized roles can query audit logs, and students are rejected"""
        # Create an alert to generate some audit logs
        client_teacher = get_auth_client(db_session, "teacher-1")
        client_teacher.post("/api/v1/alerts", json={"type": "PACING", "priority": "MEDIUM", "owner_id": "student-1"})

        # Student queries audit logs -> 403 Forbidden
        client_student = get_auth_client(db_session, "student-1")
        resp = client_student.get("/api/v1/audit-logs")
        assert resp.status_code == 403

        # Teacher queries audit logs -> 200 OK
        resp = client_teacher.get("/api/v1/audit-logs")
        assert resp.status_code == 200
        assert len(resp.json()) > 0
        assert resp.json()[0]["entity"] == "ALERT"
        assert resp.json()[0]["operation"] == "CREATE"
