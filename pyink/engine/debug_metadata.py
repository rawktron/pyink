class DebugMetadata:
    def __init__(self):
        self.startLineNumber = 0
        self.endLineNumber = 0
        self.startCharacterNumber = 0
        self.endCharacterNumber = 0
        self.fileName = None
        self.sourceName = None

    def Merge(self, dm: "DebugMetadata"):
        new_debug_metadata = DebugMetadata()

        new_debug_metadata.fileName = self.fileName
        new_debug_metadata.sourceName = self.sourceName

        if self.startLineNumber < dm.startLineNumber:
            new_debug_metadata.startLineNumber = self.startLineNumber
            new_debug_metadata.startCharacterNumber = self.startCharacterNumber
        elif self.startLineNumber > dm.startLineNumber:
            new_debug_metadata.startLineNumber = dm.startLineNumber
            new_debug_metadata.startCharacterNumber = dm.startCharacterNumber
        else:
            new_debug_metadata.startLineNumber = self.startLineNumber
            new_debug_metadata.startCharacterNumber = min(
                self.startCharacterNumber, dm.startCharacterNumber
            )

        if self.endLineNumber > dm.endLineNumber:
            new_debug_metadata.endLineNumber = self.endLineNumber
            new_debug_metadata.endCharacterNumber = self.endCharacterNumber
        elif self.endLineNumber < dm.endLineNumber:
            new_debug_metadata.endLineNumber = dm.endLineNumber
            new_debug_metadata.endCharacterNumber = dm.endCharacterNumber
        else:
            new_debug_metadata.endLineNumber = self.endLineNumber
            new_debug_metadata.endCharacterNumber = max(
                self.endCharacterNumber, dm.endCharacterNumber
            )

        return new_debug_metadata

    def __str__(self):
        if self.fileName is not None:
            return f'line {self.startLineNumber} of {self.fileName}"'
        return f"line {self.startLineNumber}"
