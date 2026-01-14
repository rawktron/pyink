from __future__ import annotations

from pathlib import Path

import pytest

from pyink import Story
from pyink.engine.container import Container
from pyink.engine.divert import Divert
from pyink.engine.error import ErrorType
from pyink.engine.object import InkObject


ROOT = Path(__file__).resolve().parent
INKFILES_DIR = ROOT / "inkfiles" / "compiled"


def iter_compiled_inkfiles():
    for path in INKFILES_DIR.rglob("*.ink.json"):
        rel = path.relative_to(INKFILES_DIR)
        yield rel


def collect_external_names(obj, names):
    if isinstance(obj, Container):
        for inner_content in obj.content:
            container = inner_content if isinstance(inner_content, Container) else None
            if container is None or not container.hasValidName:
                collect_external_names(inner_content, names)
        for value in obj.namedContent.values():
            if isinstance(value, InkObject):
                collect_external_names(value, names)
        return

    divert = obj if isinstance(obj, Divert) else None
    if divert and divert.isExternal and divert.targetPathString is not None:
        names.add(divert.targetPathString)


@pytest.mark.parametrize("rel_path", list(iter_compiled_inkfiles()))
def test_compiled_story_runs_without_errors(rel_path):
    text = (INKFILES_DIR / rel_path).read_text(encoding="utf-8-sig")
    errors = []

    def on_error(message, error_type):
        if error_type == ErrorType.Error:
            errors.append(message)

    story = Story(text)
    story.onError = on_error
    external_names = set()
    collect_external_names(story._mainContentContainer, external_names)
    for name in sorted(external_names):
        story.BindExternalFunction(name, lambda *args: 0, True)

    max_steps = 20000
    steps = 0

    while steps < max_steps:
        while story.canContinue and steps < max_steps:
            story.Continue()
            steps += 1
        if story.currentChoices:
            story.ChooseChoiceIndex(0)
            continue
        break

    assert not errors, f"{rel_path} errors: {errors}"
