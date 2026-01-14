from .object import InkObject


class Tag(InkObject):
    def __init__(self, tag_text: str):
        super().__init__()
        self.text = str(tag_text) if tag_text is not None else ""

    def __str__(self):
        return "# " + self.text
