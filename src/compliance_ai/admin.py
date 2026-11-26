from getpass import getpass
from os import getenv
from uuid import NAMESPACE_URL, UUID, uuid5

import psycopg
from dotenv import load_dotenv
from psycopg import sql
from sqlalchemy.engine import make_url

from compliance_ai.auth import PASSWORDS

DEMO_NAMESPACE = uuid5(NAMESPACE_URL, "compliance-ai/demo-identity/v1")
DEMO_ACCOUNTS = (
    ("abc-admin", "admin", None),
    ("abc-auditor", "auditor", None),
    ("abc-nv001", "employee", "NV001"),
    ("xy-admin", "admin", None),
)


def demo_id(name: str) -> UUID:
    return uuid5(DEMO_NAMESPACE, name)


def privileged_connection() -> psycopg.Connection[tuple]:
    load_dotenv()
    raw = getenv("MIGRATION_DATABASE_URL")
    if not raw or make_url(raw).drivername != "postgresql+psycopg":
        raise ValueError("Set MIGRATION_DATABASE_URL to a postgresql+psycopg URL")
    url = make_url(raw).set(drivername="postgresql")
    return psycopg.connect(url.render_as_string(hide_password=False), connect_timeout=3)


def configure_roles() -> None:
    load_dotenv()
    roles = {
        "compliance_app": getenv("APP_DB_PASSWORD", ""),
        "compliance_evaluator": getenv("EVALUATOR_DB_PASSWORD", ""),
    }
    if any(len(password) < 24 for password in roles.values()):
        raise ValueError("Set APP_DB_PASSWORD and EVALUATOR_DB_PASSWORD to random local values")
    if len(set(roles.values())) != len(roles):
        raise ValueError("Database roles require distinct passwords")
    with privileged_connection() as connection:
        for role, password in roles.items():
            existing = connection.execute(
                """
                SELECT rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls
                OR EXISTS (SELECT FROM pg_auth_members WHERE member = pg_roles.oid)
                FROM pg_roles WHERE rolname = %s
                """,
                (role,),
            ).fetchone()
            if existing is not None and existing[0]:
                raise ValueError(f"The existing PostgreSQL role {role} has elevated privileges")
            if existing is None:
                connection.execute(sql.SQL("CREATE ROLE {} NOINHERIT").format(sql.Identifier(role)))
            connection.execute(
                sql.SQL("ALTER ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )


def seed_demo_identities() -> None:
    load_dotenv()
    if getenv("EXECUTION_MODE", "SIMULATION") != "SIMULATION":
        raise ValueError("Demo identities require SIMULATION")
    password = getpass("Mật khẩu cục bộ cho tài khoản mô phỏng ban đầu (tối thiểu 12 ký tự) > ")
    if len(password) < 12:
        raise ValueError("Mật khẩu cần tối thiểu 12 ký tự.")
    password_hashes = {username: PASSWORDS.hash(password) for username, _, _ in DEMO_ACCOUNTS}
    with privileged_connection() as connection:
        for org, name in (("abc", "ABC Technology (mô phỏng)"), ("xy", "XY Services (mô phỏng)")):
            connection.execute(
                """
                INSERT INTO app_data.companies (id, name, synthetic) VALUES (%s, %s, true)
                ON CONFLICT (id) DO NOTHING
                """,
                (demo_id(org), name),
            )
            for code in ("NV001", "NV002"):
                connection.execute(
                    """
                    INSERT INTO app_data.employees (company_id, id, code, display_name)
                    VALUES (%s, %s, %s, %s) ON CONFLICT (company_id, id) DO NOTHING
                    """,
                    (demo_id(org), demo_id(f"{org}/{code}"), code, f"Nhân viên mô phỏng {code}"),
                )
        for username, role, employee in DEMO_ACCOUNTS:
            org = username.split("-", 1)[0]
            connection.execute(
                """
                INSERT INTO app_auth.users (id, username, password_hash) VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (demo_id(username), username, password_hashes[username]),
            )
            connection.execute(
                """
                INSERT INTO app_auth.memberships (company_id, user_id, role, employee_id)
                VALUES (%s, %s, %s, %s) ON CONFLICT (company_id, user_id) DO NOTHING
                """,
                (
                    demo_id(org),
                    demo_id(username),
                    role,
                    demo_id(f"{org}/{employee}") if employee else None,
                ),
            )
    print("Đã kiểm tra hoặc tạo danh tính mô phỏng: abc-admin, abc-auditor, abc-nv001, xy-admin.")
