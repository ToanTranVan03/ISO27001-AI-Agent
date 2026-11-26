from collections.abc import Iterator
from dataclasses import dataclass
from os import getenv
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from compliance_ai.admin import demo_id, seed_demo_identities
from compliance_ai.api import create_app
from compliance_ai.auth import PASSWORDS
from compliance_ai.db import Database

pytestmark = pytest.mark.postgres
SECRET = "pytest-phase03-local-only-never-use-for-deployment"
PASSWORD = "synthetic-user-test-password"


@dataclass(frozen=True)
class Fixture:
    maintenance: Engine
    app_url: str
    evaluator_url: str
    companies: tuple[UUID, UUID]
    employees: tuple[UUID, UUID, UUID]
    actors: dict[str, UUID]
    logins: dict[str, str]
    docs: tuple[UUID, UUID]


@pytest.fixture(scope="module")
def fixture() -> Iterator[Fixture]:
    admin_url = getenv("TEST_MIGRATION_DATABASE_URL")
    app_url = getenv("TEST_DATABASE_URL")
    evaluator_url = getenv("TEST_EVALUATOR_DATABASE_URL")
    if not (admin_url and app_url and evaluator_url):
        pytest.skip("Set three TEST_*_DATABASE_URL variables for a dedicated migrated test DB")
    database_names = {make_url(url).database or "" for url in (admin_url, app_url, evaluator_url)}
    if len(database_names) != 1 or not next(iter(database_names), "").endswith("_test"):
        pytest.fail("The three test URLs must target the same dedicated *_test database.")
    company_a, company_b = uuid4(), uuid4()
    own, coworker, foreign = uuid4(), uuid4(), uuid4()
    doc_a, doc_b = uuid4(), uuid4()
    actors = {role: uuid4() for role in ("admin", "auditor", "employee", "foreign_admin")}
    logins = {role: str(actor) for role, actor in actors.items()}
    data = Fixture(
        create_engine(admin_url, hide_parameters=True),
        app_url,
        evaluator_url,
        (company_a, company_b),
        (own, coworker, foreign),
        actors,
        logins,
        (doc_a, doc_b),
    )
    password_hash = PASSWORDS.hash(PASSWORD)
    with data.maintenance.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO app_data.companies (id, name, synthetic) VALUES "
                "(:a, 'Tenant A', true), (:b, 'Tenant B', true)"
            ),
            {"a": company_a, "b": company_b},
        )
        connection.execute(
            text("""
                INSERT INTO app_data.employees (company_id, id, code, display_name)
                VALUES (:a, :own, 'NV001', 'Own'), (:a, :coworker, 'NV002', 'Coworker'),
                       (:b, :foreign, 'NV001', 'Foreign')
            """),
            {"a": company_a, "b": company_b, "own": own, "coworker": coworker, "foreign": foreign},
        )
        connection.execute(
            text(
                "INSERT INTO app_auth.users (id, username, password_hash) VALUES "
                "(:id, :username, :password_hash)"
            ),
            [
                {"id": actors[role], "username": login, "password_hash": password_hash}
                for role, login in logins.items()
            ],
        )
        connection.execute(
            text(
                "INSERT INTO app_auth.memberships (company_id, user_id, role, employee_id) "
                "VALUES (:tenant, :actor, :role, :employee)"
            ),
            [
                {
                    "tenant": company_b if role == "foreign_admin" else company_a,
                    "actor": actor,
                    "role": "admin" if role == "foreign_admin" else role,
                    "employee": own if role == "employee" else None,
                }
                for role, actor in actors.items()
            ],
        )
        connection.execute(
            text("""
                INSERT INTO app_data.document_chunks
                    (company_id, id, control_id, source_type, source_ref, content, embedding)
                VALUES (:tenant, :doc, 'A.6.3', 'research_rubric', 'test',
                    'Synthetic test reference', CAST(:vector AS public.vector))
            """),
            [
                {"tenant": tenant, "doc": doc, "vector": str([value] * 384)}
                for tenant, doc, value in ((company_a, doc_a, 1), (company_b, doc_b, 0))
            ],
        )
        connection.execute(
            text("""
                INSERT INTO benchmark_private.expected_results
                    (id, company_id, scenario_id, criterion_id, target_id, expected_status)
                VALUES (:id, :tenant, 'SC-H03', 'H03', :target, 'COMPLIANT')
            """),
            {"id": uuid4(), "tenant": company_a, "target": own},
        )
    try:
        yield data
    finally:
        with data.maintenance.begin() as connection:
            for table in (
                "app_data.audit_events",
                "app_data.asset_return_receipts",
                "app_data.sim_actions",
                "app_data.assessment_jobs",
                "app_data.assessments",
                "app_data.sim_resources",
                "app_data.sim_cases",
                "app_data.policy_versions",
                "benchmark_private.expected_results",
                "app_data.document_chunks",
                "app_auth.memberships",
                "app_data.employees",
            ):
                connection.execute(
                    text(f"DELETE FROM {table} WHERE company_id IN (:a, :b)"),
                    {"a": company_a, "b": company_b},
                )
            connection.execute(
                text("DELETE FROM app_data.companies WHERE id IN (:a, :b)"),
                {"a": company_a, "b": company_b},
            )
            for actor in actors.values():
                connection.execute(text("DELETE FROM app_auth.users WHERE id = :id"), {"id": actor})
        data.maintenance.dispose()


@pytest.fixture
def client(fixture: Fixture, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATABASE_URL", fixture.app_url)
    monkeypatch.setenv("APP_SECRET_KEY", SECRET)
    app = create_app()
    with TestClient(app) as client:
        yield client
    app.state.db.engine.dispose()


def login(client: TestClient, username: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/token", json={"username": username, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_employee_own_scope_and_membership_revocation(client: TestClient, fixture: Fixture) -> None:
    company_a, company_b = fixture.companies
    own, coworker, foreign = fixture.employees
    actor = fixture.actors["employee"]
    assert client.get("/ready").status_code == 200
    assert client.get("/api/v1/companies").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/token",
            json={
                "username": fixture.logins["employee"],
                "password": "wrong",
            },
        ).status_code
        == 401
    )
    supplied = "synthetic-secret" * 20
    rejected = client.post(
        "/api/v1/auth/token",
        json={
            "username": fixture.logins["employee"],
            "password": supplied,
        },
    )
    assert rejected.status_code == 422
    assert supplied not in rejected.text
    headers = login(client, fixture.logins["employee"])
    assert [row["id"] for row in client.get("/api/v1/companies", headers=headers).json()] == [
        str(company_a)
    ]
    base = f"/api/v1/companies/{company_a}/employees"
    assert [row["id"] for row in client.get(base, headers=headers).json()] == [str(own)]
    assert client.get(f"{base}/{own}", headers=headers).status_code == 200
    assert client.get(f"{base}/{coworker}", headers=headers).status_code == 404
    assert client.get(f"{base}/{foreign}", headers=headers).status_code == 404
    assert (
        client.get(
            f"/api/v1/companies/{company_b}/employees",
            headers=headers,
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"{base}/{own}",
            headers=headers,
            json={"display_name": "Denied", "expected_revision": 1},
        ).status_code
        == 403
    )
    with fixture.maintenance.begin() as connection:
        connection.execute(
            text("UPDATE app_auth.memberships SET active = false WHERE user_id = :actor"),
            {"actor": actor},
        )
    try:
        assert client.get("/api/v1/companies", headers=headers).json() == []
        assert client.get(f"{base}/{own}", headers=headers).status_code == 404
    finally:
        with fixture.maintenance.begin() as connection:
            connection.execute(
                text("UPDATE app_auth.memberships SET active = true WHERE user_id = :actor"),
                {"actor": actor},
            )


def test_admin_update_concurrency_and_audit(client: TestClient, fixture: Fixture) -> None:
    company_a, company_b = fixture.companies
    _, coworker, foreign = fixture.employees
    admin = login(client, fixture.logins["admin"])
    auditor = login(client, fixture.logins["auditor"])
    base = f"/api/v1/companies/{company_a}/employees"
    data = {"display_name": "Tên mô phỏng mới", "expected_revision": 1}
    assert client.patch(f"{base}/{coworker}", headers=auditor, json=data).status_code == 403
    assert (
        client.patch(
            f"/api/v1/companies/{company_b}/employees/{foreign}",
            headers=admin,
            json=data,
        ).status_code
        == 404
    )
    assert client.patch(f"{base}/{foreign}", headers=admin, json=data).status_code == 404
    assert (
        client.patch(
            f"{base}/{coworker}",
            headers=admin,
            json={**data, "role": "admin"},
        ).status_code
        == 422
    )
    response = client.patch(f"{base}/{coworker}", headers=admin, json=data)
    assert response.status_code == 200
    assert response.json()["revision"] == 2
    assert client.patch(f"{base}/{coworker}", headers=admin, json=data).status_code == 409
    with fixture.maintenance.connect() as connection:
        audit = connection.execute(
            text(
                "SELECT company_id, actor_id, detail FROM app_data.audit_events "
                "WHERE target_id = :target"
            ),
            {"target": coworker},
        ).one()
        assert tuple(audit) == (company_a, fixture.actors["admin"], {"revision": 2})
        assert (
            connection.scalar(
                text(
                    "SELECT revision FROM app_data.employees "
                    "WHERE company_id = :tenant AND id = :id"
                ),
                {"tenant": company_b, "id": foreign},
            )
            == 1
        )


def test_pgvector_scope_and_no_ambient_tenant(fixture: Fixture) -> None:
    db = Database(fixture.app_url)
    company_a, company_b = fixture.companies
    admin = fixture.actors["admin"]
    employee = fixture.actors["employee"]
    try:
        with db.transaction(admin, company_a) as connection:
            assert [
                doc.id
                for doc in db.nearest_documents(
                    connection,
                    company_a,
                    "A.6.3",
                    [0.0] * 384,
                    5,
                )
            ] == [fixture.docs[0]]
            assert db.nearest_documents(connection, company_b, "A.6.3", [0.0] * 384, 5) == []
            assert connection.scalar(text("SELECT count(*) FROM app_data.document_chunks")) == 1
        with db.transaction(admin, company_b) as connection:
            assert connection.scalar(text("SELECT count(*) FROM app_data.document_chunks")) == 0
        with db.transaction(employee, company_a) as connection:
            assert connection.scalar(text("SELECT count(*) FROM app_data.document_chunks")) == 0
        with db.transaction() as connection:
            assert connection.scalar(text("SELECT count(*) FROM app_data.document_chunks")) == 0
            assert connection.scalar(text("SELECT count(*) FROM app_data.employees")) == 0
    finally:
        db.engine.dispose()


def test_database_denies_oracle_audit_rewrites_and_cross_tenant_writes(fixture: Fixture) -> None:
    db = Database(fixture.app_url)
    evaluator = create_engine(fixture.evaluator_url, hide_parameters=True)
    company_a, company_b = fixture.companies
    foreign = fixture.employees[2]
    admin = fixture.actors["admin"]
    try:
        with db.transaction(admin, company_b) as connection:
            assert (
                connection.execute(
                    text(
                        "UPDATE app_data.employees SET display_name = 'Blocked' WHERE id = :foreign"
                    ),
                    {"foreign": foreign},
                ).rowcount
                == 0
            )
        with (
            pytest.raises(DBAPIError, match="permission denied"),
            db.transaction(admin, company_a) as connection,
        ):
            connection.execute(text("SELECT * FROM benchmark_private.expected_results"))
        with (
            pytest.raises(DBAPIError, match="permission denied"),
            db.transaction(admin, company_a) as connection,
        ):
            connection.execute(text("DELETE FROM app_data.audit_events"))
        with evaluator.connect() as connection:
            assert (
                connection.scalar(
                    text(
                        "SELECT expected_status FROM benchmark_private.expected_results "
                        "WHERE company_id = :tenant"
                    ),
                    {"tenant": company_a},
                )
                == "COMPLIANT"
            )
        with pytest.raises(DBAPIError, match="permission denied"), evaluator.begin() as connection:
            connection.execute(text("SELECT * FROM app_data.employees"))
        with pytest.raises(DBAPIError, match="permission denied"), evaluator.begin() as connection:
            connection.execute(text("DELETE FROM benchmark_private.expected_results"))
    finally:
        db.engine.dispose()


def test_demo_seed_is_idempotent(fixture: Fixture, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIGRATION_DATABASE_URL", getenv("TEST_MIGRATION_DATABASE_URL", ""))
    monkeypatch.setattr("compliance_ai.admin.getpass", lambda _: PASSWORD)

    def count_employees() -> int | None:
        with fixture.maintenance.connect() as connection:
            return connection.scalar(
                text("SELECT count(*) FROM app_data.employees WHERE company_id = :company"),
                {"company": demo_id("abc")},
            )

    try:
        seed_demo_identities()
        assert count_employees() == 2
        seed_demo_identities()
        assert count_employees() == 2
        db = Database(fixture.app_url)
        try:
            record = db.credentials("abc-nv001")
            assert record is not None and PASSWORDS.verify(record[1], PASSWORD)
        finally:
            db.engine.dispose()
    finally:
        tenants = {"a": demo_id("abc"), "b": demo_id("xy")}
        with fixture.maintenance.begin() as connection:
            for table in ("app_auth.memberships", "app_data.employees"):
                connection.execute(
                    text(f"DELETE FROM {table} WHERE company_id IN (:a, :b)"),
                    tenants,
                )
            connection.execute(text("DELETE FROM app_data.companies WHERE id IN (:a, :b)"), tenants)
            for username in ("abc-admin", "abc-auditor", "abc-nv001", "xy-admin"):
                connection.execute(
                    text("DELETE FROM app_auth.users WHERE id = :id"),
                    {"id": demo_id(username)},
                )


def test_nv015_offboarding_and_employee_retest(
    client: TestClient, fixture: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import UTC, datetime, timedelta
    from json import dumps
    from pathlib import Path

    from compliance_ai.catalog import load_catalog

    tenant, foreign = fixture.companies
    employee = fixture.employees[0]
    departed = uuid4()
    catalog = load_catalog(Path("configs"))
    policy = next(item for item in catalog.policies if item.id == "abc")
    with fixture.maintenance.begin() as connection:
        connection.execute(
            text("""
            INSERT INTO app_data.policy_versions (company_id,version,effective_at,document)
            VALUES (:tenant,1,now(),CAST(:doc AS jsonb))
        """),
            {"tenant": tenant, "doc": policy.model_dump_json()},
        )
        connection.execute(
            text("""
            INSERT INTO app_data.employees (
                company_id,id,code,display_name,employment_status,termination_effective_at
            ) VALUES (:tenant,:employee,'NV015','Synthetic Exit','terminated',now())
        """),
            {"tenant": tenant, "employee": departed},
        )
        for owner, kind, state in (
            (departed, "account", {"enabled": True, "grants": ["VPN", "APP"], "protected": False}),
            (departed, "endpoint", {"screen_lock_seconds": 900, "patches": []}),
            (departed, "asset", {"returned": False, "return_receipt": None}),
            (employee, "training", {"nda_signed": True, "assignment": None}),
            (
                employee,
                "account",
                {
                    "enabled": True,
                    "protected": False,
                    "mfa_registered": False,
                    "mfa_enforced": False,
                },
            ),
        ):
            connection.execute(
                text("""
                INSERT INTO app_data.sim_resources (company_id,id,employee_id,kind,state,updated_at)
                VALUES (:tenant,:id,:employee,:kind,CAST(:state AS jsonb),now())
            """),
                {
                    "tenant": tenant,
                    "id": uuid4(),
                    "employee": owner,
                    "kind": kind,
                    "state": dumps(state),
                },
            )
    admin = login(client, fixture.logins["admin"])
    auditor = login(client, fixture.logins["auditor"])
    learner = login(client, fixture.logins["employee"])
    base = f"/api/v1/companies/{tenant}"

    def scan(code: str, headers: dict[str, str], key: str) -> dict:
        response = client.post(
            f"{base}/assessments",
            json={"employee_code": code},
            headers=headers | {"Idempotency-Key": key},
        )
        assert response.status_code == 200, response.text
        return response.json()

    def plan(assessment: dict, criterion: str, headers: dict[str, str]) -> dict:
        finding = next(item for item in assessment["findings"] if item["criterion_id"] == criterion)
        response = client.post(
            f"{base}/assessments/{assessment['id']}/findings/{finding['id']}/plan",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        return response.json()

    def execute_action(action: dict, key: str, expected: int = 200) -> dict:
        response = client.post(
            f"{base}/actions/{action['id']}/execute",
            json={"plan_hash": action["plan_hash"]},
            headers=admin | {"Idempotency-Key": key},
        )
        assert response.status_code == expected, response.text
        return response.json()

    actor_run = scan("NV015", auditor, "offboard-0001")
    queue = f"{base}/assessment-jobs"
    queued_headers = auditor | {"Idempotency-Key": "offboard-queued"}
    scope = {"employee_code": "NV015"}
    queued = client.post(queue, headers=queued_headers, json=scope)
    assert queued.status_code == 202, queued.text
    checkpoint = queued.json()
    assert checkpoint["state"] == "PENDING"
    assert client.post(queue, headers=queued_headers, json=scope).json() == checkpoint
    assert (
        client.post(queue, headers=queued_headers, json={"employee_code": "NV001"}).status_code
        == 409
    )
    job_url = f"{queue}/{checkpoint['id']}"
    assert client.get(job_url, headers=auditor).json() == checkpoint
    assert client.post(job_url + "/resume", headers=admin).status_code == 404
    assert (
        client.post(
            job_url.replace(str(tenant), str(foreign)) + "/resume", headers=auditor
        ).status_code
        == 404
    )
    completed_job = client.post(job_url + "/resume", headers=auditor).json()
    assert completed_job["state"] == "COMPLETED" and completed_job["assessment_id"]
    assert client.post(job_url + "/resume", headers=auditor).json() == completed_job
    background = client.post(
        queue + "?start=true",
        json=scope,
        headers=auditor | {"Idempotency-Key": "offboard-background"},
    )
    assert background.status_code == 202
    background_job = client.get(f"{queue}/{background.json()['id']}", headers=auditor).json()
    assert background_job["state"] == "COMPLETED"
    (citation,) = actor_run["citations_by_control"]["A.6.3"]
    assert citation["chunk_id"] == str(fixture.docs[0])
    assert actor_run["citations_by_control"]["A.5.11"] == []
    reference_url = f"{base}/knowledge/A.6.3/chunks/{citation['chunk_id']}"
    fingerprint = {"expected_sha256": citation["content_sha256"]}
    assert client.get(reference_url, headers=auditor, params=fingerprint).json()["id"] == str(
        fixture.docs[0]
    )
    assert client.get(reference_url, headers=learner, params=fingerprint).status_code == 403
    for wrong in (
        reference_url.replace("A.6.3", "A.5.11"),
        reference_url.replace(str(fixture.docs[0]), str(fixture.docs[1])),
    ):
        assert client.get(wrong, headers=auditor, params=fingerprint).status_code == 404
    assert (
        client.get(reference_url, headers=auditor, params={"expected_sha256": "0" * 64}).status_code
        == 409
    )
    assert actor_run["workflow_steps"] == ["observe", "people", "hardware", "software", "report"]
    assert actor_run == scan("NV015", auditor, "offboard-0001")
    assert (
        client.get(
            f"/api/v1/companies/{foreign}/assessments/{actor_run['id']}", headers=admin
        ).status_code
        == 404
    )
    account = plan(actor_run, "H09", auditor)
    stale_grants = plan(actor_run, "M01", auditor)
    decision = {"approve": True, "plan_hash": account["plan_hash"]}
    path = f"{base}/actions/{account['id']}"
    proof = {"plan_hash": account["plan_hash"]}
    assert client.post(path + "/dry-run", headers=learner, json=proof).status_code == 403
    preview = client.post(path + "/dry-run", headers=auditor, json=proof).json()
    assert (
        preview["state"] == "NEEDS_APPROVAL" and preview["revision"] == account["plan"]["revision"]
    )
    assert client.get(path, headers=admin).json() == account
    # The protected flag must block the action even if an adapter has not advanced its revision.
    protect = text("""
        UPDATE app_data.sim_resources
        SET state=jsonb_set(state,'{protected}',to_jsonb(CAST(:v AS boolean)))
        WHERE company_id=:c AND id=:id
    """)
    params = {"c": tenant, "id": account["plan"]["target_id"]}
    with fixture.maintenance.begin() as connection:
        connection.execute(protect, params | {"v": True})
    assert client.post(path + "/dry-run", headers=admin, json=proof).json()["state"] == "BLOCKED"
    assert client.post(path + "/decision", headers=admin, json=decision).status_code == 409
    with fixture.maintenance.begin() as connection:
        connection.execute(protect, params | {"v": False})
    assert (
        client.post(
            path + "/dry-run", headers=admin, json=proof | {"command": "arbitrary"}
        ).status_code
        == 422
    )
    stale_path = f"{base}/actions/{stale_grants['id']}"
    grant_proof = {"plan_hash": stale_grants["plan_hash"]}
    assert (
        client.post(
            stale_path + "/decision", headers=admin, json=grant_proof | {"approve": True}
        ).json()["state"]
        == "APPROVED"
    )

    def future_clock(minutes: int) -> type[datetime]:
        moment = datetime.now(UTC) + timedelta(minutes=minutes)

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return moment.astimezone(tz)

        return Clock

    other = scan("NV015", auditor, "gate-expiry")
    waiting = plan(other, "H09", auditor)
    approved = plan(other, "M01", auditor)
    own = plan(scan("NV015", admin, "gate-separation"), "H09", admin)
    assert (
        client.post(
            f"{base}/actions/{own['id']}/decision",
            headers=admin,
            json={"approve": True, "plan_hash": own["plan_hash"]},
        ).status_code
        == 409
    )
    approve_url = f"{base}/actions/{approved['id']}"
    approved_proof = {"plan_hash": approved["plan_hash"]}
    assert (
        client.post(
            approve_url + "/decision", headers=admin, json=approved_proof | {"approve": True}
        ).json()["state"]
        == "APPROVED"
    )
    with monkeypatch.context() as clock:
        clock.setattr("compliance_ai.actions.datetime", future_clock(16))
        assert (
            client.post(approve_url + "/dry-run", headers=admin, json=approved_proof).json()[
                "state"
            ]
            == "EXPIRED"
        )
        assert execute_action(approved, "expired-approval")["state"] == "EXPIRED"
        assert execute_action(approved, "expired-approval")["state"] == "EXPIRED"
        clock.setattr("compliance_ai.actions.datetime", future_clock(61))
        expired = client.post(
            f"{base}/actions/{waiting['id']}/decision",
            headers=admin,
            json={"approve": True, "plan_hash": waiting["plan_hash"]},
        ).json()
        assert expired["state"] == "EXPIRED" and expired["approved_by"] is None
        execute_action(waiting, "expired-plan", expected=409)
    assert client.post(f"{path}/decision", json=decision, headers=auditor).status_code == 403
    execute_action(account, "execute-0001", expected=409)
    rejected = client.post(
        f"{path}/decision",
        json=decision | {"plan_hash": "0" * 64},
        headers=admin,
    )
    assert rejected.status_code == 409
    assert (
        client.post(f"{path}/decision", json=decision, headers=admin).json()["state"] == "APPROVED"
    )
    assert execute_action(account, "execute-0001")["state"] == "SUCCEEDED"
    assert execute_action(account, "execute-0001")["state"] == "SUCCEEDED"
    execute_action(account, "execute-0002", expected=409)
    verified = client.post(f"{path}/verify", headers=admin).json()
    assert verified["state"] == "VERIFIED" and verified["verification"]["fresh"]
    asset = plan(actor_run, "D02", auditor)
    assert execute_action(asset, "execute-0003")["state"] == "WAITING_EXTERNAL"
    assert client.post(f"{base}/actions/{asset['id']}/verify", headers=admin).json()["state"] == (
        "WAITING_EXTERNAL"
    )
    assert (
        client.post(stale_path + "/dry-run", headers=admin, json=grant_proof).json()["state"]
        == "BLOCKED"
    )
    assert execute_action(stale_grants, "execute-stale")["state"] == "FAILED"
    resumed = scan("NV015", auditor, "offboard-0002")
    grants = plan(resumed, "M01", auditor)
    assert (
        client.post(
            f"{base}/actions/{grants['id']}/decision",
            json={"approve": True, "plan_hash": grants["plan_hash"]},
            headers=admin,
        ).status_code
        == 200
    )
    assert execute_action(grants, "execute-0004")["state"] == "SUCCEEDED"
    assert client.post(f"{base}/actions/{grants['id']}/verify", headers=admin).json()["state"] == (
        "VERIFIED"
    )
    patch_run = scan("NV015", auditor, "offboard-patch")
    patch = plan(patch_run, "S04", auditor)
    assert patch["plan"]["risk"] == "medium"
    assert patch["plan"]["changes"] == {"patches": ["SIM-001"]}
    assert (
        client.post(
            f"{base}/actions/{patch['id']}/decision",
            json={"approve": True, "plan_hash": patch["plan_hash"]},
            headers=admin,
        ).status_code
        == 200
    )
    assert execute_action(patch, "execute-patch")["state"] == "SUCCEEDED"
    assert (
        client.post(
            f"{base}/actions/{patch['id']}/verify",
            headers=admin,
        ).json()["state"]
        == "VERIFIED"
    )
    baseline_run = scan("NV015", auditor, "offboard-baseline")
    baseline = plan(baseline_run, "S05", auditor)
    assert baseline["plan"]["risk"] == "medium"
    assert baseline["plan"]["changes"] == {"screen_lock_seconds": 300}
    assert (
        client.post(
            f"{base}/actions/{baseline['id']}/decision",
            json={"approve": True, "plan_hash": baseline["plan_hash"]},
            headers=admin,
        ).status_code
        == 200
    )
    assert execute_action(baseline, "execute-baseline")["state"] == "SUCCEEDED"
    assert (
        client.post(
            f"{base}/actions/{baseline['id']}/verify",
            headers=admin,
        ).json()["state"]
        == "VERIFIED"
    )
    final = scan("NV015", auditor, "offboard-0003")
    comparison = client.get(
        f"{base}/assessments/{final['id']}/compare",
        params={"before": actor_run["id"]},
        headers=auditor,
    )
    assert comparison.status_code == 200 and len(comparison.json()["changes"]) >= 4
    csv_response = client.get(f"{base}/assessments/{final['id']}/reports/gap.csv", headers=auditor)
    assert csv_response.status_code == 200 and "H09" in csv_response.text
    outcomes = {item["criterion_id"]: item["status"] for item in final["findings"]}
    assert outcomes["H09"] == outcomes["M01"] == "COMPLIANT"
    assert outcomes["D02"] == "INSUFFICIENT_EVIDENCE"
    assert outcomes["S04"] == outcomes["S05"] == "COMPLIANT"

    rollback_path = f"{base}/actions/{baseline['id']}/rollback"
    rollback_proof = {"plan_hash": baseline["plan_hash"]}
    assert client.post(rollback_path, json=rollback_proof, headers=auditor).status_code == 403
    assert (
        client.post(rollback_path, json={"plan_hash": "0" * 64}, headers=admin).status_code == 409
    )
    assert (
        client.post(
            f"{base}/actions/{patch['id']}/rollback",
            json={"plan_hash": patch["plan_hash"]},
            headers=admin,
        ).status_code
        == 409
    )
    restored = client.post(rollback_path, json=rollback_proof, headers=admin)
    assert restored.status_code == 200, restored.text
    assert restored.json()["state"] == "ROLLED_BACK"
    assert restored.json()["verification"]["restored"]
    assert client.post(rollback_path, json=rollback_proof, headers=admin).json() == restored.json()
    after_rollback = scan("NV015", auditor, "offboard-rollback")
    restored_outcomes = {
        item["criterion_id"]: item["status"] for item in after_rollback["findings"]
    }
    assert restored_outcomes["S05"] == "NON_COMPLIANT"
    assert restored_outcomes["S04"] == "COMPLIANT"
    assert client.get(f"{base}/assessments/{final['id']}", headers=auditor).json() == final

    incomplete = {"kind": "initial", "answer": "Tôi sẽ mở tin nhắn."}
    assert (
        client.post(f"{base}/me/interview", json=incomplete, headers=learner).json()["grade"][
            "status"
        ]
        == "FOLLOWUP"
    )
    assert (
        client.post(f"{base}/me/interview", json=incomplete, headers=learner).json()["grade"][
            "status"
        ]
        == "FAILED"
    )
    learning_run = scan("NV001", auditor, "learning-0001")
    task = plan(learning_run, "H03", auditor)
    assert execute_action(task, "execute-0005")["state"] == "WAITING_EXTERNAL"
    task_path = f"{base}/actions/{task['id']}"
    assert client.post(f"{task_path}/verify", headers=admin).json()["state"] == "WAITING_EXTERNAL"
    retest = {
        "kind": "retest",
        "answer": "Tin nhắn đáng ngờ. Tôi không mở tệp và sẽ báo cáo cho SOC.",
    }
    assert client.post(f"{base}/me/interview", json=retest, headers=learner).status_code == 409
    assert client.post(f"{base}/me/training/complete", headers=admin).status_code == 404
    assert (
        client.post(f"{base}/me/training/complete", headers=learner).json()["status"] == "COMPLETED"
    )
    assert (
        client.post(f"{base}/me/interview", json=retest, headers=learner).json()["grade"]["status"]
        == "PASSED"
    )
    assert client.post(f"{task_path}/verify", headers=admin).json()["state"] == "VERIFIED"
    # An old true flag does not establish which document this employee acknowledged.
    nda_run = scan("NV001", auditor, "nda-initial")

    def h06(run: dict) -> dict:
        return next(item for item in run["findings"] if item["criterion_id"] == "H06")

    assert h06(nda_run)["status"] == "INSUFFICIENT_EVIDENCE"
    nda_action = plan(nda_run, "H06", auditor)
    assert execute_action(nda_action, "nda-request")["state"] == "WAITING_EXTERNAL"
    verify_nda = f"{base}/actions/{nda_action['id']}/verify"
    assert client.post(verify_nda, headers=admin).json()["state"] == "WAITING_EXTERNAL"
    pending = h06(scan("NV001", auditor, "nda-waiting"))
    assert pending["status"] == h06(nda_run)["status"] and pending["proposed_tool"] is None
    view = client.get(f"{base}/me/training", headers=learner).json()
    doc = nda_action["plan"]["nda_document"]
    assert doc == view["nda"]["document"]
    proof = {
        "request_id": nda_action["id"],
        "document_hash": doc["sha256"],
        "expected_revision": view["revision"],
        "acknowledged": True,
    }
    ack_url = f"{base}/me/nda/acknowledge"
    for headers in (auditor, admin):
        assert client.post(ack_url, headers=headers, json=proof).status_code == 404
    assert (
        client.post(
            ack_url.replace(str(tenant), str(foreign)), headers=learner, json=proof
        ).status_code
        == 404
    )
    for overrides in (
        {"document_hash": "0" * 64},
        {"acknowledged": False},
        {"expected_revision": proof["expected_revision"] - 1},
    ):
        assert client.post(ack_url, headers=learner, json=proof | overrides).status_code == 409
    assert (
        client.post(ack_url, headers=learner, json=proof | {"request_id": str(uuid4())}).status_code
        == 404
    )
    submitted = client.post(ack_url, headers=learner, json=proof)
    assert submitted.status_code == 200, submitted.text
    receipt = submitted.json()
    assert receipt["submitted_by"] == str(fixture.actors["employee"])
    assert client.post(ack_url, headers=learner, json=proof).json() == receipt
    verified_nda = client.post(verify_nda, headers=admin).json()
    assert verified_nda["state"] == "VERIFIED"
    assert verified_nda["verification"]["receipt_id"] == receipt["evidence_id"]
    after = h06(scan("NV001", auditor, "nda-after"))
    assert after["status"] == "COMPLIANT" and receipt["evidence_id"] in after["evidence_ids"]

    from psycopg import connect

    from compliance_ai.mfa_simulator import record_observation

    def s02(key: str) -> dict:
        return next(
            item
            for item in scan("NV001", auditor, key)["findings"]
            if item["criterion_id"] == "S02"
        )

    mfa_run = scan("NV001", auditor, "mfa-initial")
    initial = next(item for item in mfa_run["findings"] if item["criterion_id"] == "S02")
    assert initial["status"] == "NON_COMPLIANT"
    mfa = plan(mfa_run, "S02", auditor)
    assert execute_action(mfa, "request-mfa")["state"] == "WAITING_EXTERNAL"
    check = f"{base}/actions/{mfa['id']}/verify"
    pending_mfa = s02("mfa-pending")
    assert pending_mfa["status"] == "NON_COMPLIANT" and pending_mfa["proposed_tool"] is None
    assert client.get(f"{base}/me/training", headers=learner).json()["mfa_request_id"] == mfa["id"]
    assert (
        client.get(f"/api/v1/companies/{foreign}/me/training", headers=learner).status_code == 404
    )
    assert client.post(check, headers=admin).json()["state"] == "WAITING_EXTERNAL"
    revision = pending_mfa["observed"]["revision"]
    test_url = fixture.maintenance.url.set(drivername="postgresql").render_as_string(
        hide_password=False
    )
    from compliance_ai.asset_return import receive_asset

    ticket = UUID(asset["id"])
    asset_id = UUID(asset["plan"]["target_id"])
    awaiting = next(item for item in final["findings"] if item["criterion_id"] == "D02")
    assert awaiting["observed"]["return_timing"] == "WITHIN_WINDOW"
    assert awaiting["proposed_tool"] is None and awaiting["observed"]["request_id"] == str(ticket)
    asset_revision = awaiting["observed"]["revision"]
    asset_check = f"{base}/actions/{ticket}/verify"
    with connect(test_url) as desk:
        for company, code, target, request, rev in (
            (foreign, "NV015", asset_id, ticket, asset_revision),
            (tenant, "NV001", asset_id, ticket, asset_revision),
            (tenant, "NV015", uuid4(), ticket, asset_revision),
            (tenant, "NV015", asset_id, uuid4(), asset_revision),
            (tenant, "NV015", asset_id, ticket, asset_revision - 1),
        ):
            with pytest.raises(ValueError):
                receive_asset(desk, company, code, target, request, rev)
    # An inventory flag and reference without the desk's matching record cannot close the ticket.
    with connect(test_url) as desk:
        desk.execute(
            """
            UPDATE app_data.sim_resources SET state=state ||
              '{"returned":true,"return_receipt":"unconfirmed","custody":"asset_desk"}'::jsonb,
              revision=revision+1,updated_at=clock_timestamp() WHERE company_id=%s AND id=%s
        """,
            (tenant, asset_id),
        )
    conflict = scan("NV015", auditor, "asset-unconfirmed")
    assert next(i for i in conflict["findings"] if i["criterion_id"] == "D02")["status"] == (
        "INSUFFICIENT_EVIDENCE"
    )
    assert client.post(asset_check, headers=admin).json()["state"] == "WAITING_EXTERNAL"
    with connect(test_url) as desk:
        source = desk.execute(
            """
            UPDATE app_data.sim_resources SET state=state ||
              '{"returned":false,"return_receipt":null,"custody":"employee"}'::jsonb,
              revision=revision+1,updated_at=clock_timestamp()
            WHERE company_id=%s AND id=%s RETURNING revision
        """,
            (tenant, asset_id),
        ).fetchone()
        assert source is not None
        asset_revision = source[0]
    # Exercise the overdue path by correcting the synthetic HR separation date.
    with fixture.maintenance.begin() as connection:
        connection.execute(
            text("""
            UPDATE app_data.employees SET termination_effective_at=now()-interval '10 days',
                revision=revision+1 WHERE company_id=:tenant AND id=:employee
        """),
            {"tenant": tenant, "employee": departed},
        )
    overdue_run = scan("NV015", auditor, "offboard-overdue")
    overdue_asset = next(item for item in overdue_run["findings"] if item["criterion_id"] == "D02")
    assert overdue_asset["status"] == "NON_COMPLIANT"
    assert overdue_asset["observed"]["return_timing"] == "OVERDUE"
    with connect(test_url) as desk:
        received = receive_asset(desk, tenant, "NV015", asset_id, ticket, asset_revision)
    closed_asset = client.post(asset_check, headers=admin).json()
    assert closed_asset["state"] == "VERIFIED"
    assert closed_asset["verification"]["receipt_id"] == received["receipt_id"]
    assert closed_asset["verification"]["return_timing"] == "LATE"
    db = Database(fixture.app_url)
    try:
        select_receipt = text("SELECT id FROM app_data.asset_return_receipts WHERE id=:id")
        params = {"id": UUID(received["receipt_id"])}
        for role, company, expected in (
            ("auditor", tenant, params["id"]),
            ("employee", tenant, None),
            ("foreign_admin", foreign, None),
            ("admin", foreign, None),
        ):
            with db.transaction(fixture.actors[role], company) as reader:
                assert reader.scalar(select_receipt, params) == expected
                for privilege in ("INSERT", "UPDATE", "DELETE"):
                    assert (
                        reader.scalar(
                            text(
                                "SELECT has_table_privilege(current_user,"
                                "'app_data.asset_return_receipts',:p)"
                            ),
                            {"p": privilege},
                        )
                        is False
                    )
    finally:
        db.engine.dispose()
    with connect(test_url) as desk:
        assert receive_asset(desk, tenant, "NV015", asset_id, ticket, asset_revision) == received
    after_return = scan("NV015", auditor, "offboard-returned")
    returned = next(i for i in after_return["findings"] if i["criterion_id"] == "D02")
    assert returned["status"] == "PARTIAL" and received["receipt_id"] in returned["evidence_ids"]
    assert returned["observed"]["return_timing"] == "LATE" and returned["proposed_tool"] is None
    assert returned["observed"]["revision"] == asset_revision + 1
    assert client.get(f"{base}/assessments/{final['id']}", headers=auditor).json() == final
    with connect(test_url) as identity:
        with pytest.raises(ValueError):
            record_observation(identity, foreign, "NV001", revision, True, True)
        with pytest.raises(ValueError):
            record_observation(identity, tenant, "NV001", revision - 1, True, True)
        partial = record_observation(identity, tenant, "NV001", revision, True, False)
    assert s02("mfa-partial")["status"] == "PARTIAL"
    assert client.get(f"{base}/me/training", headers=learner).json()["mfa_request_id"] is None
    assert client.post(check, headers=admin).json()["state"] == "WAITING_EXTERNAL"
    with connect(test_url) as identity:
        both = record_observation(identity, tenant, "NV001", partial["revision"], True, True)
    closed = client.post(check, headers=admin).json()
    assert closed["state"] == "VERIFIED"
    assert closed["verification"]["identity_event_id"] == both["event"]["id"]
    assert s02("mfa-closed")["status"] == "COMPLIANT"
    with connect(test_url) as identity:
        record_observation(identity, tenant, "NV001", both["revision"], False, True)
    reopened = s02("mfa-reopened")
    assert reopened["status"] == "PARTIAL" and reopened["proposed_tool"] == "request_mfa_enrollment"
    with fixture.maintenance.begin() as connection:
        connection.execute(
            text("""
            UPDATE app_data.sim_resources SET state=state-'mfa_enforced',revision=revision+1
            WHERE company_id=:t AND employee_id=:e AND kind='account'
        """),
            {"t": tenant, "e": employee},
        )
    unknown = s02("mfa-missing")
    assert unknown["status"] == "INSUFFICIENT_EVIDENCE"
    assert unknown["proposed_tool"] is None and "mfa_enforced" in unknown["missing_evidence"]
    assert (
        client.get(
            f"{base}/assessments/{actor_run['id']}/reports/remediation",
            headers=auditor,
        ).status_code
        == 200
    )


def test_dashboard_runs_assessment_approval_and_report_through_real_api(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import os
    import socket
    import subprocess
    import sys
    from pathlib import Path
    from time import monotonic, sleep
    from urllib.error import URLError
    from urllib.request import urlopen

    from streamlit.testing.v1 import AppTest

    from compliance_ai.catalog import research_catalog

    tenant, _ = fixture.companies
    employee, target = uuid4(), uuid4()
    policy = next(item for item in research_catalog().policies if item.id == "abc")
    with fixture.maintenance.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO app_data.policy_versions(company_id,version,effective_at,document)
                VALUES (:tenant,1,now(),CAST(:doc AS jsonb)) ON CONFLICT DO NOTHING
            """),
            {"tenant": tenant, "doc": policy.model_dump_json()},
        )
        connection.execute(
            text("""
                INSERT INTO app_data.employees
                    (company_id,id,code,display_name,employment_status,termination_effective_at)
                VALUES (:tenant,:employee,'NV019','UI test','terminated',now())
            """),
            {"tenant": tenant, "employee": employee},
        )
        connection.execute(
            text("""
                INSERT INTO app_data.sim_resources(company_id,id,employee_id,kind,state,updated_at)
                VALUES (:tenant,:target,:employee,'account',
                        jsonb_build_object('enabled',true,'protected',false,'grants','[]'::jsonb),
                        now())
            """),
            {"tenant": tenant, "employee": employee, "target": target},
        )

    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
    monkeypatch.setenv("COMPLIANCE_API_PORT", str(port))
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "compliance_ai.api:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        env=os.environ | {"DATABASE_URL": fixture.app_url, "APP_SECRET_KEY": SECRET},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        ready = False
        deadline = monotonic() + 15
        while monotonic() < deadline and process.poll() is None:
            try:
                with urlopen(f"http://127.0.0.1:{port}/ready", timeout=1) as response:
                    ready = response.status == 200
                    break
            except (URLError, TimeoutError):
                sleep(0.1)
        assert ready, "API did not become ready for dashboard integration test."
        path = Path(__file__).resolve().parents[1] / "ui" / "streamlit_app.py"
        app = AppTest.from_file(path, default_timeout=12).run()
        app.text_input[0].set_value(fixture.logins["auditor"])
        app.text_input[1].set_value(PASSWORD)
        app.button[0].click().run()
        assert not app.exception
        assert any(element.value == "Đánh giá" for element in app.header)
        assert len(app.sidebar.selectbox) == 1
        assert app.sidebar.selectbox[0].options == ["Tenant A"]

        def button(label: str):
            return next(widget for widget in app.button if widget.label == label)

        def input_field(label: str):
            return next(widget for widget in app.text_input if widget.label == label)

        input_field("Mã nhân viên").set_value("NV019")
        button("Lưu yêu cầu để chạy sau").click().run()
        assert app.session_state["job"]["state"] == "PENDING"
        button("Chạy yêu cầu đã lưu").click().run()
        button("Xem kết quả yêu cầu").click().run()
        run = app.session_state["run"]
        assert run["scope"]["employee_code"] == "NV019"
        button("Lập kế hoạch mô phỏng").click().run()
        action = app.session_state["action_id"]
        assert not any(widget.label == "Phê duyệt mô phỏng" for widget in app.button)
        app.sidebar.button[0].click().run()
        app.text_input[0].set_value(fixture.logins["admin"])
        app.text_input[1].set_value(PASSWORD)
        app.button[0].click().run()
        input_field("Mã đánh giá đã lưu").set_value(run["id"]).run()
        button("Mở đánh giá").click().run()
        input_field("Mã hành động cần mở").set_value(action).run()
        button("Chạy thử điều kiện thực thi").click().run()
        button("Phê duyệt mô phỏng").click().run()
        button("Thực thi mô phỏng").click().run()
        button("Đọc lại nguồn để xác minh").click().run()
        button("Báo cáo khắc phục").click().run()
        report = app.session_state[f"report-remediation-{run['id']}"]
        assert not app.exception and not app.error
        assert any(
            item["id"] == action and item["state"] == "VERIFIED" for item in report["actions"]
        )
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_checkpoint_rejects_a_new_policy_before_resume(
    client: TestClient, fixture: Fixture
) -> None:
    from compliance_ai.catalog import research_catalog

    tenant = fixture.companies[1]
    policy = next(item for item in research_catalog().policies if item.id == "abc")
    insert = text("""
        INSERT INTO app_data.policy_versions(company_id,version,effective_at,document)
        VALUES (:tenant,:version,now(),CAST(:doc AS jsonb))
    """)
    with fixture.maintenance.begin() as connection:
        connection.execute(
            insert, {"tenant": tenant, "version": 1, "doc": policy.model_dump_json()}
        )
    admin = login(client, fixture.logins["foreign_admin"])
    jobs = f"/api/v1/companies/{tenant}/assessment-jobs"
    queued = client.post(
        jobs, json={"employee_code": "NV001"}, headers=admin | {"Idempotency-Key": "stale-policy"}
    )
    assert queued.status_code == 202, queued.text
    with fixture.maintenance.begin() as connection:
        new_policy = policy.model_copy(update={"version": 2})
        connection.execute(
            insert, {"tenant": tenant, "version": 2, "doc": new_policy.model_dump_json()}
        )
    path = f"{jobs}/{queued.json()['id']}"
    assert client.post(path + "/resume", headers=admin).status_code == 409
    assert client.get(path, headers=admin).json() == queued.json()
