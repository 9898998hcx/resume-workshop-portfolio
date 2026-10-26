class MockCaptchaVerifier:
    name = "mock"

    def verify(self, token: str | None, remote_ip: str | None = None) -> bool:
        return token in {None, "mock-valid"}
