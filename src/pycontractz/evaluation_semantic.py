from enum import Enum


class EvaluationSemantic(Enum):
    """The semantic with which to evaluate a contract assertion"""

    ignore = 1  # On contract violation, the contract violation handler is never called
    observe = 2  # On contract violation, the contract violation handler is called, and if it returns, the program continues
    enforce = 3  # On contract violation, the contract violation handler is called, and if it returns, the program exits
    quick_enforce = 4  # On contract violation, the contract violation handler is not called and the program exits immediately
