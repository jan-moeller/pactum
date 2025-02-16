from collections.abc import Callable
from dataclasses import dataclass

from pactum._evaluation_semantic import EvaluationSemantic
from pactum._assertion_kind import AssertionKind


@dataclass
class ContractAssertionInfo:
    """Bundles information about a contract assertion relevant to contract assertion labels"""

    kind: AssertionKind
    module_name: str


type ContractAssertionLabel = Callable[
    [EvaluationSemantic, ContractAssertionInfo], EvaluationSemantic
]
"""A contract assertion label is a function that takes the previous evaluation semantic and information about the 
current contract assertion, and returns a new evaluation semantic.
"""
