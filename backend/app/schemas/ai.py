from pydantic import BaseModel, Field


class PolishRequest(BaseModel):
    resume_id: str | None = Field(default=None, max_length=36)
    content: str = Field(min_length=1, max_length=20_000)
    instruction: str | None = Field(default=None, max_length=1_000)


class PolishResponse(BaseModel):
    job_id: str
    status: str
    provider: str
    preview: str
    accepted: bool
