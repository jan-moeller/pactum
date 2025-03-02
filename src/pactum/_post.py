import inspect
from collections.abc import Callable
from enum import Enum, Flag, auto
from functools import wraps
from types import TracebackType
from typing import Any, Self, Literal

from pactum._evaluation_semantic import EvaluationSemantic
from pactum._assertion_kind import AssertionKind
from pactum._utils._assert_contract import assert_contract
from pactum._utils._effective_semantic import effective_semantic
from pactum._utils._map_function_arguments import map_function_arguments
from pactum._utils._parent_frame import get_parent_frame
from pactum._utils._resolve_bindings import (
    resolve_bindings,
    collect_available_variables,
)
from pactum._predicate import Predicate
from pactum._capture_set import CaptureSet, normalize_capture_set
from pactum._contract_assertion_label import ContractAssertionLabel


class PostconditionScope(Flag):
    """Holds information on when a postcondition should be evaluated."""

    RegularReturn = auto()
    ExceptionalReturn = auto()
    Always = RegularReturn | ExceptionalReturn


class post:
    """Postcondition assertion factory taking a predicate to evaluate after function evaluation"""

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
        scope: PostconditionScope = PostconditionScope.RegularReturn,
    ):
        """Initializes the precondition assertion factory

        Keyword arguments:
            predicate: A callable evaluating the predicate to check after function evaluation
            capture_before: A set of names to capture before function evaluation. Variables by this name can be predicate parameters
            capture_after: A set of names to capture after function evaluation. Variables by this name can be predicate parameters
            clone_before: A set of names to clone before function evaluation. Variables by this name can be predicate parameters
            clone_after: A set of names to clone after function evaluation. Variables by this name can be predicate parameters
            labels: A list of labels that determine this assertion's evaluation semantic
            scope: Determines whether the postcondition applies if the function returns regularly, with an exception, or both
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
        self.__scope = scope
        self.__parent_frame = get_parent_frame(inspect.currentframe())
        self.__semantic = effective_semantic(
            self.__parent_frame, AssertionKind.post, labels
        )

    def __find_result_param(self) -> str | None:
        """Given the predicate parameters `pred_params`, finds the one not in the set of bound names `bindings`.

        Returns `None` if there is no result parameter.

        Raises `TypeError` if there is more than one potential result parameter.
        """

        bindings = (
            set(self.__capture_before.keys())
            | set(self.__clone_before.keys())
            | set(self.__capture_after.keys())
            | set(self.__clone_after.keys())
        )
        params = inspect.signature(self.__predicate).parameters
        candidates = {n for n in params.keys() if n not in bindings}
        match len(candidates):
            case 0:
                return None
            case 1:
                return candidates.pop()
            case _:
                raise TypeError(
                    f"Unable to determine predicate result parameter. Candidates: {','.join(candidates)}"
                )

    def __call__[R](
        self,
        func: Callable[..., R],
        /,
        *,
        _implicit_return_capture: bool = True,
        _implicit_arg_capture: bool = False,
    ) -> Callable[..., R]:
        """Wraps the given callable in another callable that checks postconditions after executing the original callable

        Keyword arguments:
            func: Callable to wrap. Typically, a function.

        Returns:
            - `func` if the effective contract evaluation semantic is `ignore`
            - a checked wrapper compatible with `func` otherwise
        """

        if self.__semantic == EvaluationSemantic.ignore:
            return func

        @wraps(func)
        def checked_func(*args: Any, **kwargs: Any) -> R:
            sig = inspect.signature(func)
            nkwargs = map_function_arguments(sig, args, kwargs)

            # resolve "before"-type bindings
            available_variables = collect_available_variables(
                self.__parent_frame,
                nkwargs,
            )
            capture = self.__capture_before
            if _implicit_arg_capture:
                capture = {n: n for n in sig.parameters.keys()} | capture
            resolved_kwargs = resolve_bindings(
                available_variables=available_variables,
                capture=capture,
                clone=self.__clone_before,
            )

            # evaluate decorated function
            exception_raised = None
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                if PostconditionScope.ExceptionalReturn not in self.__scope:
                    raise
                exception_raised = exc
            else:
                if PostconditionScope.RegularReturn not in self.__scope:
                    return result

            # resolve "after"-type bindings
            available_variables = collect_available_variables(
                self.__parent_frame,
                nkwargs,
            )
            # Implicitly capture result argument
            capture = self.__capture_after
            if _implicit_return_capture:
                result_name = self.__find_result_param()
                result_value = result if exception_raised is None else exception_raised
                if result_name is not None:
                    capture = {result_name: result_name} | capture
                    available_variables.insert(0, {result_name: result_value})
            resolved_kwargs |= resolve_bindings(
                available_variables=available_variables,
                capture=capture,
                clone=self.__clone_after,
            )

            # assert postcondition
            assert_contract(
                semantic=self.__semantic,
                kind=AssertionKind.post,
                calling_frame=self.__parent_frame,
                predicate=self.__predicate,
                predicate_kwargs=resolved_kwargs,
            )

            # If an exception was raised, re-raise it; otherwise, return the regular return value
            if exception_raised is not None:
                raise exception_raised
            else:
                return result

        return checked_func

    def __enter__(self) -> Self:
        """Captures before-type bindings when the scope is entered"""

        # resolve "before"-type bindings
        available_variables = collect_available_variables(self.__parent_frame, {})
        self.__resolved_kwargs = resolve_bindings(
            available_variables=available_variables,
            capture=self.__capture_before,
            clone=self.__clone_before,
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Captures after-type bindings, then checks the postcondition"""

        exceptional_exit = exc_val is not None
        if exceptional_exit:
            if PostconditionScope.ExceptionalReturn not in self.__scope:
                return False
        else:
            if PostconditionScope.RegularReturn not in self.__scope:
                return False

        # resolve "after"-type bindings
        available_variables = collect_available_variables(self.__parent_frame, {})
        self.__resolved_kwargs |= resolve_bindings(
            available_variables=available_variables,
            capture=self.__capture_after,
            clone=self.__clone_after,
        )

        # assert postcondition
        assert_contract(
            semantic=self.__semantic,
            kind=AssertionKind.post,
            calling_frame=self.__parent_frame,
            predicate=self.__predicate,
            predicate_kwargs=self.__resolved_kwargs,
        )
        return False
