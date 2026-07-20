
import uuid
import bcrypt
from sqlalchemy import create_engine, text
import sys

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def create_super_admin(db_url, email, password, name):
    try:
        engine = create_engine(db_url)
        hashed_pwd = hash_password(password)
        user_id = str(uuid.uuid4())
        
        with engine.connect() as conn:
            # Check if user exists
            result = conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email}).fetchone()
            
            if result:
                print(f"User {email} exists. Updating to Super Admin...")
                conn.execute(
                    text("UPDATE users SET role = 'ADMIN', tenant_id = NULL, hashed_password = :pwd, full_name = :name WHERE email = :email"),
                    {"pwd": hashed_pwd, "name": name, "email": email}
                )
            else:
                print(f"Creating new Super Admin {email}...")
                conn.execute(
                    text("INSERT INTO users (id, email, hashed_password, role, tenant_id, is_active, full_name) VALUES (:id, :email, :pwd, 'ADMIN', NULL, TRUE, :name)"),
                    {"id": user_id, "email": email, "pwd": hashed_pwd, "name": name}
                )
            conn.commit()
            print(f"SUCCESS: Super Admin {email} is ready.")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python standalone_admin.py <db_url> <email> <password> <name>")
        sys.exit(1)
    
    create_super_admin(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
