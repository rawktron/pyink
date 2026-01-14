from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pyink import Story
from pyink.engine.error import ErrorType

ROOT = Path(__file__).resolve().parent
INKFILES_DIR = ROOT / "inkfiles" / "compiled"


def load_json_file(filename: str, category: str | None):
    if category:
        file_path = INKFILES_DIR / category / f"{filename}.ink.json"
    else:
        file_path = INKFILES_DIR / f"{filename}.ink.json"
    return file_path.read_text(encoding="utf-8-sig")


@dataclass
class TestContext:
    testing_errors: bool = False
    story: Story | None = None
    bytecode: str | None = None
    error_messages: list[str] = field(default_factory=list)
    warning_messages: list[str] = field(default_factory=list)
    author_messages: list[str] = field(default_factory=list)

    def on_error(self, message: str, error_type: ErrorType):
        if not self.testing_errors:
            return
        if error_type == ErrorType.Error:
            self.error_messages.append(message)
        elif error_type == ErrorType.Warning:
            self.warning_messages.append(message)
        else:
            self.author_messages.append(message)


def from_json_test_context(name: str, category: str | None, testing_errors: bool = False):
    context = TestContext(testing_errors=testing_errors)
    json_content = load_json_file(name, category)
    context.story = Story(json_content)
    if testing_errors:
        context.story.onError = context.on_error
    context.bytecode = context.story.ToJson()
    return context
