import inspect
from collections.abc import Callable
from functools import wraps

from pycontractz.evaluation_semantic import EvaluationSemantic
from pycontractz.assertion_kind import AssertionKind
from pycontractz.contract_violation_handler import get_contract_evaluation_semantic
from pycontractz.utils.assert_contract import assert_contract
from pycontractz.utils.map_function_arguments import map_function_arguments
from pycontractz.utils.resolve_bindings import resolve_bindings
from pycontractz.predicate import Predicate, assert_predicate_well_formed
from pycontractz.capture_set import CaptureSet, normalize_capture_set


class pre:
    """Precondition assertion factory taking a predicate to evaluate on function evaluation"""

    def __init__(
        self,
        predicate: Predicate,
        /,
        *,
        capture: CaptureSet = None,
        clone: CaptureSet = None,
    ):
        """Initializes the precondition assertion factory

        Keyword arguments:
            predicate: A callable evaluating the predicate to check before function evaluation.
            capture: A set of names to capture. Variables by this name can be predicate parameters.
                     Note that the wrapped function's arguments are implicitly captured.
            clone: A set of names to clone. Variables by this name can be predicate parameters.
        """
        capture = normalize_capture_set(capture)
        clone = normalize_capture_set(clone)

        self.__predicate = predicate
        self.__capture = capture
        self.__clone = clone
        self.__pred_sig = inspect.signature(predicate)
        self.__pred_params = self.__pred_sig.parameters
        self.__parent_frame = inspect.currentframe().f_back
        self.__semantic: EvaluationSemantic = get_contract_evaluation_semantic(
            AssertionKind.pre
        )

    def __call__(self, func: Callable, /):
        """Wraps the given callable in another callable that checks preconditions before executing the original callable

        Keyword arguments:
            func: Callable to wrap. Typically, a function.

        Returns:
            - `func` if the current contract evaluation semantic is `ignore`
            - a checked wrapper compatible with `func` otherwise

        Raises:
            TypeError: if the predicate is malformed given `func` and the set of captured and cloned values.
        """
        func_sig = inspect.signature(func)
        func_params = func_sig.parameters

        variables_in_scope = (
            set(func_sig.parameters.keys())
            | set(self.__parent_frame.f_locals.keys())
            | set(self.__parent_frame.f_globals)
        )

        bindings = {n: n for n in func_params.keys()} | self.__capture | self.__clone
        assert_predicate_well_formed(self.__pred_params, bindings, variables_in_scope)

        if self.__semantic == EvaluationSemantic.ignore:
            return func

        @wraps(func)
        def checked_func(*args, **kwargs):
            nkwargs = map_function_arguments(func_sig, args, kwargs)

            # resolve bindings
            candidate_bindings = [
                nkwargs,
                self.__parent_frame.f_locals,
                self.__parent_frame.f_globals,
            ]
            resolved_kwargs = resolve_bindings(
                candidates=candidate_bindings,
                capture={n: n for n in self.__pred_params.keys()} | self.__capture,
                clone=self.__clone,
            )

            # assert precondition
            assert_contract(
                semantic=self.__semantic,
                kind=AssertionKind.pre,
                loc=inspect.getframeinfo(self.__parent_frame),
                predicate=self.__predicate,
                predicate_kwargs=resolved_kwargs,
            )

            # evaluate decorated function
            return func(*args, **kwargs)

        return checked_func

    def __enter__(self):
        """Checks all preconditions when the scope is entered

        Raises:
            TypeError: if the predicate is malformed given the set of captured and cloned values.
        """

        # resolve bindings
        candidate_bindings = [
            self.__parent_frame.f_locals,
            self.__parent_frame.f_globals,
        ]
        resolved_kwargs = resolve_bindings(
            candidates=candidate_bindings,
            capture={n: n for n in self.__pred_params.keys()} | self.__capture,
            clone=self.__clone,
        )

        # assert precondition
        assert_contract(
            semantic=self.__semantic,
            kind=AssertionKind.pre,
            loc=inspect.getframeinfo(self.__parent_frame),
            predicate=self.__predicate,
            predicate_kwargs=resolved_kwargs,
        )
        return self

    def __exit__(self, *exc):
        """Doesn't do anything"""
        return False
