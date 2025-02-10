import copy
import inspect
from functools import wraps
from inspect import Parameter
from typing import Any

from pycontractz.evaluation_semantic import EvaluationSemantic
from pycontractz.assertion_kind import AssertionKind
from pycontractz.contract_violation import ContractViolation
from pycontractz.contract_violation_handler import (
    get_contract_evaluation_semantic,
    invoke_contract_violation_handler,
)
from pycontractz.utils.find_outer_stack_frame import find_outer_stack_frame
from pycontractz.utils.map_function_arguments import map_function_arguments


def __resolve_binding(candidates: list[dict[str, Any]], name: str) -> Any:
    """Resolves a single binding and returns it. In case of error, raises ValueError."""
    for scope in candidates:
        if name in scope:
            return scope[name]
    raise ValueError(f'Invalid binding "{name}"')


def __resolve_bindings(
    candidates: list[dict[str, Any]],
    capture: set[str],
    clone: set[str],
) -> dict[str, Any]:
    """Resolves all captures and clones and returns them. In case of error, raises ValueError."""

    referenced = {n: __resolve_binding(candidates, n) for n in capture}
    cloned = {n: copy.deepcopy(__resolve_binding(candidates, n)) for n in clone}
    return referenced | cloned


def __call_predicate(
    predicate,
    args: tuple,
    kwargs: dict,
) -> bool:
    """Calls the given predicate given some arguments and returns whether the result was truthy

    `args` and `kwargs` are assumed to be the output of `__promote_positional_arguments_to_keyword_arguments`.
    """

    reduced_kwargs = {}

    sig = inspect.signature(predicate)
    has_variadic_positional = False
    has_variadic_keyword = False
    for name, param in sig.parameters.items():
        match param.kind:
            case Parameter.VAR_POSITIONAL:
                has_variadic_positional = True
            case Parameter.VAR_KEYWORD:
                has_variadic_keyword = True
            case _:
                reduced_kwargs[name] = kwargs[name]

    if has_variadic_positional and has_variadic_keyword:
        return bool(predicate(*args, **kwargs))
    elif has_variadic_positional:
        return bool(predicate(*args, **reduced_kwargs))
    elif has_variadic_keyword:
        return bool(predicate(**kwargs))
    return bool(predicate(**reduced_kwargs))


def __handle_contract_violation(
    semantic: EvaluationSemantic,
    kind: AssertionKind,
    location: inspect.Traceback,
    comment: str = "",
):
    """Handles a contract violation by invoking the contract violation handler and/or terminating if required"""

    if semantic == EvaluationSemantic.ignore:
        return

    violation = ContractViolation(
        comment=comment,
        kind=kind,
        location=location,
        semantic=semantic,
    )

    if semantic == EvaluationSemantic.check:
        invoke_contract_violation_handler(violation)


def __assert_contract(
    semantic: EvaluationSemantic,
    kind: AssertionKind,
    loc: inspect.Traceback,
    predicate,
    predicate_kwargs: dict[str, Any],
):
    """Evaluates the given predicate and handles a contract violation if the result was false"""

    pred_result = predicate(**predicate_kwargs)
    if not pred_result:
        __handle_contract_violation(
            semantic=semantic,
            kind=kind,
            location=loc,
        )


def __assert_predicate_well_formed(
    pred_params,
    bindings: set[str],
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
                if not name in bindings:
                    raise TypeError(f'Predicate parameter "{name}" not bound')
                if not name in variables_in_scope:
                    raise TypeError(f'Predicate parameter "{name}" not in scope')
            case _:
                raise TypeError(
                    f'Predicate parameter "{name}" is of invalid kind {param.kind}'
                )


def pre(
    predicate,
    capture: set[str] = None,
    clone: set[str] = None,
):
    """Precondition assertion decorator factory taking a predicate to evaluate on function evaluation

    Keyword arguments:
        predicate: A callable evaluating the predicate to check before function evaluation
        capture: A set of names to capture. Variables by this name can be predicate parameters
        clone: A set of names to clone. Variables by this name can be predicate parameters

    Note that the wrapped function's arguments are implicitly captured.

    Returns:
        - The returned decorator raises TypeError if the predicate is malformed.
        - Otherwise:

          - if the current contract evaluation semantic is not `ignore`, returns a wrapper of the decorated function that
            checks the predicate before evaluating the original function.
          - if the current contract evaluation semantic is `ignore`, returns the decorated function unmodified.
    """

    if capture is None:
        capture = set()
    if clone is None:
        clone = set()

    pred_sig = inspect.signature(predicate)
    pred_params = pred_sig.parameters
    loc = inspect.getframeinfo(inspect.currentframe().f_back)
    semantic: EvaluationSemantic = get_contract_evaluation_semantic(AssertionKind.pre)

    def make_contract_checked_func(func):
        func_sig = inspect.signature(func)
        func_params = func_sig.parameters

        frame = find_outer_stack_frame(func)
        variables_in_scope = (
            set(func_sig.parameters.keys())
            | set(frame.frame.f_locals.keys())
            | set(frame.frame.f_globals)
        )

        bindings = set(func_params.keys()) | capture | clone
        __assert_predicate_well_formed(pred_params, bindings, variables_in_scope)

        if semantic == EvaluationSemantic.ignore:
            return func

        @wraps(func)
        def checked_func(*args, **kwargs):
            nkwargs = map_function_arguments(func_sig, args, kwargs)

            # resolve bindings
            candidate_bindings = [nkwargs, frame.frame.f_locals, frame.frame.f_globals]
            resolved_kwargs = __resolve_bindings(
                candidates=candidate_bindings,
                capture=capture | pred_params.keys(),
                clone=clone,
            )

            # assert precondition
            __assert_contract(
                semantic=semantic,
                kind=AssertionKind.pre,
                loc=loc,
                predicate=predicate,
                predicate_kwargs=resolved_kwargs,
            )

            # evaluate decorated function
            return func(*args, **kwargs)

        return checked_func

    return make_contract_checked_func


def __find_result_param(pred_params, bindings: set[str]) -> str | None:
    """Given the predicate parameters `pred_params`, finds the one not in the set of bound names `bindings`.

    Returns `None` if there is no result parameter.

    Raises `TypeError` if there is more than one potential result parameter.
    """

    candidates = {n for n in pred_params.keys() if n not in bindings}
    match len(candidates):
        case 0:
            return None
        case 1:
            return candidates.pop()
        case _:
            raise TypeError(
                f"Unable to determine predicate result parameter. Candidates: {','.join(candidates)}"
            )


def post(
    predicate,
    capture_before: set[str] = None,
    capture_after: set[str] = None,
    clone_before: set[str] = None,
    clone_after: set[str] = None,
):
    """Postcondition assertion decorator factory taking a predicate to evaluate after function evaluation

    Keyword arguments:
        predicate: A callable evaluating the predicate to check after function evaluation
        capture_before: A set of names to capture before function evaluation. Variables by this name can be predicate parameters
        capture_after: A set of names to capture after function evaluation. Variables by this name can be predicate parameters
        clone_before: A set of names to clone before function evaluation. Variables by this name can be predicate parameters
        clone_after: A set of names to clone after function evaluation. Variables by this name can be predicate parameters

    Returns:
        - The returned decorator raises TypeError if the predicate is malformed.
        - Otherwise:

          - if the current contract evaluation semantic is not `ignore`, returns a wrapper of the decorated function that
            checks the predicate before evaluating the original function.
          - if the current contract evaluation semantic is `ignore`, returns the decorated function unmodified.
    """

    if capture_before is None:
        capture_before = set()
    if capture_after is None:
        capture_after = set()
    if clone_before is None:
        clone_before = set()
    if clone_after is None:
        clone_after = set()

    pred_sig = inspect.signature(predicate)
    pred_params = pred_sig.parameters
    loc = inspect.getframeinfo(inspect.currentframe().f_back)
    semantic: EvaluationSemantic = get_contract_evaluation_semantic(AssertionKind.pre)

    def make_contract_checked_func(func):
        func_sig = inspect.signature(func)
        frame = find_outer_stack_frame(func)

        variables_in_scope = (
            set(func_sig.parameters.keys())
            | set(frame.frame.f_locals.keys())
            | set(frame.frame.f_globals)
        )

        bindings = capture_before | capture_after | clone_before | clone_after

        result_param_name = __find_result_param(pred_params, bindings)
        if result_param_name is not None:
            bindings.add(result_param_name)
            variables_in_scope.add(result_param_name)

        __assert_predicate_well_formed(pred_params, bindings, variables_in_scope)

        if semantic == EvaluationSemantic.ignore:
            return func

        @wraps(func)
        def checked_func(*args, **kwargs):
            nkwargs = map_function_arguments(func_sig, args, kwargs)

            # resolve "before"-type bindings
            candidate_bindings = [nkwargs, frame.frame.f_locals, frame.frame.f_globals]
            resolved_kwargs = __resolve_bindings(
                candidates=candidate_bindings,
                capture=capture_before,
                clone=clone_before,
            )

            # evaluate decorated function
            result = func(*args, **kwargs)

            # resolve "after"-type bindings
            referenced_bindings = capture_after
            if result_param_name is not None:
                candidate_bindings = [{result_param_name: result}] + candidate_bindings
                referenced_bindings.add(result_param_name)
            resolved_kwargs |= __resolve_bindings(
                candidates=candidate_bindings,
                capture=referenced_bindings,
                clone=clone_after,
            )

            # assert postcondition
            __assert_contract(
                semantic=semantic,
                kind=AssertionKind.post,
                loc=loc,
                predicate=predicate,
                predicate_kwargs=resolved_kwargs,
            )

            return result

        return checked_func

    return make_contract_checked_func
