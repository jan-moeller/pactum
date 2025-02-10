import inspect
from functools import wraps

from pycontractz.evaluation_semantic import EvaluationSemantic
from pycontractz.assertion_kind import AssertionKind
from pycontractz.contract_violation_handler import get_contract_evaluation_semantic
from pycontractz.utils.assert_contract import assert_contract
from pycontractz.utils.find_outer_stack_frame import find_outer_stack_frame
from pycontractz.utils.map_function_arguments import map_function_arguments
from pycontractz.utils.resolve_bindings import resolve_bindings
from pycontractz.predicate import Predicate, assert_predicate_well_formed


def pre(
    predicate: Predicate,
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
        assert_predicate_well_formed(pred_params, bindings, variables_in_scope)

        if semantic == EvaluationSemantic.ignore:
            return func

        @wraps(func)
        def checked_func(*args, **kwargs):
            nkwargs = map_function_arguments(func_sig, args, kwargs)

            # resolve bindings
            candidate_bindings = [nkwargs, frame.frame.f_locals, frame.frame.f_globals]
            resolved_kwargs = resolve_bindings(
                candidates=candidate_bindings,
                capture=capture | pred_params.keys(),
                clone=clone,
            )

            # assert precondition
            assert_contract(
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
