from enum import Enum


class DetectionMode(Enum):
    """The mode of detection of a contract violation"""

    implicit = 1  # Violation not due to user-provided predicate
    predicate_false = 2  # A user-provided predicate returned False
    evaluation_exception = 3  # A user provided predicate exited via exception
