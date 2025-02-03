import inspect
import sys
from functools import wraps
from inspect import Parameter

from pycontractz.evaluation_semantic import EvaluationSemantic
from pycontractz.assertion_kind import AssertionKind
from pycontractz.contract_violation import ContractViolation
from pycontractz.contract_violation_handler import (
    get_contract_evaluation_semantic,
    invoke_contract_violation_handler,
)
from pycontractz.detection_mode import DetectionMode


def __promote_positional_arguments_to_keyword_arguments(
    args: tuple,
    kwargs: dict,
    signature: inspect.Signature,
) -> tuple[tuple, dict]:
    """Promotes positional arguments passed to a function to keyword arguments where possible

    Given a function with signature `signature`, positional arguments from *args are promoted to **kwargs if a matching
    named parameter exists in the function signature. After this process, only parameters matching *args in the
    signature (if any) remain positional.
    """

    matched_args = []
    matched_kwargs = {}

    params = list(signature.parameters.items())

    for i in range(min(len(params), len(args))):
        name = params[i][0]
        param = params[i][1]
        match param.kind:
            case Parameter.VAR_POSITIONAL:
                matched_args.extend(args[i:])
                break  # Everything after must be keyword arguments
            case _:
                matched_kwargs[name] = args[i]

    matched_kwargs.update(kwargs)

    return tuple(matched_args), matched_kwargs


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
    mode: DetectionMode,
    kind: AssertionKind,
    location: inspect.Traceback,
    comment: str = "",
    evaluation_exception: Exception | None = None,
):
    """Handles a contract violation by invoking the contract violation handler and/or terminating if required"""

    if semantic == EvaluationSemantic.ignore:
        return

    violation = ContractViolation(
        comment=comment,
        detection_mode=mode,
        evaluation_exception=evaluation_exception,
        kind=kind,
        location=location,
        semantic=semantic,
    )

    if semantic in [EvaluationSemantic.observe, EvaluationSemantic.enforce]:
        invoke_contract_violation_handler(violation)

    if violation.is_terminating:
        sys.exit(1)


def __assert_contract(
    semantic: EvaluationSemantic,
    kind: AssertionKind,
    loc: inspect.Traceback,
    predicate,
    predicate_args: tuple,
    predicate_kwargs: dict,
):
    """Evaluates the given predicate and handles a contract violation if the result was false or an exception escaped

    `predicate_args` and `predicate_kwargs` are assumed to be the output of
    `__promote_positional_arguments_to_keyword_arguments`.
    """

    try:
        pred_result = __call_predicate(
            predicate,
            predicate_args,
            predicate_kwargs,
        )
    except Exception as exc:
        __handle_contract_violation(
            semantic=semantic,
            mode=DetectionMode.evaluation_exception,
            evaluation_exception=exc,
            kind=kind,
            location=loc,
        )
    else:
        if not pred_result:
            __handle_contract_violation(
                semantic=semantic,
                mode=DetectionMode.predicate_false,
                kind=kind,
                location=loc,
            )


def __check_predicate_well_formed(pred_params, func_params) -> str | None:
    """Checks if a predicate is well-formed for the function it's decorating

    Returns an error description if the predicate is found to be ill-formed. Otherwise, returns None.
    """

    # Check that:
    # - the predicate doesn't have positional-only parameters
    # - if the predicate has a *args parameter, the decorated function also has one
    # - all keyword arguments also exist in the decorated function
    for name, param in pred_params.items():
        match param.kind:
            case Parameter.POSITIONAL_ONLY:
                return f'Predicate has positional-only parameter "{name}"'
            case Parameter.VAR_POSITIONAL:
                if not any(
                    p.kind == Parameter.VAR_POSITIONAL for p in func_params.values()
                ):
                    return f'Predicate has variadic positional-only parameter "{name}", but decorated function doesn\'t'
            case Parameter.POSITIONAL_OR_KEYWORD | Parameter.KEYWORD_ONLY:
                if not any(
                    p.kind not in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD]
                    and n == name
                    for n, p in func_params.items()
                ):
                    return f'Predicate has parameter "{name}" not present in decorated function'
    return None


def pre(predicate):
    """Precondition assertion decorator taking a predicate to evaluate on function evaluation"""

    pred_sig = inspect.signature(predicate)
    pred_params = pred_sig.parameters
    loc = inspect.getframeinfo(inspect.currentframe().f_back)
    semantic: EvaluationSemantic = get_contract_evaluation_semantic(AssertionKind.pre)

    def make_contract_checked_func(func):
        func_sig = inspect.signature(func)
        func_params = func_sig.parameters

        error_msg = __check_predicate_well_formed(pred_params, func_params)
        if error_msg is not None:
            __handle_contract_violation(
                semantic=semantic,
                mode=DetectionMode.implicit,
                kind=AssertionKind.pre,
                location=loc,
                comment=error_msg,
            )
            return func

        if semantic == EvaluationSemantic.ignore:
            return func

        @wraps(func)
        def checked_func(*args, **kwargs):
            nargs, nkwargs = __promote_positional_arguments_to_keyword_arguments(
                args, kwargs, func_sig
            )

            __assert_contract(
                semantic=semantic,
                kind=AssertionKind.pre,
                loc=loc,
                predicate=predicate,
                predicate_args=nargs,
                predicate_kwargs=nkwargs,
            )

            return func(*args, **kwargs)

        return checked_func

    return make_contract_checked_func


def post(predicate):
    """Postcondition assertion decorator taking a predicate to evaluate after function evaluation"""

    pred_sig = inspect.signature(predicate)
    pred_params = pred_sig.parameters
    loc = inspect.getframeinfo(inspect.currentframe().f_back)
    semantic: EvaluationSemantic = get_contract_evaluation_semantic(AssertionKind.pre)

    def make_contract_checked_func(func):
        if len(pred_params) > 1:
            __handle_contract_violation(
                semantic=semantic,
                mode=DetectionMode.implicit,
                kind=AssertionKind.pre,
                location=loc,
                comment="Postconditions must either have no or one parameter",
            )
            return func

        if semantic == EvaluationSemantic.ignore:
            return func

        @wraps(func)
        def checked_func(*args, **kwargs):
            result = func(*args, **kwargs)

            assertion_kwargs = {name: result for name in pred_params.keys()}
            __assert_contract(
                semantic=semantic,
                kind=AssertionKind.post,
                loc=loc,
                predicate=predicate,
                predicate_args=(),
                predicate_kwargs=assertion_kwargs,
            )

            return result

        return checked_func

    return make_contract_checked_func
