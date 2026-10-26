from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ai, auth, health, resume, templates
from app.core.config import get_settings
from app.core.errors import (
    ApiError,
    api_error_handler,
    unexpected_error_handler,
    validation_error_handler,
)


settings = get_settings()

app = FastAPI(
    title="简历工坊 API",
    version="0.1.0",
    description="阶段一 FastAPI、数据库和健康检查基础服务",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unexpected_error_handler)

app.include_router(health.router)
app.include_router(ai.router)
app.include_router(resume.router)
app.include_router(auth.router)
app.include_router(templates.router)
