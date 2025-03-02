import pytest

from pactum import (
    ContractViolationException,
    pre,
    post,
    labels,
    global_contract_assertion_label,
    PostconditionScope,
)

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

    @post(lambda result, z, y: True, capture_before={"z", "y"})
    def test(x, y):
        return abs(x + y)

    with pytest.raises(TypeError):
        test(1, 2)

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


def test_post_scope_exceptional_return():

    @post(
        lambda exc: type(exc) == ValueError, scope=PostconditionScope.ExceptionalReturn
    )
    def test(exc):
        raise exc

    with pytest.raises(ValueError):
        test(ValueError())

    with pytest.raises(ContractViolationException):
        test(TypeError())


def test_post_scope_always():

    @post(lambda r: type(r) in [ValueError, int], scope=PostconditionScope.Always)
    def test(val):
        if isinstance(val, Exception):
            raise val
        return val

    test(42)

    with pytest.raises(ValueError):
        test(ValueError())

    with pytest.raises(ContractViolationException):
        test(TypeError())

    with pytest.raises(ContractViolationException):
        test("something")


def test_post_predicate_invalid():

    @post(lambda x, y: True)
    def test():
        pass

    with pytest.raises(TypeError):
        test()


def test_post_capture_before_local():

    @post(lambda x: x == 0, capture_before={"x"})
    def test():
        pass

    x = 0

    test()


def test_post_clone_before_local():

    @post(lambda x: x.pop() == 0, clone_before={"x"})
    def test():
        pass

    x = [0]

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

    @post(lambda x: x == 0, capture_after={"x"})
    def test():
        nonlocal x
        x = 0

    x = 42

    test()

    assert x == 0


def test_post_clone_after_local():

    @post(lambda x: x.pop() == 1, clone_after={"x"})
    def test():
        nonlocal x
        x[0] = 1

    x = [42]

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


def test_post_capture_rename():

    @post(lambda y: y == 0, capture_before={"y": "x"})
    def test():
        pass

    x = 0

    test()


def test_post_capture_before_and_after():

    @post(lambda x, y: len(x) + 1 == len(y), clone_before={"x"}, clone_after={"y": "x"})
    def test(x):
        x.append(42)

    test([42])


def test_post_capture_wrong_type():

    with pytest.raises(TypeError):

        @post(lambda x: x == 0, capture_before=["x"])
        def test():
            pass


def test_post_as_context_manager():
    x = [42]
    with (
        post(lambda x: x.pop() == 42, clone_before={"x"}),
        post(lambda x: x.pop() == 3, clone_after={"x"}),
    ):
        x[0] = 3
    assert x == [3]


def test_post_as_context_manager_scope_regular_exit():
    x = [42]

    with pytest.raises(ValueError):
        with post(lambda x: x[0] == 0, capture_after={"x"}):
            raise ValueError()


def test_post_as_context_manager_scope_exceptional_exit():
    x = [42]

    with post(
        lambda x: x[0] == 0,
        capture_after={"x"},
        scope=PostconditionScope.ExceptionalReturn,
    ):
        pass


def test_post_with_label():

    @post(lambda: False, labels=[labels.ignore])
    def test():
        pass

    test()

    @post(lambda: False, labels=[labels.ignore_postconditions])
    def test():
        pass

    test()

    with labels.enable_expensive(False):

        @post(lambda: False, labels=[labels.expensive])
        def test():
            pass

        test()

    with pytest.raises(ContractViolationException), labels.enable_expensive(True):

        @post(lambda: False, labels=[labels.expensive])
        def test():
            pass

        test()

    with global_contract_assertion_label(labels.filter_by_module(r"foo")):

        @post(lambda: False)
        def test():
            pass

        test()

    with global_contract_assertion_label(labels.filter_by_module(r"post")):

        with pytest.raises(ContractViolationException):

            @post(lambda: False)
            def test():
                pass

            test()
