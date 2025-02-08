from enum import Enum


class EvaluationSemantic(Enum):
    """The semantic with which to evaluate a contract assertion"""

    ignore = 1  # On contract violation, the contract violation handler is never called
    check = 2  # On contract violation, the contract violation handler is called, and if it returns, the program continues
