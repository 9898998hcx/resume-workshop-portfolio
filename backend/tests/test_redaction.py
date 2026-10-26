from app.core.redaction import mask_email, mask_phone, redact_text


def test_sensitive_values_are_redacted() -> None:
    assert mask_phone("13800138000") == "138****8000"
    assert mask_email("person@example.com") == "p***@example.com"
    redacted = redact_text("person@example.com 13800138000 sk-secret-value-1234")
    assert "person@example.com" not in redacted
    assert "13800138000" not in redacted
    assert "sk-secret-value-1234" not in redacted
