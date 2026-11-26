from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints

from compliance_ai.auth import TOKEN_SECONDS, issue_token, verified_actor, verify_password
from compliance_ai.db import Company, Database, Employee

router = APIRouter(prefix="/api/v1")
bearer = HTTPBearer(auto_error=False)
DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class TokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    password: SecretStr = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = TOKEN_SECONDS


class EditEmployee(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: DisplayName
    expected_revision: int = Field(gt=0, strict=True)


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Thông tin xác thực không hợp lệ.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def database(request: Request) -> Database:
    db: Database | None = request.app.state.db
    if db is None:
        raise HTTPException(503, "Cơ sở dữ liệu chưa được cấu hình.")
    return db


DB = Annotated[Database, Depends(database)]


def identity(
    request: Request,
    db: DB,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> UUID:
    if credentials is None:
        raise unauthorized()
    try:
        actor = verified_actor(credentials.credentials, request.app.state.auth_secret)
    except (InvalidTokenError, ValueError) as error:
        raise unauthorized() from error
    if not db.user_enabled(actor):
        raise unauthorized()
    return actor


Actor = Annotated[UUID, Depends(identity)]


@router.post("/auth/token", tags=["auth"])
def token(payload: TokenRequest, request: Request, db: DB) -> TokenResponse:
    record = db.credentials(payload.username.strip().lower())
    if not verify_password(payload.password.get_secret_value(), record[1] if record else None):
        raise unauthorized()
    if record is None:
        raise unauthorized()
    return TokenResponse(access_token=issue_token(record[0], request.app.state.auth_secret))


@router.get("/companies", tags=["companies"])
def companies(actor: Actor, db: DB) -> list[Company]:
    return db.companies(actor)


@router.get("/companies/{company_id}/employees", tags=["employees"])
def list_employees(
    company_id: UUID,
    actor: Actor,
    db: DB,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Employee]:
    with db.transaction(actor, company_id) as connection:
        if db.membership(connection, company_id) is None:
            raise HTTPException(404, "Không tìm thấy doanh nghiệp.")
        return db.employees(connection, company_id, limit, offset)


@router.get("/companies/{company_id}/employees/{employee_id}", tags=["employees"])
def get_employee(company_id: UUID, employee_id: UUID, actor: Actor, db: DB) -> Employee:
    with db.transaction(actor, company_id) as connection:
        record = db.employee(connection, company_id, employee_id)
        if record is None:
            raise HTTPException(404, "Không tìm thấy hồ sơ nhân viên.")
        return record


@router.patch("/companies/{company_id}/employees/{employee_id}", tags=["employees"])
def edit_employee(
    company_id: UUID,
    employee_id: UUID,
    payload: EditEmployee,
    actor: Actor,
    db: DB,
) -> Employee:
    with db.transaction(actor, company_id) as connection:
        role = db.membership(connection, company_id)
        if role is None:
            raise HTTPException(404, "Không tìm thấy hồ sơ nhân viên.")
        if role != "admin":
            raise HTTPException(403, "Vai trò hiện tại không được sửa hồ sơ.")
        if db.employee(connection, company_id, employee_id) is None:
            raise HTTPException(404, "Không tìm thấy hồ sơ nhân viên.")
        result = db.rename_employee(
            connection,
            company_id,
            actor,
            employee_id,
            payload.display_name,
            payload.expected_revision,
        )
        if result is None:
            raise HTTPException(409, "Hồ sơ đã có phiên bản mới. Hãy tải lại.")
        return result
