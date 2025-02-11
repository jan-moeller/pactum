from warnings import deprecated

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

set_contract_evaluation_semantics(EvaluationSemantic.check)
set_contract_violation_handler(raising_contract_violation_handler)

THE_ANSWER = [42]


def __raise(exception):
    raise exception


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

    @pre(lambda args: len(args) > 0)
    def test(*args):
        return args[0]

    assert test(42) == 42
    assert test(42, 19) == 42

    with pytest.raises(ContractViolationException):
        test()

    @pre(lambda args: len(args) > 0)
    def test(*args):
        return args[0]

    assert test(42) == 42
    assert test(42, 19) == 42


def test_pre_predicate_with_kwargs():

    @pre(lambda kwargs: "y" in kwargs)
    def test(x, **kwargs):
        return x

    assert test(x=42, y=1) == 42
    assert test(x=42, y="foobar", z=3) == 42

    with pytest.raises(ContractViolationException):
        test(x=42)

    with pytest.raises(TypeError):
        test(y=9)


def test_pre_predicate_with_mixed_arguments():

    @pre(lambda x: x > 0)
    @pre(lambda y: y > 10)
    @pre(lambda y, x: x + y < 100)
    @pre(lambda args, x, kwargs: True)
    @pre(lambda args: len(args) > 0)
    @pre(lambda kwargs: len(kwargs) >= 1)
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

    with pytest.raises(ValueError):
        test()


def test_pre_predicate_invalid():

    with pytest.raises(TypeError):

        @pre(lambda x: x == 0)
        def test():
            pass


def test_pre_capture_local():

    x = 0

    @pre(lambda x: x == 0, capture={"x"})
    def test():
        pass

    test()


def test_pre_clone_local():

    x = [0]

    @pre(lambda x: x.pop() == 0, clone={"x"})
    def test():
        pass

    assert x == [0]

    test()


def test_pre_capture_global():

    @pre(lambda THE_ANSWER: THE_ANSWER[0] == 42, capture={"THE_ANSWER"})
    def test():
        pass

    test()


def test_pre_clone_global():

    @pre(lambda THE_ANSWER: THE_ANSWER.pop() == 42, clone={"THE_ANSWER"})
    def test():
        pass

    test()

    assert THE_ANSWER == [42]


def test_pre_post_capture_with_other_decorator():

    x = ["foo"]

    @deprecated("foobar")
    @pre(lambda x: len(x) == 1, capture={"x"})
    @post(lambda result, x, y: len(result) == len(x) + 1, capture_before={"x", "y"})
    def test(y: int):
        return x + [y]

    test(42)


def test_pre_as_context_manager():
    x = [42]
    with pre(lambda x: x.pop() == 42, clone={"x"}):
        pass
    assert x == [42]


def test_pre_post_as_context_manager():
    x = [42]
    with (
        pre(lambda x: x.pop() == 42, clone={"x"}),
        post(lambda x: len(x) == 0, capture_after={"x"}),
    ):
        x.pop()
    assert x == []
