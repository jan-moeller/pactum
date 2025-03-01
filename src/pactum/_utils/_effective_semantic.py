import inspect
from types import FrameType

from pactum._contract_violation_handler import get_contract_evaluation_semantic
from pactum._assertion_kind import AssertionKind
from pactum._contract_assertion_label import (
    ContractAssertionInfo,
    ContractAssertionLabel,
)
from pactum._evaluation_semantic import EvaluationSemantic


def effective_semantic(
    parent_frame: FrameType | None,
    kind: AssertionKind,
    labels: list[ContractAssertionLabel],
) -> EvaluationSemantic:
    """Computes the effective semantic of a specific contract assertion"""

    module = inspect.getmodule(parent_frame)
    info = ContractAssertionInfo(
        kind=kind,
        module_name=module.__name__ if module is not None else "",
    )
    semantic: EvaluationSemantic = get_contract_evaluation_semantic(info)
    for label in labels:
        semantic = label(semantic, info)

    return semantic
