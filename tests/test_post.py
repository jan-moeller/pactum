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


def test_post_predicate_false():

    @pre(lambda: True)
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


def test_post_predicate_with_capture():

    @post(lambda result, x, y: result == x + y, capture_before={"x", "y"})
    def test(x, y):
        return abs(x + y)

    assert test(1, 11) == 12
    assert test(20, 30) == 50

    @post(lambda x, y, result: result == x + y, capture_before={"x", "y"})
    def test(x, y):
        return abs(x + y)

    assert test(1, 11) == 12
    assert test(20, 30) == 50

    with pytest.raises(ContractViolationException):
        test(-2, 1)

    with pytest.raises(TypeError):

        @post(lambda result, z, y: True, capture_before={"z", "y"})
        def test(x, y):
            return abs(x + y)

    @post(lambda x: not x.append(0), capture_before={"x"})
    def test(x):
        return len(x) == 0

    assert test([])

    @post(
        lambda args, result, kwargs: result == len(args) + len(kwargs),
        capture_before={"args", "kwargs"},
    )
    def test(*args, **kwargs):
        return len(args) + len(kwargs)

    assert test(1, 2, 3) == 3


def test_post_exception():

    @post(lambda: __raise(ValueError("Ahhhh")))
    def test():
        pass

    with pytest.raises(ValueError):
        test()


def test_post_predicate_invalid():

    with pytest.raises(TypeError):

        @post(lambda x, y: True)
        def test():
            pass


def test_post_capture_before_local():

    x = 0

    @post(lambda x: x == 0, capture_before={"x"})
    def test():
        pass

    test()


def test_post_clone_before_local():

    x = [0]

    @post(lambda x: x.pop() == 0, clone_before={"x"})
    def test():
        pass

    test()

    assert x == [0]


def test_post_capture_before_global():

    @post(lambda THE_ANSWER: THE_ANSWER[0] == 42, capture_before={"THE_ANSWER"})
    def test():
        pass

    test()


def test_post_clone_before_global():

    @post(lambda THE_ANSWER: THE_ANSWER.pop() == 42, clone_before={"THE_ANSWER"})
    def test():
        pass

    test()

    assert THE_ANSWER == [42]


def test_post_capture_after_local():

    x = 42

    @post(lambda x: x == 0, capture_after={"x"})
    def test():
        nonlocal x
        x = 0

    test()


def test_post_clone_after_local():

    x = [42]

    @post(lambda x: x.pop() == 1, clone_after={"x"})
    def test():
        nonlocal x
        x[0] = 1

    test()

    assert x == [1]


def test_post_capture_after_global():

    @post(lambda THE_ANSWER: THE_ANSWER[0] == 42, capture_after={"THE_ANSWER"})
    def test():
        pass

    test()


def test_post_clone_after_global():

    @post(lambda THE_ANSWER: THE_ANSWER.pop() == 42, clone_after={"THE_ANSWER"})
    def test():
        pass

    test()

    assert THE_ANSWER == [42]
