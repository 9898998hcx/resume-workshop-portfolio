from typing import Protocol


class CaptchaVerifier(Protocol):
    name: str

    def verify(self, token: str | None, remote_ip: str | None = None) -> bool:
        ...
