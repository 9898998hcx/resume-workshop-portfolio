from typing import Protocol


class SMSProvider(Protocol):
    name: str

    def send_code(self, phone: str, code: str, purpose: str) -> None:
        ...
