class MockAIProvider:
    name = "mock"

    def polish(self, content: str, instruction: str | None = None) -> str:
        suffix = f"（按“{instruction}”优化）" if instruction else ""
        return f"（Mock 预览）{content.strip()}{suffix}"
