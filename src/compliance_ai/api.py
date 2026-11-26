from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from compliance_ai.config import Settings, auth_secret
from compliance_ai.db import Database
from compliance_ai.tenant_api import router
from compliance_ai.workflow_api import router as workflow_router


class Health(BaseModel):
    status: Literal["ok"] = "ok"
    execution_mode: Literal["SIMULATION"] = "SIMULATION"


def create_app() -> FastAPI:
    settings = Settings.load()
    app = FastAPI(title="Trợ lý đánh giá an toàn thông tin", version="0.1.0")

    @app.get("/health", tags=["health"])
    def health() -> Health:
        return Health(execution_mode=settings.execution_mode)

    db = Database(settings.database_url) if settings.database_url else None
    app.state.db = db
    if db is not None:
        app.state.auth_secret = auth_secret()
    app.include_router(router)
    app.include_router(workflow_router)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {"loc": item["loc"], "type": item["type"], "msg": "Dữ liệu không hợp lệ."}
                    for item in error.errors()
                ],
            },
        )

    @app.get("/ready", tags=["health"])
    def ready() -> Health:
        try:
            available = db is not None and db.ready()
        except SQLAlchemyError:
            available = False
        if not available:
            raise HTTPException(503, "Cơ sở dữ liệu chưa sẵn sàng.")
        return Health(execution_mode=settings.execution_mode)

    return app
