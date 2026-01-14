from .object import InkObject


class VariableAssignment(InkObject):
    def __init__(self, variable_name: str | None, is_new_declaration: bool):
        super().__init__()
        self.variableName = variable_name or None
        self.isNewDeclaration = bool(is_new_declaration)
        self.isGlobal = False

    def __str__(self):
        return "VarAssign to " + str(self.variableName)
