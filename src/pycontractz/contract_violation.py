import inspect
import traceback

from pycontractz.assertion_kind import AssertionKind
from pycontractz.detection_mode import DetectionMode
from pycontractz.evaluation_semantic import EvaluationSemantic


class ContractViolation:
    """Holds information about a contract violation"""

    __kind_strings = [None, "Precondition", "Postcondition", "Assertion"]

    def __init__(
        self,
        comment: str,
        detection_mode: DetectionMode,
        evaluation_exception: Exception | None,
        kind: AssertionKind,
        location: inspect.Traceback,
        semantic: EvaluationSemantic,
    ):
        self.comment = comment
        self.detection_mode = detection_mode
        self.evaluation_exception = evaluation_exception
        self.is_terminating = semantic in [
            EvaluationSemantic.enforce,
            EvaluationSemantic.quick_enforce,
        ]
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
        if self.evaluation_exception is not None:
            exc_str = "\n".join(traceback.format_exception(self.evaluation_exception))
            diagnostic += (
                f"\nDue to exception escaped from contract predicate:\n{exc_str}"
            )
        if self.is_terminating:
            diagnostic += f"\nThis contract violation is unrecoverable."
        return diagnostic
