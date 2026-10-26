from uuid import uuid4

from fastapi import APIRouter

from app.schemas.resume import RenderRequest, RenderResponse


router = APIRouter()


@router.post("/api/resume/render", response_model=RenderResponse)
def render(payload: RenderRequest) -> RenderResponse:
    return RenderResponse(
        job_id=str(uuid4()),
        status="mock",
        format=payload.format,
        download_url=None,
        message="PDF 渲染接口已预留，当前返回 mock 结果",
    )
