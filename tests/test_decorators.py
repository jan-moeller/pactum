import inspect

import pytest

from pycontractz import (
    ContractViolationException,
    pre,
    post,
    EvaluationSemantic,
    raising_contract_violation_handler,
    set_contract_evaluation_semantics,
    set_contract_violation_handler,
)
from pycontractz.decorators import __promote_positional_arguments_to_keyword_arguments

set_contract_evaluation_semantics(EvaluationSemantic.observe)
set_contract_violation_handler(raising_contract_violation_handler)


def __raise(exception):
    raise exception


def test_promote_positional_arguments_to_keyword_arguments():
    def foo(*args, **kwargs):
        nargs, nkwargs = __promote_positional_arguments_to_keyword_arguments(
            args, kwargs, inspect.signature(foo)
        )
        assert nargs == (1, 2, 3)
        assert len(nkwargs) == 0

    foo(1, 2, 3)

    def foo(*args, **kwargs):
        nargs, nkwargs = __promote_positional_arguments_to_keyword_arguments(
            args, kwargs, inspect.signature(foo)
        )
        assert nargs == ()
        assert nkwargs == {"x": 1, "y": 2}

    foo(x=1, y=2)

    def foo(*args, **kwargs):
        nargs, nkwargs = __promote_positional_arguments_to_keyword_arguments(
            args, kwargs, inspect.signature(foo)
        )
        assert nargs == (1, 2)
        assert nkwargs == {"x": 3, "y": 4}

    foo(1, 2, x=3, y=4)

    def foo(a, *args, b, **kwargs):
        nargs, nkwargs = __promote_positional_arguments_to_keyword_arguments(
            (a,) + args, {"b": b} | kwargs, inspect.signature(foo)
        )
        assert nargs == (2,)
        assert nkwargs == {"a": 1, "b": 3, "c": 4}

    foo(1, 2, b=3, c=4)

    def foo(a, /, b, *args, c, **kwargs):
        nargs, nkwargs = __promote_positional_arguments_to_keyword_arguments(
            (a,) + args, {"b": b, "c": c} | kwargs, inspect.signature(foo)
        )
        assert nargs == ()
        assert nkwargs == {"a": 1, "b": 2, "c": 3, "d": 4}

    foo(1, 2, c=3, d=4)


def test_pre_predicate_false():

    @pre(lambda: False)
    def test():
        pass

    with pytest.raises(ContractViolationException):
        test()


def test_pre_predicate_true():

    @pre(lambda: True)
    def test():
        return 42

    assert test() == 42


def test_pre_predicate_with_named_arguments():

    @pre(lambda x: x > 0)
    @pre(lambda y: y > 10)
    @pre(lambda y, x: x + y < 100)
    def test(x, y):
        return x + y

    assert test(1, 11) == 12
    assert test(50, 49) == 99

    with pytest.raises(ContractViolationException):
        test(0, 20)

    with pytest.raises(ContractViolationException):
        test(20, 0)

    with pytest.raises(ContractViolationException):
        test(200, 200)


def test_pre_predicate_with_args():

    @pre(lambda *args: len(args) > 0)
    def test(*args):
        return args[0]

    assert test(42) == 42
    assert test(42, 19) == 42

    with pytest.raises(ContractViolationException):
        test()

    with pytest.raises(ContractViolationException):

        @pre(lambda *args: True)
        def test(x, /):
            return x


def test_pre_predicate_with_kwargs():

    @pre(lambda **kwargs: "x" in kwargs)
    def test(x, **kwargs):
        return x

    assert test(x=42) == 42
    assert test(x=42, y="foobar") == 42

    with pytest.raises(ContractViolationException):
        test()

    with pytest.raises(ContractViolationException):
        test(y=9)


def test_pre_predicate_with_mixed_arguments():

    @pre(lambda x: x > 0)
    @pre(lambda y: y > 10)
    @pre(lambda y, x: x + y < 100)
    @pre(lambda *args, x, **kwargs: True)
    @pre(lambda *args: len(args) > 0)
    @pre(lambda **kwargs: len(kwargs) > 2)
    def test(x, /, y, *args, z=0, **kwargs):
        return x + y + z

    assert test(1, 11, 42, 43, foo=9) == 12
    assert test(50, 49, 42, 43, foo=9) == 99

    with pytest.raises(ContractViolationException):
        test(0, 20, 42, 43, foo=9)

    with pytest.raises(ContractViolationException):
        test(20, 0, 42, 43, foo=9)

    with pytest.raises(ContractViolationException):
        test(200, 200, 42, 43, foo=9)

    with pytest.raises(ContractViolationException):
        test(50, 49, 1)

    with pytest.raises(ContractViolationException):
        test(50, 49, foo=1)


def test_pre_exception():

    @pre(lambda: __raise(ValueError("Ahhhh")))
    def test():
        pass

    with pytest.raises(ContractViolationException):
        test()


def test_pre_predicate_invalid():

    with pytest.raises(ContractViolationException):

        @pre(lambda x: x == 0)
        def test():
            pass


def test_post_predicate_false():

    @post(lambda: False)
    def test():
        pass

    with pytest.raises(ContractViolationException):
        test()


def test_post_predicate_true():

    @post(lambda: True)
    def test():
        return 42

    assert test() == 42


def test_post_predicate_with_result_argument():

    @post(lambda result: result <= 50)
    def test(x, y):
        return x + y

    assert test(1, 11) == 12
    assert test(20, 30) == 50

    with pytest.raises(ContractViolationException):
        test(50, 49)


def test_post_exception():

    @post(lambda: __raise(ValueError("Ahhhh")))
    def test():
        pass

    with pytest.raises(ContractViolationException):
        test()


def test_post_predicate_invalid():

    with pytest.raises(ContractViolationException):

        @post(lambda x, y: True)
        def test():
            pass
