import sys

from pycontractz._contract_violation import ContractViolation


def default_contract_violation_handler(violation: ContractViolation):
    print(violation, file=sys.stderr)
