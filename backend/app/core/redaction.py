import re


_EMAIL = re.compile(r"([A-Za-z0-9])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+)")
_PHONE = re.compile(r"(?<!\d)(1\d{2})\d{4}(\d{4})(?!\d)")
_API_KEY = re.compile(r"\b(sk-[A-Za-z0-9_-]{6,})\b")


def mask_email(value: str) -> str:
    return _EMAIL.sub(r"\1***\2", value)


def mask_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) < 7:
        return "***"
    return f"{digits[:3]}****{digits[-4:]}"


def redact_text(value: str) -> str:
    value = _EMAIL.sub(r"\1***\2", value)
    value = _PHONE.sub(r"\1****\2", value)
    return _API_KEY.sub("sk-****", value)
