import inspect
from collections.abc import Callable
from functools import wraps
from types import TracebackType
from typing import Any, Self, Literal

from pactum._evaluation_semantic import EvaluationSemantic
from pactum._assertion_kind import AssertionKind
from pactum._contract_violation_handler import get_contract_evaluation_semantic
from pactum._utils._assert_contract import assert_contract
from pactum._utils._map_function_arguments import map_function_arguments
from pactum._utils._resolve_bindings import resolve_bindings
from pactum._predicate import Predicate, assert_predicate_well_formed
from pactum._capture_set import CaptureSet, normalize_capture_set
from pactum._contract_assertion_label import (
    ContractAssertionLabel,
    ContractAssertionInfo,
)


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
        self.__pred_sig = inspect.signature(predicate)
        self.__pred_params = self.__pred_sig.parameters
        self.__parent_frame = inspect.currentframe()
        if self.__parent_frame is not None:
            self.__parent_frame = self.__parent_frame.f_back

        module = inspect.getmodule(self.__parent_frame)
        info = ContractAssertionInfo(
            kind=AssertionKind.pre,
            module_name=module.__name__ if module is not None else "",
        )
        self.__semantic: EvaluationSemantic = get_contract_evaluation_semantic(info)
        for label in labels:
            self.__semantic = label(self.__semantic, info)

    def __call__[R](self, func: Callable[..., R], /) -> Callable[..., R]:
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

        variables_in_scope = set(func_sig.parameters.keys())
        if self.__parent_frame is not None:
            variables_in_scope |= set(self.__parent_frame.f_locals.keys())
            variables_in_scope |= set(self.__parent_frame.f_globals.keys())

        bindings = {n: n for n in func_params.keys()} | self.__capture | self.__clone
        assert_predicate_well_formed(self.__pred_params, bindings, variables_in_scope)

        if self.__semantic == EvaluationSemantic.ignore:
            return func

        @wraps(func)
        def checked_func(*args: Any, **kwargs: Any) -> R:
            nkwargs = map_function_arguments(func_sig, args, kwargs)

            # resolve bindings
            candidate_bindings = [nkwargs]
            if self.__parent_frame is not None:
                candidate_bindings += [
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
                loc=(
                    inspect.getframeinfo(self.__parent_frame)
                    if self.__parent_frame is not None
                    else None
                ),
                predicate=self.__predicate,
                predicate_kwargs=resolved_kwargs,
            )

            # evaluate decorated function
            return func(*args, **kwargs)

        return checked_func

    def __enter__(self) -> Self:
        """Checks all preconditions when the scope is entered

        Raises:
            TypeError: if the predicate is malformed given the set of captured and cloned values.
        """

        # resolve bindings
        candidate_bindings = []
        if self.__parent_frame is not None:
            candidate_bindings += [
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
            loc=(
                inspect.getframeinfo(self.__parent_frame)
                if self.__parent_frame is not None
                else None
            ),
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
