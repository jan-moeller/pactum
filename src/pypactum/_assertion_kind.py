from enum import Enum


class AssertionKind(Enum):
    """The kind of contract assertion"""

    pre = 1  # Precondition
    post = 2  # Postcondition
