import inspect
from collections.abc import Callable
from functools import wraps

from pycontractz._evaluation_semantic import EvaluationSemantic
from pycontractz._assertion_kind import AssertionKind
from pycontractz._contract_violation_handler import get_contract_evaluation_semantic
from pycontractz._utils._assert_contract import assert_contract
from pycontractz._utils._map_function_arguments import map_function_arguments
from pycontractz._utils._resolve_bindings import resolve_bindings
from pycontractz._predicate import Predicate, assert_predicate_well_formed
from pycontractz._capture_set import CaptureSet, normalize_capture_set
from pycontractz._contract_assertion_label import (
    ContractAssertionLabel,
    ContractAssertionInfo,
)


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
        /,
        *,
        capture_before: CaptureSet | None = None,
        capture_after: CaptureSet | None = None,
        clone_before: CaptureSet | None = None,
        clone_after: CaptureSet | None = None,
        labels: list[ContractAssertionLabel] | None = None,
    ):
        """Initializes the precondition assertion factory

        Keyword arguments:
            predicate: A callable evaluating the predicate to check after function evaluation
            capture_before: A set of names to capture before function evaluation. Variables by this name can be predicate parameters
            capture_after: A set of names to capture after function evaluation. Variables by this name can be predicate parameters
            clone_before: A set of names to clone before function evaluation. Variables by this name can be predicate parameters
            clone_after: A set of names to clone after function evaluation. Variables by this name can be predicate parameters
            labels: A list of labels that determine this assertion's evaluation semantic
        """

        capture_before = normalize_capture_set(capture_before)
        capture_after = normalize_capture_set(capture_after)
        clone_before = normalize_capture_set(clone_before)
        clone_after = normalize_capture_set(clone_after)

        if labels is None:
            labels = []

        self.__predicate = predicate
        self.__capture_before = capture_before
        self.__capture_after = capture_after
        self.__clone_before = clone_before
        self.__clone_after = clone_after
        self.__pred_sig = inspect.signature(predicate)
        self.__pred_params = self.__pred_sig.parameters
        self.__parent_frame = inspect.currentframe()
        if self.__parent_frame is not None:
            self.__parent_frame = self.__parent_frame.f_back

        module = inspect.getmodule(self.__parent_frame)
        info = ContractAssertionInfo(
            kind=AssertionKind.post,
            module_name=module.__name__ if module is not None else "",
        )
        self.__semantic: EvaluationSemantic = get_contract_evaluation_semantic(info)
        for label in labels:
            self.__semantic = label(self.__semantic, info)

        self.__bindings = capture_before | capture_after | clone_before | clone_after
        self.__result_param_name = self.__find_result_param(set(self.__bindings.keys()))

    def __find_result_param(self, bindings: set[str]) -> str | None:
        """Given the predicate parameters `pred_params`, finds the one not in the set of bound names `bindings`.

        Returns `None` if there is no result parameter.

        Raises `TypeError` if there is more than one potential result parameter.
        """

        candidates = {n for n in self.__pred_params.keys() if n not in bindings}
        match len(candidates):
            case 0:
                return None
            case 1:
                return candidates.pop()
            case _:
                raise TypeError(
                    f"Unable to determine predicate result parameter. Candidates: {','.join(candidates)}"
                )

    def __call__(self, func: Callable, /):
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

        variables_in_scope = set(func_sig.parameters.keys())
        if self.__parent_frame is not None:
            variables_in_scope |= set(self.__parent_frame.f_locals.keys())
            variables_in_scope |= set(self.__parent_frame.f_globals.keys())

        if self.__result_param_name is not None:
            self.__bindings[self.__result_param_name] = self.__result_param_name
            variables_in_scope.add(self.__result_param_name)

        assert_predicate_well_formed(
            self.__pred_params, self.__bindings, variables_in_scope
        )

        if self.__semantic == EvaluationSemantic.ignore:
            return func

        @wraps(func)
        def checked_func(*args, **kwargs):
            nkwargs = map_function_arguments(func_sig, args, kwargs)

            # resolve "before"-type bindings
            candidate_bindings = [
                nkwargs,
                self.__parent_frame.f_locals,
                self.__parent_frame.f_globals,
            ]
            resolved_kwargs = resolve_bindings(
                candidates=candidate_bindings,
                capture=self.__capture_before,
                clone=self.__clone_before,
            )

            # evaluate decorated function
            result = func(*args, **kwargs)

            # resolve "after"-type bindings
            referenced_bindings = self.__capture_after
            if self.__result_param_name is not None:
                candidate_bindings = [
                    {self.__result_param_name: result}
                ] + candidate_bindings
                referenced_bindings[self.__result_param_name] = self.__result_param_name
            resolved_kwargs |= resolve_bindings(
                candidates=candidate_bindings,
                capture=referenced_bindings,
                clone=self.__clone_after,
            )

            # assert postcondition
            assert_contract(
                semantic=self.__semantic,
                kind=AssertionKind.post,
                loc=inspect.getframeinfo(self.__parent_frame),
                predicate=self.__predicate,
                predicate_kwargs=resolved_kwargs,
            )

            return result

        return checked_func

    def __enter__(self):
        """Captures any variables when the scope is entered

        Raises:
            TypeError: if the predicate is malformed given the set of captured and cloned values.
        """

        if self.__result_param_name is not None:
            raise TypeError(
                f'Postcondition refers to result "{self.__result_param_name}", but usage as context manager precludes result parameter usage'
            )

        # resolve "before"-type bindings
        self.__candidate_bindings = [
            self.__parent_frame.f_locals,
            self.__parent_frame.f_globals,
        ]
        self.__resolved_kwargs = resolve_bindings(
            candidates=self.__candidate_bindings,
            capture=self.__capture_before,
            clone=self.__clone_before,
        )
        return self

    def __exit__(self, *exc):
        """Captures any variables, then checks all postconditions

        Raises:
            TypeError: if the predicate is malformed given the set of captured and cloned values.
        """

        # resolve "after"-type bindings
        referenced_bindings = self.__capture_after
        self.__resolved_kwargs |= resolve_bindings(
            candidates=self.__candidate_bindings,
            capture=referenced_bindings,
            clone=self.__clone_after,
        )

        # assert postcondition
        assert_contract(
            semantic=self.__semantic,
            kind=AssertionKind.post,
            loc=inspect.getframeinfo(self.__parent_frame),
            predicate=self.__predicate,
            predicate_kwargs=self.__resolved_kwargs,
        )
        return False
