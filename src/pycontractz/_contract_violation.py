import inspect

from pycontractz._assertion_kind import AssertionKind
from pycontractz._evaluation_semantic import EvaluationSemantic


class ContractViolation:
    """Holds information about a contract violation"""

    __kind_strings = [None, "Precondition", "Postcondition", "Assertion"]

    def __init__(
        self,
        comment: str,
        kind: AssertionKind,
        location: inspect.Traceback | None,
        semantic: EvaluationSemantic,
    ):
        self.comment = comment
        self.kind = kind
        self.location = location
        self.semantic = semantic

    def __str__(self) -> str:
        kind = ContractViolation.__kind_strings[self.kind.value]
        loc = (
            f"{self.location.filename}:{self.location.lineno}"
            if self.location is not None
            else ""
        )
        diagnostic = f"{kind} violation at {loc}"
        if len(self.comment) > 0:
            diagnostic += f": {self.comment}"
        if (
            self.location is not None
            and self.location.code_context is not None
            and len(self.location.code_context) > 0
        ):
            diagnostic += f"\nContext:\n{'\n'.join(self.location.code_context)}"
        return diagnostic
