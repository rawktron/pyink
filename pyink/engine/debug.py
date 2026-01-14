class Debug:
    @staticmethod
    def AssertType(variable, expected_type, message: str):
        Debug.Assert(isinstance(variable, expected_type), message)

    @staticmethod
    def Assert(condition: bool, message: str | None = None):
        if not condition:
            if message is not None:
                print(message)
            raise AssertionError(message or "")
