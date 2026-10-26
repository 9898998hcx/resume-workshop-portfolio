from time import perf_counter

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.session import check_connection, database_kind, get_db
from app.schemas.common import DatabaseHealthResponse, HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="resume-workshop-api")


@router.get("/api/health/db", response_model=DatabaseHealthResponse)
def database_health(_: Session = Depends(get_db)) -> DatabaseHealthResponse:
    started = perf_counter()
    try:
        check_connection()
    except SQLAlchemyError as exc:
        raise ApiError(503, "DB_UNAVAILABLE", "数据库暂时不可用") from exc
    elapsed = max(0, int((perf_counter() - started) * 1000))
    return DatabaseHealthResponse(status="ok", database=database_kind(), latency_ms=elapsed)
