from contextlib import ContextDecorator
from types import TracebackType
from typing import Self, Literal

from pactum._contract_violation import ContractViolation
from pactum._evaluation_semantic import EvaluationSemantic
from pactum._contract_assertion_label import (
    ContractAssertionLabel,
    ContractAssertionInfo,
)
from pactum.handlers import raise_on_contract_violation, ContractViolationHandler

__contract_violation_handler: ContractViolationHandler = raise_on_contract_violation
__global_evaluation_semantic: EvaluationSemantic = EvaluationSemantic.check
__global_contract_assertion_label: ContractAssertionLabel = lambda sem, info: sem


def invoke_contract_violation_handler(violation: ContractViolation) -> None:
    """Invokes the current contract violation handler"""
    __contract_violation_handler(violation)


def set_contract_violation_handler(handler: ContractViolationHandler) -> None:
    """Replaces the contract violation handler"""
    global __contract_violation_handler
    __contract_violation_handler = handler


def get_contract_violation_handler() -> ContractViolationHandler:
    """Retrieves the current contract violation handler"""
    return __contract_violation_handler


def set_contract_evaluation_semantic(semantic: EvaluationSemantic) -> None:
    """Changes the current contract evaluation semantic"""
    global __global_evaluation_semantic
    __global_evaluation_semantic = semantic


def get_contract_evaluation_semantic(
    info: ContractAssertionInfo | None = None,
) -> EvaluationSemantic:
    """Retrieves the currently configured contract evaluation semantic"""

    if info is None:
        return __global_evaluation_semantic
    return __global_contract_assertion_label(__global_evaluation_semantic, info)


def set_global_contract_assertion_label(label: ContractAssertionLabel) -> None:
    """Changes the current global label, influencing the evaluation semantics"""
    global __global_contract_assertion_label
    __global_contract_assertion_label = label


def get_global_contract_assertion_label() -> ContractAssertionLabel:
    """Retrieves the current global label"""
    return __global_contract_assertion_label


class contract_violation_handler(ContextDecorator):
    """Context manager to temporarily change the contract violation handler. Usable as decorator as well."""

    def __init__(self, handler: ContractViolationHandler):
        self.handler = handler

    def __enter__(self) -> Self:
        self.old_handler = get_contract_violation_handler()
        set_contract_violation_handler(self.handler)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        set_contract_violation_handler(self.old_handler)
        return False


class contract_evaluation_semantic(ContextDecorator):
    """Context manager to temporarily change the evaluation semantic. Usable as a decorator as well."""

    def __init__(
        self,
        semantic: EvaluationSemantic,
    ):
        self.semantic = semantic

    def __enter__(self) -> Self:
        self.old_semantic = get_contract_evaluation_semantic()
        set_contract_evaluation_semantic(self.semantic)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        set_contract_evaluation_semantic(self.old_semantic)
        return False


class global_contract_assertion_label(ContextDecorator):
    """Context manager to temporarily change the global contract assertion label. Usable as a decorator as well."""

    def __init__(
        self,
        label: ContractAssertionLabel,
    ):
        self.label = label

    def __enter__(self) -> Self:
        self.old_label = get_global_contract_assertion_label()
        set_global_contract_assertion_label(self.label)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        set_global_contract_assertion_label(self.old_label)
        return False
