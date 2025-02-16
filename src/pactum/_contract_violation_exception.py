from pactum._contract_violation import ContractViolation


class ContractViolationException(Exception):
    """Exception to raise in case of contract violation"""

    def __init__(self, violation: ContractViolation):
        self.violation = violation
