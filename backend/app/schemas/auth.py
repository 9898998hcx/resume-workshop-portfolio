from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SendOtpRequest(BaseModel):
    phone: str = Field(min_length=7, max_length=20)
    purpose: Literal["login", "register", "bind_phone"] = "login"
    captcha_token: str | None = Field(default=None, max_length=500)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        normalized = "".join(ch for ch in value if ch.isdigit() or ch == "+")
        if len(normalized.replace("+", "")) < 7:
            raise ValueError("手机号格式不正确")
        return normalized


class VerifyOtpRequest(BaseModel):
    phone: str = Field(min_length=7, max_length=20)
    purpose: Literal["login", "register", "bind_phone"] = "login"
    code: str = Field(min_length=4, max_length=8)


class PlaceholderResponse(BaseModel):
    status: str
    message: str
