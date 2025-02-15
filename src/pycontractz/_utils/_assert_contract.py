import inspect
from typing import Any
from pycontractz._evaluation_semantic import EvaluationSemantic
from pycontractz._assertion_kind import AssertionKind
from pycontractz._contract_violation import ContractViolation
from pycontractz._contract_violation_handler import invoke_contract_violation_handler
from pycontractz._predicate import Predicate


def __handle_contract_violation(
    semantic: EvaluationSemantic,
    kind: AssertionKind,
    location: inspect.Traceback | None,
    comment: str = "",
) -> None:
    """Handles a contract violation by invoking the contract violation handler and/or terminating if required"""

    violation = ContractViolation(
        comment=comment,
        kind=kind,
        location=location,
        semantic=semantic,
    )

    if semantic == EvaluationSemantic.check:
        invoke_contract_violation_handler(violation)


def assert_contract(
    semantic: EvaluationSemantic,
    kind: AssertionKind,
    loc: inspect.Traceback | None,
    predicate: Predicate,
    predicate_kwargs: dict[str, Any],
) -> None:
    """Evaluates the given predicate and handles a contract violation if the result was false"""

    if semantic == EvaluationSemantic.ignore:
        return

    pred_result = predicate(**predicate_kwargs)
    if not pred_result:
        __handle_contract_violation(
            semantic=semantic,
            kind=kind,
            location=loc,
        )
