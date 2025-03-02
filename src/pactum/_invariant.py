import inspect
from types import TracebackType
from typing import Self, Literal, Any

from pactum._pre import pre
from pactum._post import post, PostconditionScope
from pactum._predicate import Predicate
from pactum._capture_set import CaptureSet, normalize_capture_set
from pactum._contract_assertion_label import ContractAssertionLabel
from pactum._utils._parent_frame import get_parent_frame


class invariant:
    """Invariant assertion factory taking a predicate to evaluate before and after member method evaluation"""

    __methods_to_ignore = [
        # runs before the object is initialized and therefore can't maintain any invariants
        "__new__",
        "__init_subclass__",
        "__subclasshook__",
        # required for the implementation of invariant
        "__dir__",
        "__setattr__",
        "__getattribute__",
        "__delattr__",
    ]

    def __init__(
        self,
        predicate: Predicate,
        /,
        *,
        capture: CaptureSet | None = None,
        clone: CaptureSet | None = None,
        labels: list[ContractAssertionLabel] | None = None,
    ):
        """Initializes the invariant assertion factory

        Keyword arguments:
            predicate: A callable evaluating the predicate to check before function evaluation.
            capture: A set of names to capture. Variables by this name can be predicate parameters.
                     Note that the wrapped method's arguments are implicitly captured, including `self`.
            clone: A set of names to clone. Variables by this name can be predicate parameters.
            labels: A list of labels that determine this assertion's evaluation semantic
        """
        capture = normalize_capture_set(capture)
        clone = normalize_capture_set(clone)

        if labels is None:
            labels = []

        self.__pre = pre(
            predicate,
            capture=capture,
            clone=clone,
            labels=labels,
        )
        self.__post = post(
            predicate,
            capture_after=capture,
            clone_after=clone,
            labels=labels,
            scope=PostconditionScope.Always,
        )
        # Hacky! Patch up internal parent frame to point to the correct parent, instead of this __init__ method
        parent_frame = get_parent_frame(inspect.currentframe())
        setattr(self.__pre, "_pre__parent_frame", parent_frame)
        setattr(self.__post, "_post__parent_frame", parent_frame)

    def __call__[T](self, cls: type[T], /) -> type[T]:
        """Wraps the given class that checks invariants before and after evaluation of all member methods

        Keyword arguments:
            cls: Class to wrap.

        Returns:
            - `clazz` if the current contract evaluation semantic is `ignore`
            - a checked wrapper compatible with `clazz` otherwise

        Raises:
            TypeError: if the predicate is malformed given `clazz` and the set of captured and cloned values.
        """

        def is_member_function(attribute: Any) -> bool:
            return callable(attribute) and not (
                isinstance(attribute, staticmethod)
                or isinstance(attribute, classmethod)
                or inspect.isclass(attribute)
            )

        # Copy over any inherited functions
        for name in dir(cls):
            if name not in invariant.__methods_to_ignore and name not in cls.__dict__:
                attr = getattr(cls, name)
                if is_member_function(attr):
                    setattr(cls, name, attr)

        # Decorate them
        for attr_name, attr_value in cls.__dict__.items():
            if is_member_function(attr_value):
                if attr_name in invariant.__methods_to_ignore:
                    continue
                if attr_name != "__init__":  # Can't have invariant as precondition
                    setattr(cls, attr_name, self.__pre(getattr(cls, attr_name)))
                if attr_name != "__del__":  # Can't have invariant as postcondition
                    setattr(
                        cls,
                        attr_name,
                        self.__post(
                            getattr(cls, attr_name),
                            _implicit_return_capture=False,
                            _implicit_arg_capture=True,
                        ),
                    )

        return cls

    def __enter__(self) -> Self:
        """Checks all invariants when the scope is entered

        Raises:
            TypeError: if the predicate is malformed given the set of captured and cloned values.
        """

        self.__post.__enter__()
        self.__pre.__enter__()

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Checks all invariants when the scope is exited"""

        self.__pre.__exit__(exc_type, exc_val, exc_tb)
        self.__post.__exit__(exc_type, exc_val, exc_tb)
        return False
