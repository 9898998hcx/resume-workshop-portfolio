from fastapi import APIRouter

from app.core.errors import ApiError
from app.schemas.auth import PlaceholderResponse, SendOtpRequest, VerifyOtpRequest


router = APIRouter()


@router.post("/api/auth/phone/send-code", response_model=PlaceholderResponse)
def send_code(_: SendOtpRequest) -> PlaceholderResponse:
    raise ApiError(501, "SMS_PROVIDER_NOT_CONFIGURED", "短信服务尚未配置")


@router.post("/api/auth/phone/verify-code", response_model=PlaceholderResponse)
def verify_code(_: VerifyOtpRequest) -> PlaceholderResponse:
    raise ApiError(501, "OTP_NOT_ENABLED", "手机号登录尚未启用")
