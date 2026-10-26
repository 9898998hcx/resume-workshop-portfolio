from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.models import ResumeTemplate
from app.db.session import get_db
from app.schemas.templates import TemplateDetailResponse, TemplateListItem, TemplateListResponse


router = APIRouter()


def _public_conditions(category: str | None):
    conditions = [
        ResumeTemplate.status == "APPROVED",
        ResumeTemplate.is_active.is_(True),
    ]
    if category:
        conditions.append(ResumeTemplate.category == category)
    return conditions


@router.get("/api/templates", response_model=TemplateListResponse)
def list_templates(
    category: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> TemplateListResponse:
    conditions = _public_conditions(category)
    try:
        total = int(db.scalar(select(func.count()).select_from(ResumeTemplate).where(*conditions)) or 0)
        rows = db.scalars(
            select(ResumeTemplate)
            .where(*conditions)
            .order_by(ResumeTemplate.created_at.desc(), ResumeTemplate.name.asc())
            .offset(offset)
            .limit(limit)
        ).all()
    except SQLAlchemyError as exc:
        raise ApiError(503, "DB_UNAVAILABLE", "模板库暂时不可用") from exc
    return TemplateListResponse(
        items=[TemplateListItem.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/api/templates/{template_id}", response_model=TemplateDetailResponse)
def get_template(template_id: str, db: Session = Depends(get_db)) -> TemplateDetailResponse:
    try:
        row = db.scalar(
            select(ResumeTemplate).where(
                ResumeTemplate.id == template_id,
                ResumeTemplate.status == "APPROVED",
                ResumeTemplate.is_active.is_(True),
            )
        )
    except SQLAlchemyError as exc:
        raise ApiError(503, "DB_UNAVAILABLE", "模板库暂时不可用") from exc
    if row is None:
        raise ApiError(404, "TEMPLATE_NOT_FOUND", "模板不存在或尚未公开")
    return TemplateDetailResponse(
        id=row.id,
        name=row.name,
        slug=row.slug,
        category=row.category,
        description=row.description,
        template_type=row.template_type,
        preview_image=row.preview_image,
        source_url=row.source_url,
        license=row.license,
        html_content=row.html_content,
        css_content=row.css_content,
        schema_content=row.schema_json,
    )
