import copy
from types import FrameType
from typing import Any


def __resolve_binding(available_variables: list[dict[str, Any]], name: str) -> Any:
    """Resolves a single binding and returns it. In case of error, raises TypeError."""
    for scope in available_variables:
        if name in scope:
            return scope[name]
    raise TypeError(f'Invalid binding "{name}"')


def resolve_bindings(
    available_variables: list[dict[str, Any]],
    capture: dict[str, str],
    clone: dict[str, str],
) -> dict[str, Any]:
    """Resolves all captures and clones and returns them. In case of error, raises TypeError."""

    referenced = {
        k: __resolve_binding(available_variables, v) for k, v in capture.items()
    }
    cloned = {
        k: copy.deepcopy(__resolve_binding(available_variables, v))
        for k, v in clone.items()
    }
    return referenced | cloned


def collect_available_variables(
    parent_frame: FrameType | None,
    kwargs: dict[str, Any],
) -> list[dict[str, Any]]:
    """Collects a list of all available variables, to be passed to resolve_bindings"""

    candidate_bindings = [kwargs]
    if parent_frame is not None:
        candidate_bindings += [
            parent_frame.f_locals,
            parent_frame.f_globals,
        ]
    return candidate_bindings
