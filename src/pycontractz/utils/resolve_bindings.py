import copy
from typing import Any


def __resolve_binding(candidates: list[dict[str, Any]], name: str) -> Any:
    """Resolves a single binding and returns it. In case of error, raises ValueError."""
    for scope in candidates:
        if name in scope:
            return scope[name]
    raise ValueError(f'Invalid binding "{name}"')


def resolve_bindings(
    candidates: list[dict[str, Any]],
    capture: dict[str, str],
    clone: dict[str, str],
) -> dict[str, Any]:
    """Resolves all captures and clones and returns them. In case of error, raises ValueError."""

    referenced = {k: __resolve_binding(candidates, v) for k, v in capture.items()}
    cloned = {
        k: copy.deepcopy(__resolve_binding(candidates, v)) for k, v in clone.items()
    }
    return referenced | cloned
