import sys
import logging
from collections.abc import Callable
from io import TextIOWrapper
from typing import TextIO

from pycontractz._contract_violation import ContractViolation
from pycontractz._contract_violation_exception import ContractViolationException

type ContractViolationHandler = Callable[[ContractViolation], None]

def raise_on_contract_violation(violation: ContractViolation):
    """A contract violation handler that raises a ContractViolationException"""
    raise ContractViolationException(violation)


def log_on_contract_violation(
    target: logging.Logger | TextIO | TextIOWrapper = None,
):
    """A factory for contract violation handlers that log the violation

    Keyword arguments:
        target: Either a TextIO sink like stderr (the default), or a logger object
    """
    if target is None:
        target = sys.stderr

    match target:
        case TextIO() | TextIOWrapper() as file:

            def handler(violation: ContractViolation):
                print(str(violation), file=file)

            return handler

        case logging.Logger() as log:

            def handler(violation: ContractViolation):
                log.error(str(violation))

            return handler

        case _:
            raise TypeError("Invalid logging target")
