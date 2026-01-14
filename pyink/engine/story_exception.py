class StoryException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.useEndLineNumber = False
        self.message = message
        self.name = "StoryException"
