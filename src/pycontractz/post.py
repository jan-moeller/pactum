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


class post:
    """Postcondition assertion factory taking a predicate to evaluate after function evaluation"""

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

    def __init__(
        self,
        predicate: Predicate,
        capture_before: set[str] = None,
        capture_after: set[str] = None,
        clone_before: set[str] = None,
        clone_after: set[str] = None,
    ):
        """Initializes the precondition assertion factory

        Keyword arguments:
            predicate: A callable evaluating the predicate to check after function evaluation
            capture_before: A set of names to capture before function evaluation. Variables by this name can be predicate parameters
            capture_after: A set of names to capture after function evaluation. Variables by this name can be predicate parameters
            clone_before: A set of names to clone before function evaluation. Variables by this name can be predicate parameters
            clone_after: A set of names to clone after function evaluation. Variables by this name can be predicate parameters
        """

        if capture_before is None:
            capture_before = set()
        if capture_after is None:
            capture_after = set()
        if clone_before is None:
            clone_before = set()
        if clone_after is None:
            clone_after = set()

        self.predicate = predicate
        self.capture_before = capture_before
        self.capture_after = capture_after
        self.clone_before = clone_before
        self.clone_after = clone_after
        self.pred_sig = inspect.signature(predicate)
        self.pred_params = self.pred_sig.parameters
        self.parent_frame = inspect.currentframe().f_back
        self.semantic: EvaluationSemantic = get_contract_evaluation_semantic(
            AssertionKind.post
        )
        self.bindings = capture_before | capture_after | clone_before | clone_after
        self.result_param_name = self.__find_result_param(self.bindings)

    def __find_result_param(self, bindings: set[str]) -> str | None:
        """Given the predicate parameters `pred_params`, finds the one not in the set of bound names `bindings`.

        Returns `None` if there is no result parameter.

        Raises `TypeError` if there is more than one potential result parameter.
        """

        candidates = {n for n in self.pred_params.keys() if n not in bindings}
        match len(candidates):
            case 0:
                return None
            case 1:
                return candidates.pop()
            case _:
                raise TypeError(
                    f"Unable to determine predicate result parameter. Candidates: {','.join(candidates)}"
                )

    def __call__(self, func: Callable):
        """Wraps the given callable in another callable that checks postconditions after executing the original callable

        Keyword arguments:
            func: Callable to wrap. Typically, a function.

        Returns:
            - `func` if the current contract evaluation semantic is `ignore`
            - a checked wrapper compatible with `func` otherwise

        Raises:
            TypeError: if the predicate is malformed given `func` and the set of captured and cloned values.
        """
        func_sig = inspect.signature(func)

        variables_in_scope = (
            set(func_sig.parameters.keys())
            | set(self.parent_frame.f_locals.keys())
            | set(self.parent_frame.f_globals)
        )

        if self.result_param_name is not None:
            self.bindings.add(self.result_param_name)
            variables_in_scope.add(self.result_param_name)

        assert_predicate_well_formed(
            self.pred_params, self.bindings, variables_in_scope
        )

        if self.semantic == EvaluationSemantic.ignore:
            return func

        @wraps(func)
        def checked_func(*args, **kwargs):
            nkwargs = map_function_arguments(func_sig, args, kwargs)

            # resolve "before"-type bindings
            candidate_bindings = [
                nkwargs,
                self.parent_frame.f_locals,
                self.parent_frame.f_globals,
            ]
            resolved_kwargs = resolve_bindings(
                candidates=candidate_bindings,
                capture=self.capture_before,
                clone=self.clone_before,
            )

            # evaluate decorated function
            result = func(*args, **kwargs)

            # resolve "after"-type bindings
            referenced_bindings = self.capture_after
            if self.result_param_name is not None:
                candidate_bindings = [
                    {self.result_param_name: result}
                ] + candidate_bindings
                referenced_bindings.add(self.result_param_name)
            resolved_kwargs |= resolve_bindings(
                candidates=candidate_bindings,
                capture=referenced_bindings,
                clone=self.clone_after,
            )

            # assert postcondition
            assert_contract(
                semantic=self.semantic,
                kind=AssertionKind.post,
                loc=inspect.getframeinfo(self.parent_frame),
                predicate=self.predicate,
                predicate_kwargs=resolved_kwargs,
            )

            return result

        return checked_func

    def __enter__(self):
        """Captures any variables when the scope is entered

        Raises:
            TypeError: if the predicate is malformed given the set of captured and cloned values.
        """

        if self.result_param_name is not None:
            raise TypeError(
                f'Postcondition refers to result "{self.result_param_name}", but usage as context manager precludes result parameter usage'
            )

        # resolve "before"-type bindings
        self.candidate_bindings = [
            self.parent_frame.f_locals,
            self.parent_frame.f_globals,
        ]
        self.resolved_kwargs = resolve_bindings(
            candidates=self.candidate_bindings,
            capture=self.capture_before,
            clone=self.clone_before,
        )
        return self

    def __exit__(self, *exc):
        """Captures any variables, then checks all postconditions

        Raises:
            TypeError: if the predicate is malformed given the set of captured and cloned values.
        """

        # resolve "after"-type bindings
        referenced_bindings = self.capture_after
        self.resolved_kwargs |= resolve_bindings(
            candidates=self.candidate_bindings,
            capture=referenced_bindings,
            clone=self.clone_after,
        )

        # assert postcondition
        assert_contract(
            semantic=self.semantic,
            kind=AssertionKind.post,
            loc=inspect.getframeinfo(self.parent_frame),
            predicate=self.predicate,
            predicate_kwargs=self.resolved_kwargs,
        )
        return False
