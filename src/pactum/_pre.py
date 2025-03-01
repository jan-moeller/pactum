import inspect
from collections.abc import Callable
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


class pre:
    """Precondition assertion factory taking a predicate to evaluate on function evaluation"""

    def __init__(
        self,
        predicate: Predicate,
        /,
        *,
        capture: CaptureSet | None = None,
        clone: CaptureSet | None = None,
        labels: list[ContractAssertionLabel] | None = None,
    ):
        """Initializes the precondition assertion factory

        Keyword arguments:
            predicate: A callable evaluating the predicate to check before function evaluation.
            capture: A set of names to capture. Variables by this name can be predicate parameters.
                     Note that the wrapped function's arguments are implicitly captured.
            clone: A set of names to clone. Variables by this name can be predicate parameters.
            labels: A list of labels that determine this assertion's evaluation semantic
        """
        capture = normalize_capture_set(capture)
        clone = normalize_capture_set(clone)

        if labels is None:
            labels = []

        self.__predicate = predicate
        self.__capture = capture
        self.__clone = clone
        self.__parent_frame = get_parent_frame(inspect.currentframe())
        self.__semantic = effective_semantic(
            self.__parent_frame, AssertionKind.pre, labels
        )

    def __call__[R](
        self,
        func: Callable[..., R],
        /,
        *,
        _implicit_arg_capture: bool = True,
    ) -> Callable[..., R]:
        """Wraps the given callable in another callable that checks preconditions before executing the original callable

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

            # resolve bindings
            available_variables = collect_available_variables(
                self.__parent_frame,
                nkwargs,
            )
            # Implicitly capture function arguments, but explicit captures take priority
            capture = self.__capture
            if _implicit_arg_capture:
                capture = {n: n for n in sig.parameters.keys()} | capture
            resolved_kwargs = resolve_bindings(
                available_variables=available_variables,
                capture=capture,
                clone=self.__clone,
            )

            # assert precondition
            assert_contract(
                semantic=self.__semantic,
                kind=AssertionKind.pre,
                calling_frame=self.__parent_frame,
                predicate=self.__predicate,
                predicate_kwargs=resolved_kwargs,
            )

            # evaluate decorated function
            return func(*args, **kwargs)

        return checked_func

    def __enter__(self) -> Self:
        """Checks all preconditions when the scope is entered"""

        # resolve bindings
        available_variables = collect_available_variables(self.__parent_frame, {})
        resolved_kwargs = resolve_bindings(
            available_variables=available_variables,
            capture=self.__capture,
            clone=self.__clone,
        )

        # assert precondition
        assert_contract(
            semantic=self.__semantic,
            kind=AssertionKind.pre,
            calling_frame=self.__parent_frame,
            predicate=self.__predicate,
            predicate_kwargs=resolved_kwargs,
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Doesn't do anything"""

        return False
