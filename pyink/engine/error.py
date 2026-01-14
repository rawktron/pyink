from enum import Enum
from typing import Callable


class ErrorType(Enum):
    Author = 0
    Warning = 1
    Error = 2


ErrorHandler = Callable[[str, ErrorType], None]
