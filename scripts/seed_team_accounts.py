"""Script to seed/sync team accounts for ISO 27001 assessment team.
Ensures admin, Khoa, and Tú can all log in with matching UUIDs.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")

from backend.database import get_connection
from backend.teamwork import hash_password, DEMO_ASSESSMENT_ID

ACCOUNTS = [
    {
        "user_id": "0636c41b-8080-4c07-a1d9-4dc13d023c43",
        "username": "admin",
        "display_name": "Trần Văn Toàn (Admin)",
        "role": "admin",
        "password": "Admin@12345678",
    },
    {
        "user_id": "145f6315-7d77-4ae0-b30b-67deff6637a3",
        "username": "ledangkhoa",
        "display_name": "Lê Đăng Khoa",
        "role": "assessor",
        "password": "Khoa@12345678",
    },
    {
        "user_id": "c9ccb219-e097-49e7-b746-0ad63a8c0e36",
        "username": "vantu",
        "display_name": "Lê Đoàn Văn Tú",
        "role": "assessor",
        "password": "VanTu@12345678",
    },
]

def seed():
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM team_sessions")
            cur.execute("DELETE FROM login_attempts")
            for acc in ACCOUNTS:
                pw_hash = hash_password(acc["password"])
                cur.execute(
                    """
                    INSERT INTO team_users (user_id, username, password_hash, display_name, role)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE 
                    SET password_hash = EXCLUDED.password_hash,
                        display_name = EXCLUDED.display_name,
                        role = EXCLUDED.role
                    RETURNING user_id
                    """,
                    (acc["user_id"], acc["username"], pw_hash, acc["display_name"], acc["role"])
                )
                actual_user_id = cur.fetchone()[0]
                cur.execute(
                    """
                    INSERT INTO assessment_members (assessment_id, user_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (DEMO_ASSESSMENT_ID, actual_user_id)
                )
            con.commit()
    print("Seed team accounts completed successfully:")
    for acc in ACCOUNTS:
        print(f" - [{acc['role'].upper()}] {acc['username']} ({acc['display_name']}) -> Password: {acc['password']}")

if __name__ == "__main__":
    seed()
