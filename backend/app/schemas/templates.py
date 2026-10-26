from pydantic import BaseModel, ConfigDict, Field


class TemplateListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    category: str
    description: str | None
    template_type: str
    preview_image: str | None
    source_url: str
    license: str


class TemplateListResponse(BaseModel):
    items: list[TemplateListItem]
    total: int
    limit: int
    offset: int


class TemplateDetailResponse(TemplateListItem):
    html_content: str | None
    css_content: str | None
    schema_content: str | None


class TemplateQuery(BaseModel):
    category: str | None = Field(default=None, max_length=40)
