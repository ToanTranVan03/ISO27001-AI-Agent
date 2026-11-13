"""Create one assessor account, preserving existing accounts and passwords."""
import argparse
from getpass import getpass
from pathlib import Path
import sys
from uuid import uuid4

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")

from backend.database import get_connection
from backend.teamwork import DEMO_ASSESSMENT_ID, hash_password

ACCOUNTS = {
    "tu": ("vantu", "Lê Đoàn Văn Tú"),
    "khoa": ("ledangkhoa", "Lê Đăng Khoa"),
}


def seed(user_key="tu"):
    username, display_name = ACCOUNTS[user_key]
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("SELECT user_id, role FROM team_users WHERE username=%s", (username,))
            existing = cur.fetchone()
            if existing:
                user_id, role = existing
                if role != "assessor":
                    raise ValueError("Tài khoản hiện có không phải assessor; cần người quản trị kiểm tra.")
                print(f"Giữ nguyên tài khoản và mật khẩu hiện có: {username}.")
            else:
                password = getpass(f"Mật khẩu mới cho {username} (ít nhất 12 ký tự): ")
                if len(password) < 12 or password != getpass("Nhập lại mật khẩu: "):
                    raise ValueError("Mật khẩu phải khớp và có ít nhất 12 ký tự.")
                user_id = str(uuid4())
                cur.execute(
                    """INSERT INTO team_users (user_id, username, password_hash, display_name, role)
                       VALUES (%s, %s, %s, %s, 'assessor')""",
                    (user_id, username, hash_password(password), display_name),
                )
                print(f"Đã tạo tài khoản assessor: {username} ({display_name}).")
            cur.execute(
                """INSERT INTO assessment_members (assessment_id, user_id)
                   VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                (DEMO_ASSESSMENT_ID, user_id),
            )
    print(f"Đã gắn {username} vào đợt đánh giá. Không thay đổi tài khoản khác.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", choices=ACCOUNTS, default="tu")
    args = parser.parse_args()
    try:
        seed(args.user)
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, f"Không hoàn tất: {exc}\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    main()
