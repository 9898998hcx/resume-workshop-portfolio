class MockSMSProvider:
    name = "mock"

    def send_code(self, phone: str, code: str, purpose: str) -> None:
        # Deliberately do not print the phone number or the code.
        return None
