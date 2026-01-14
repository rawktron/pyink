class StringBuilder:
    def __init__(self, str_value: str | None = None):
        self._string = str(str_value) if str_value is not None else ""

    @property
    def Length(self) -> int:
        return len(self._string)

    def Append(self, str_value: str | None):
        if str_value is not None:
            self._string += str_value

    def AppendLine(self, str_value: str | None = None):
        if str_value is not None:
            self.Append(str_value)
        self._string += "\n"

    def AppendFormat(self, format_str: str, *args):
        def repl(match):
            num = int(match.group(1))
            return str(args[num]) if num < len(args) else match.group(0)

        import re

        self._string += re.sub(r"{(\d+)}", repl, format_str)

    def __str__(self):
        return self._string

    def Clear(self):
        self._string = ""
