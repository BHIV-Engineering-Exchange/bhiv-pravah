"""Bootstrap script to assign system_admin role to testuser"""
import sys
import os

# Add runtime-core (parent directory) to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from role_enforcement.rbac_service import sar_rbac

# Assign system_admin role to testuser
try:
    assignment = sar_rbac.assign_role(
        user_id="testuser",
        role_name="system_admin",
        tenant_id=None,  # System role
        assigned_by="bootstrap_script"
    )
    print(f"✓ Successfully assigned system_admin role to testuser")
    print(f"  Assignment ID: {assignment.user_id}_{assignment.role.name}")
    print(f"  Assigned at: {assignment.assigned_at}")
    
    # Verify
    roles = sar_rbac.get_user_roles("testuser", None)
    print(f"\n✓ User testuser now has {len(roles)} role(s):")
    for r in roles:
        print(f"  - {r.role.name} ({r.role.role_type.value})")
        
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
