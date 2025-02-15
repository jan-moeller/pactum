from inspect import Parameter
from collections.abc import Callable
from pycontractz._capture_set import CaptureSet

type Predicate = Callable[..., bool]
"""A contract predicate is a bool-returning callable"""


def assert_predicate_well_formed(
    pred_params,
    bindings: CaptureSet,
    variables_in_scope: set[str],
):
    """Checks if a precondition predicate is well-formed given a set of bindings, and if those bindings are actually in scope

    Raises a TypeError if the predicate is found to be ill-formed.
    """

    # Check that:
    # - the predicate only has POSITIONAL_OR_KEYWORD parameters
    # - all keyword arguments must be in the set of bindings
    for name, param in pred_params.items():
        match param.kind:
            case Parameter.POSITIONAL_OR_KEYWORD:
                if name not in bindings:
                    raise TypeError(f'Predicate parameter "{name}" not bound')
                if bindings[name] not in variables_in_scope:
                    raise TypeError(f'Predicate parameter "{name}" not in scope')
            case _:
                raise TypeError(
                    f'Predicate parameter "{name}" is of invalid kind {param.kind}'
                )
