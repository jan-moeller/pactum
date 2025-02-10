from collections.abc import Callable
from contextlib import ContextDecorator

from pycontractz.assertion_kind import AssertionKind
from pycontractz.contract_violation import ContractViolation
from pycontractz.evaluation_semantic import EvaluationSemantic
from pycontractz.default_contract_violation_handler import (
    default_contract_violation_handler,
)

__contract_violation_handler = default_contract_violation_handler
__assertion_semantics = {k: EvaluationSemantic.check for k in AssertionKind}


def invoke_contract_violation_handler(violation: ContractViolation):
    """Invokes the current contract violation handler"""
    __contract_violation_handler(violation)


def set_contract_violation_handler(handler: Callable[[ContractViolation], None]):
    """Replaces the contract violation handler"""
    global __contract_violation_handler
    __contract_violation_handler = handler


def get_contract_violation_handler() -> Callable[[ContractViolation], None]:
    """Retrieves the current contract violation handler"""
    return __contract_violation_handler


def set_contract_evaluation_semantics(
    default: EvaluationSemantic | dict[AssertionKind, EvaluationSemantic] | None = None,
    pre: EvaluationSemantic | None = None,
    post: EvaluationSemantic | None = None,
):
    """Changes the current contract evaluation semantics per kind"""
    global __assertion_semantics

    if default is None:
        default = __assertion_semantics
    if isinstance(default, EvaluationSemantic):
        default = {k: default for k in AssertionKind}
    if pre is None:
        pre = default[AssertionKind.pre]
    if post is None:
        post = default[AssertionKind.post]

    __assertion_semantics[AssertionKind.pre] = pre
    __assertion_semantics[AssertionKind.post] = post


def get_contract_evaluation_semantic(
    kind: AssertionKind | None = None,
) -> EvaluationSemantic | dict[AssertionKind, EvaluationSemantic]:
    """Retrieves the currently configured contract evaluation semantics per kind"""
    if kind is None:
        return __assertion_semantics
    return __assertion_semantics[kind]


class contract_violation_handler(ContextDecorator):
    """Context manager to temporarily change the contract violation handler. Usable as decorator as well."""

    def __init__(self, handler: Callable[[ContractViolation], None]):
        self.handler = handler

    def __enter__(self):
        self.old_handler = get_contract_violation_handler()
        set_contract_violation_handler(self.handler)
        return self

    def __exit__(self, *exc):
        set_contract_violation_handler(self.old_handler)
        return False


class contract_evaluation_semantics(ContextDecorator):
    """Context manager to temporarily change the evaluation semantics. Usable as a decorator as well."""

    def __init__(
        self,
        default: EvaluationSemantic | None = None,
        pre: EvaluationSemantic | None = None,
        post: EvaluationSemantic | None = None,
        assertion: EvaluationSemantic | None = None,
    ):
        self.default = default
        self.pre = pre
        self.post = post
        self.assertion = assertion

    def __enter__(self):
        self.old_semantics = get_contract_evaluation_semantic()
        set_contract_evaluation_semantics(
            default=self.default, pre=self.pre, post=self.post, assertion=self.assertion
        )
        return self

    def __exit__(self, *exc):
        set_contract_evaluation_semantics(self.old_semantics)
        return False
