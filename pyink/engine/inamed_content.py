from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class INamedContent:
    name: Optional[str] = None
    hasValidName: bool = False
