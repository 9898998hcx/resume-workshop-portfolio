from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import AiJob
from app.db.session import get_db
from app.providers.ai import MockAIProvider
from app.schemas.ai import PolishRequest, PolishResponse


router = APIRouter()


@router.post("/api/ai/polish", response_model=PolishResponse)
def polish(payload: PolishRequest, db: Session = Depends(get_db)) -> PolishResponse:
    provider = MockAIProvider()
    job_id = str(uuid4())
    now = datetime.utcnow()
    job = AiJob(
        id=job_id,
        user_id=None,
        resume_id=payload.resume_id,
        job_type="POLISH",
        status="SUCCEEDED",
        provider=provider.name,
        input_summary=f"content_length={len(payload.content)}; instruction_present={bool(payload.instruction)}",
        output_summary="mock_preview_generated",
        estimated_tokens=max(1, len(payload.content) // 4),
        started_at=now,
        finished_at=now,
    )
    db.add(job)
    db.commit()
    return PolishResponse(
        job_id=job_id,
        status="succeeded",
        provider=provider.name,
        preview=provider.polish(payload.content, payload.instruction),
        accepted=False,
    )
