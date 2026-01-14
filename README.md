# Pyink

Python runtime for ink (ported from inkjs) that loads compiled `.ink.json` files and plays them in pure Python.

## Table of contents

- [Installation](#installation)
- [Quickstart](#quickstart)
- [Working with a JSON file](#working-with-a-json-file)
- [CLI player](#cli-player)
- [External functions](#external-functions)
- [Tests](#tests)
- [License](#license)

## Installation

This repo is currently a source checkout. There is no packaged release yet.

Dependencies:
- Runtime: none
- Tests: `pytest`

## Quickstart

```python
from pathlib import Path
from pyink import Story

story_json = Path("path/to/story.ink.json").read_text(encoding="utf-8-sig")
story = Story(story_json)

print(story.ContinueMaximally())
```

## Working with a JSON file

Pyink runs compiled ink JSON output (from `inklecate` or the official ink compiler).

If you load from disk, make sure to strip the BOM or read with `utf-8-sig`:

```python
from pathlib import Path
from pyink import Story

text = Path("story.ink.json").read_text(encoding="utf-8-sig")
story = Story(text)
```

## CLI player

A simple CLI player is included:

```bash
python play_ink.py path/to/story.ink.json
```

It prints output, lists choices, and lets you pick by number.

## External functions

You can bind external functions via `BindExternalFunction`:

```python
story.BindExternalFunction("message", lambda arg: print("MESSAGE:", arg))
```

If you need the text output from a function call, use `EvaluateFunction(..., True)`:

```python
result = story.EvaluateFunction("my_func", [1, 2], True)
# result == {"returned": <value>, "output": "text\n"}
```

## Tests

```bash
pytest -q
```

## License

MIT. See `LICENSE`.
