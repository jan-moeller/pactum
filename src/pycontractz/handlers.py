import sys

from pycontractz._contract_violation import ContractViolation
from pycontractz._contract_violation_exception import ContractViolationException


def raise_on_contract_violation(violation: ContractViolation):
    """A contract violation handler that raises a ContractViolationException"""
    raise ContractViolationException(violation)


def log_to_stderr_on_contract_violation(violation: ContractViolation):
    """A contract violation handler that prints the violation to stderr"""
    print(violation, file=sys.stderr)
