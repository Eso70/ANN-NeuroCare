from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import ApiInfo, DatabaseHealthResponse, HealthResponse
from app.services.health import database_is_ready

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/health/db", response_model=DatabaseHealthResponse)
def database_health(db: Annotated[Session, Depends(get_db)]) -> DatabaseHealthResponse:
    if not database_is_ready(db):
        raise RuntimeError("Database health probe failed")
    return DatabaseHealthResponse()


@router.get("/v1/", response_model=ApiInfo)
def api_info() -> ApiInfo:
    return ApiInfo()
