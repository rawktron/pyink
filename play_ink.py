#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from pyink import Story


def play_story(json_path: Path):
    text = json_path.read_text(encoding="utf-8-sig")
    story = Story(text)

    print("--- Story start ---")
    while True:
        while story.canContinue:
            print(story.Continue(), end="")

        choices = story.currentChoices
        if not choices:
            break

        print("\nChoices:")
        for idx, choice in enumerate(choices, start=1):
            print(f"  {idx}) {choice.text}")

        while True:
            selection = input("\nChoose 1-{0} (or 'q' to quit): ".format(len(choices))).strip()
            if selection.lower() in {"q", "quit", "exit"}:
                print("\n--- Quit ---")
                return
            if selection.isdigit():
                choice_index = int(selection) - 1
                if 0 <= choice_index < len(choices):
                    story.ChooseChoiceIndex(choice_index)
                    break
            print("Invalid choice. Try again.")

    print("\n--- The End ---")


def main():
    parser = argparse.ArgumentParser(description="Play a compiled Ink JSON story")
    parser.add_argument("json_path", type=Path, help="Path to compiled .ink.json")
    args = parser.parse_args()

    if not args.json_path.exists():
        raise SystemExit(f"File not found: {args.json_path}")

    play_story(args.json_path)


if __name__ == "__main__":
    main()
