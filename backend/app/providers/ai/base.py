from typing import Protocol


class AIProvider(Protocol):
    name: str

    def polish(self, content: str, instruction: str | None = None) -> str:
        ...
