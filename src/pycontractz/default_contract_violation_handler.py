import sys

from pycontractz.contract_violation import ContractViolation


def default_contract_violation_handler(violation: ContractViolation):
    print(violation, file=sys.stderr)
