from dataclasses import dataclass

import pytest

from pactum import (
    ContractViolationException,
    invariant,
)


def __raise(exception):
    raise exception


def test_invariant_predicate_false():

    @invariant(lambda: False)
    class Test:
        pass

    with pytest.raises(ContractViolationException):
        Test()


def test_invariant_predicate_false_after_init():

    @invariant(lambda self: self.x < 0)
    class Test:
        def __init__(self):
            self.x = 42

    with pytest.raises(ContractViolationException):
        Test()


def test_invariant_predicate_false_before_or_after_method_call():

    @invariant(lambda self: self.x > 0)
    class Test:
        def __init__(self):
            self.x = 42

        def foo(self):
            pass

        def bar(self):
            self.x = -1

    t = Test()
    t.foo()

    t.x = -1  # Break the invariant
    with pytest.raises(ContractViolationException):
        t.foo()

    t.x = 42  # Fix the invariant
    with pytest.raises(ContractViolationException):
        t.bar()  # This breaks the invariant


def test_invariant_broken_after_exception():
    @invariant(lambda self: self.x > 0)
    class Test:
        def __init__(self):
            self.x = 42

        def foo(self, y):
            self.x -= 100
            self.x += 1000 / y  # Raises exception if y==0

    t = Test()
    t.foo(10)

    with pytest.raises(ContractViolationException):
        t.foo(0)


def test_invariant_on_dataclass():
    @invariant(lambda self: self.foo > 0)
    @dataclass
    class Foo:
        foo: int

    f = Foo(42)

    with pytest.raises(ContractViolationException):
        f = Foo(-1)


def test_invariant_as_context_manager():

    x = 42
    with invariant(lambda x: x == 42, capture={"x"}):
        x *= 2
        x -= 42
