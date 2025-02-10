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
    capture: set[str],
    clone: set[str],
) -> dict[str, Any]:
    """Resolves all captures and clones and returns them. In case of error, raises ValueError."""

    referenced = {n: __resolve_binding(candidates, n) for n in capture}
    cloned = {n: copy.deepcopy(__resolve_binding(candidates, n)) for n in clone}
    return referenced | cloned
