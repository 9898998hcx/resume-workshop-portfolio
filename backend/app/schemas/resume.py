from typing import Literal

from pydantic import BaseModel, Field


class RenderRequest(BaseModel):
    resume_id: str | None = Field(default=None, max_length=36)
    template: str = Field(default="professional", min_length=1, max_length=80)
    format: Literal["pdf"] = "pdf"


class RenderResponse(BaseModel):
    job_id: str
    status: str
    format: str
    download_url: str | None
    message: str
