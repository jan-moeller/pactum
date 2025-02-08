import inspect
from inspect import Parameter
from typing import Any


def map_function_arguments(
    signature: inspect.Signature,
    args: tuple,
    kwargs: dict,
) -> dict[str, Any]:
    """Maps actual function arguments from `args` and `kwargs` to their declared names given `signature`."""

    argsmap = {}

    try:
        i = 0  # next used positional argument index
        has_kwargs = False

        for name, param in signature.parameters.items():
            try:
                match param.kind:
                    case inspect.Parameter.POSITIONAL_ONLY:
                        argsmap[name] = args[i]
                        i += 1
                    case inspect.Parameter.POSITIONAL_OR_KEYWORD:
                        if name in kwargs:
                            argsmap[name] = kwargs[name]
                        else:
                            argsmap[name] = args[i]
                            i += 1
                    case inspect.Parameter.KEYWORD_ONLY:
                        argsmap[name] = kwargs[name]
                    case inspect.Parameter.VAR_POSITIONAL:
                        argsmap[name] = args[i:]
                        i += len(args[i:])
                    case inspect.Parameter.VAR_KEYWORD:
                        has_kwargs = True
                        argsmap[name] = {
                            k: v for k, v in kwargs.items() if k not in argsmap
                        }

            except (KeyError, IndexError):
                # It's okay if there is no argument for a parameter with default value
                if param.default == Parameter.empty:
                    raise

    except Exception as exc:
        raise TypeError("Arguments don't match function signature") from exc

    if i < len(args):
        raise TypeError("Excess positional arguments")
    if not has_kwargs and not all(
        k in signature.parameters.keys() for k in kwargs.keys()
    ):
        raise TypeError("Excess keyword arguments")

    return argsmap
