from pycontractz.contract_violation import ContractViolation
from pycontractz.contract_violation_exception import ContractViolationException


def raising_contract_violation_handler(violation: ContractViolation):
    raise ContractViolationException(violation)
