from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ai_polish_returns_preview_without_accepting_it() -> None:
    response = client.post(
        "/api/ai/polish",
        json={"content": "负责后台系统开发", "instruction": "突出成果"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["accepted"] is False
    assert "负责后台系统开发" in body["preview"]


def test_pdf_render_is_only_a_mock() -> None:
    response = client.post("/api/resume/render", json={"template": "professional"})
    assert response.status_code == 200
    assert response.json()["status"] == "mock"
    assert response.json()["download_url"] is None


def test_otp_placeholder_does_not_return_a_code() -> None:
    response = client.post(
        "/api/auth/phone/send-code",
        json={"phone": "13800138000", "purpose": "login"},
    )
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "SMS_PROVIDER_NOT_CONFIGURED"
    assert "code" not in response.json()
