import inspect
from typing import Any


def map_function_arguments(
    signature: inspect.Signature,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Maps actual function arguments from `args` and `kwargs` to their declared names given `signature`."""

    bound_args = signature.bind(*args, **kwargs)
    bound_args.apply_defaults()
    return dict(bound_args.arguments)
