from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.models import ResumeTemplate
from app.db.session import SessionLocal
from app.main import app


client = TestClient(app)


def test_template_list_only_exposes_approved_active_rows() -> None:
    template_id = str(uuid4())
    db = SessionLocal()
    db.add(
        ResumeTemplate(
            id=template_id,
            name="公开模板",
            slug=f"public-{template_id}",
            category="minimal",
            description="测试模板",
            template_type="html_css",
            html_content="<main>private source</main>",
            css_content="main { color: red; }",
            source_url="https://github.com/example/repo/blob/abc/index.html",
            source_path="templates/minimal/index.html",
            source_type="github",
            license="MIT",
            license_url="https://github.com/example/repo/blob/main/LICENSE",
            status="APPROVED",
            is_active=True,
        )
    )
    db.commit()
    try:
        response = client.get("/api/templates?category=minimal")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "公开模板"
        assert "html_content" not in body["items"][0]

        detail = client.get(f"/api/templates/{template_id}")
        assert detail.status_code == 200
        assert detail.json()["html_content"] == "<main>private source</main>"
        assert detail.json()["schema_content"] is None
    finally:
        db.delete(db.get(ResumeTemplate, template_id))
        db.commit()
        db.close()
