import inspect

from pycontractz.assertion_kind import AssertionKind
from pycontractz.evaluation_semantic import EvaluationSemantic


class ContractViolation:
    """Holds information about a contract violation"""

    __kind_strings = [None, "Precondition", "Postcondition", "Assertion"]

    def __init__(
        self,
        comment: str,
        kind: AssertionKind,
        location: inspect.Traceback,
        semantic: EvaluationSemantic,
    ):
        self.comment = comment
        self.kind = kind
        self.location = location
        self.semantic = semantic

    def __str__(self):
        kind = ContractViolation.__kind_strings[self.kind.value]
        loc = f"{self.location.filename}:{self.location.lineno}"
        diagnostic = f"{kind} violation at {loc}"
        if len(self.comment) > 0:
            diagnostic += f": {self.comment}"
        if len(self.location.code_context) > 0:
            diagnostic += f"\nContext:\n{'\n'.join(self.location.code_context)}"
        return diagnostic
